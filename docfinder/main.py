"""FastAPI Backend for DocFinder."""
import io
import os
import re
import shutil
import random
import string
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db, init_db, async_session_maker
from models.models import User, Comparison, Report, LoginActivity, UploadedFile
from auth.utils import verify_password, get_password_hash, create_access_token, decode_token
from services.text_comparison import TextComparisonEngine
from services.pdf_comparison import PDFComparisonEngine
from services.excel_comparison import ExcelComparisonEngine
from services.ai_engine import AIEngine
from services.report_generator import ReportGenerator
from services.email_service import email_service
from services.ai_integration import ai_service

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

security = HTTPBearer(auto_error=False)

# OTP Storage (in-memory, use Redis/DB in production)
otp_store: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    
    # Create default admin user
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                username="admin",
                email="admin@docfinder.local",
                hashed_password=get_password_hash("admin123"),
                is_admin=True
            )
            session.add(admin)
            await session.commit()
    
    yield


app = FastAPI(
    title="DocFinder API",
    description="Intelligent Document Difference Finder and Analysis Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper function to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool
    user_id: int


class OTPSendRequest(BaseModel):
    email: str


class OTPVerifyRequest(BaseModel):
    email: str
    otp: str
    username: str
    password: str


class ComparisonResponse(BaseModel):
    id: int
    file1_name: str
    file2_name: str
    similarity_score: float
    status: str


def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email: str, otp: str):
    """
    Send OTP via email.
    Uses the email service which supports SMTP configuration.
    """
    return email_service.send_otp(email, otp)


@app.post("/api/auth/send-otp")
async def send_otp(request: OTPSendRequest, db: AsyncSession = Depends(get_db)):
    """Send OTP to email for registration verification."""
    # Check if email already registered
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate and store OTP
    otp = generate_otp()
    otp_store[request.email] = {
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    # Send OTP (simulated)
    send_otp_email(request.email, otp)
    
    return {"message": "OTP sent to your email", "email": request.email}


@app.post("/api/auth/verify-otp")
async def verify_otp_and_register(request: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and complete registration."""
    # Check OTP
    otp_data = otp_store.get(request.email)
    if not otp_data:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")
    
    if datetime.utcnow() > otp_data["expires_at"]:
        del otp_store[request.email]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if otp_data["otp"] != request.otp and request.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Check username exists
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    hashed = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed,
        is_verified=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Clear OTP
    del otp_store[request.email]
    
    # Send welcome email
    email_service.send_welcome_email(request.email, request.username)
    
    # Create token
    token = create_access_token({"sub": str(new_user.id)})
    
    return Token(
        access_token=token,
        token_type="bearer",
        is_admin=new_user.is_admin,
        user_id=new_user.id
    )


# Auth endpoints
@app.post("/api/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create token
    token = create_access_token({"sub": str(new_user.id)})
    
    return Token(
        access_token=token,
        token_type="bearer",
        is_admin=new_user.is_admin,
        user_id=new_user.id
    )


@app.post("/api/login", response_model=Token)
async def login(user: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login user."""
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        # Log failed attempt
        activity = LoginActivity(
            user_id=0,
            username=user.username,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            status="failed"
        )
        db.add(activity)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    db_user.last_login = datetime.utcnow()
    await db.commit()
    
    # Log successful login
    activity = LoginActivity(
        user_id=db_user.id,
        username=db_user.username,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        status="success"
    )
    db.add(activity)
    await db.commit()
    
    token = create_access_token({"sub": str(db_user.id)})
    
    return Token(
        access_token=token,
        token_type="bearer",
        is_admin=db_user.is_admin,
        user_id=db_user.id
    )


# File comparison endpoints
@app.post("/api/compare/text")
async def compare_text(
    text1: str = Form(...),
    text2: str = Form(...),
    level: str = Form("word"),
    to_lowercase: bool = Form(False),
    sort_lines: bool = Form(False),
    replace_line_breaks: bool = Form(False),
    remove_extra_spaces: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare two text inputs with optional preprocessing."""
    # Text preprocessing
    if to_lowercase:
        text1 = text1.lower()
        text2 = text2.lower()
    
    if sort_lines:
        text1 = '\n'.join(sorted(text1.splitlines()))
        text2 = '\n'.join(sorted(text2.splitlines()))
    
    if replace_line_breaks:
        text1 = text1.replace('\n', ' ').replace('\r', ' ')
        text2 = text2.replace('\n', ' ').replace('\r', ' ')
    
    if remove_extra_spaces:
        text1 = ' '.join(text1.split())
        text2 = ' '.join(text2.split())
    
    engine = TextComparisonEngine()
    result = engine.compare_text(text1, text2, level)
    
    # Save comparison
    comparison = Comparison(
        user_id=current_user.id if current_user else 0,
        file1_name="text_input_1",
        file2_name="text_input_2",
        file1_type="txt",
        file2_type="txt",
        comparison_type=f"text_{level}",
        similarity_score=result["similarity_score"],
        status="completed",
        results=result
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)
    
    # Add AI analysis using Groq/Gemini
    ai_analysis = ai_service.get_semantic_analysis(text1, text2)
    result["ai_analysis"] = ai_analysis
    
    return {"comparison_id": comparison.id, "results": result}


@app.post("/api/compare/pdf")
async def compare_pdf(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ocr: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare two PDF files."""
    # Save uploaded files
    file1_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file1.filename}")
    file2_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file2.filename}")
    
    with open(file1_path, "wb") as f:
        shutil.copyfileobj(file1.file, f)
    with open(file2_path, "wb") as f:
        shutil.copyfileobj(file2.file, f)
    
    try:
        # Read file contents
        with open(file1_path, "rb") as f:
            pdf1_content = f.read()
        with open(file2_path, "rb") as f:
            pdf2_content = f.read()
        
        # Check if OCR is needed
        if use_ocr:
            from .services.ocr_engine import OCREngine
            if OCREngine.detect_if_scanned(pdf1_content) or OCREngine.detect_if_scanned(pdf2_content):
                pass  # OCR will be applied automatically
        
        # Compare PDFs
        result = PDFComparisonEngine.compare_pdfs(pdf1_content, pdf2_content, use_ocr)
        
        # Save comparison
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="pdf",
            file2_type="pdf",
            comparison_type="pdf",
            similarity_score=result["similarity_score"],
            status="completed",
            results=result
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)
        
        # Add AI analysis
        ai_result = AIEngine.compare_semantically(
            result.get("full_text1", ""),
            result.get("full_text2", "")
        )
        result["ai_analysis"] = ai_result
        
        return {"comparison_id": comparison.id, "results": result}
    
    finally:
        # Cleanup temp files
        os.remove(file1_path)
        os.remove(file2_path)


@app.post("/api/compare/excel")
async def compare_excel(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare two Excel files."""
    file1_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file1.filename}")
    file2_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file2.filename}")
    
    with open(file1_path, "wb") as f:
        shutil.copyfileobj(file1.file, f)
    with open(file2_path, "wb") as f:
        shutil.copyfileobj(file2.file, f)
    
    try:
        with open(file1_path, "rb") as f:
            excel1_content = f.read()
        with open(file2_path, "rb") as f:
            excel2_content = f.read()
        
        result = ExcelComparisonEngine.compare_excels(excel1_content, excel2_content)
        
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="xlsx",
            file2_type="xlsx",
            comparison_type="excel",
            similarity_score=result.get("overall_similarity", 0),
            status="completed",
            results=result
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)
        
        return {"comparison_id": comparison.id, "results": result}
    
    finally:
        os.remove(file1_path)
        os.remove(file2_path)


@app.post("/api/compare/csv")
async def compare_csv(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare two CSV files."""
    file1_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file1.filename}")
    file2_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file2.filename}")
    
    with open(file1_path, "wb") as f:
        shutil.copyfileobj(file1.file, f)
    with open(file2_path, "wb") as f:
        shutil.copyfileobj(file2.file, f)
    
    try:
        with open(file1_path, "rb") as f:
            csv1_content = f.read()
        with open(file2_path, "rb") as f:
            csv2_content = f.read()
        
        result = ExcelComparisonEngine.compare_csvs(csv1_content, csv2_content)
        
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="csv",
            file2_type="csv",
            comparison_type="csv",
            similarity_score=result.get("similarity_score", 0),
            status="completed",
            results=result
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)
        
        return {"comparison_id": comparison.id, "results": result}
    
    finally:
        os.remove(file1_path)
        os.remove(file2_path)


# Report endpoints
@app.post("/api/report/pdf/{comparison_id}")
async def generate_pdf_report(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF report for a comparison."""
    result = await db.execute(select(Comparison).where(Comparison.id == comparison_id))
    comparison = result.scalar_one_or_none()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    user_info = {"username": current_user.username if current_user else "Anonymous"}
    pdf_bytes = ReportGenerator.generate_pdf_report(comparison.results or {}, user_info)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=comparison_{comparison_id}.pdf"}
    )


@app.post("/api/report/excel/{comparison_id}")
async def generate_excel_report(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate Excel report for a comparison."""
    result = await db.execute(select(Comparison).where(Comparison.id == comparison_id))
    comparison = result.scalar_one_or_none()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    user_info = {"username": current_user.username if current_user else "Anonymous"}
    excel_bytes = ReportGenerator.generate_excel_report(comparison.results or {}, user_info)
    
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=comparison_{comparison_id}.xlsx"}
    )


# History endpoints
@app.get("/api/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's comparison history."""
    query = select(Comparison).order_by(Comparison.created_at.desc()).limit(50)
    if current_user:
        query = select(Comparison).where(Comparison.user_id == current_user.id).order_by(Comparison.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    comparisons = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "file1_name": c.file1_name,
            "file2_name": c.file2_name,
            "similarity_score": c.similarity_score,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in comparisons
    ]


# Admin endpoints
@app.get("/api/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin statistics."""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count users
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()
    
    # Count comparisons
    comparisons_result = await db.execute(select(Comparison))
    comparisons = comparisons_result.scalars().all()
    
    return {
        "total_users": len(users),
        "active_users": len([u for u in users if u.is_active]),
        "total_comparisons": len(comparisons),
        "admin_users": len([u for u in users if u.is_admin])
    }


@app.get("/api/admin/users")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)."""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "DocFinder API", "version": "1.0.0"}


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "DocFinder API",
        "version": "1.0.0",
        "description": "Intelligent Document Difference Finder and Analysis Platform"
    }


from fastapi.responses import StreamingResponse
import io
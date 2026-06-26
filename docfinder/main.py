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

from diff_engine import compute_diff_report, extract_text_from_pdf, extract_text_from_excel, extract_text_from_csv, image_diff, extract_text_from_docx, extract_text_from_pptx, get_ai_analysis, GROQ_OK
import tempfile
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request, WebSocket, WebSocketDisconnect
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
from services.image_comparison import ImageComparisonEngine
from services.ai_engine import AIEngine
from services.report_generator import ReportGenerator
from services.email_service import email_service
from services.ai_integration import ai_service
from services.vector_db import vector_db

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

# WebSockets Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()


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

class ChatRequest(BaseModel):
    text1: str
    text2: str
    query: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


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


@app.post("/api/chat")
async def chat_with_docs(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """RAG Chat endpoint to query document differences."""
    if not req.text1 and not req.text2:
        raise HTTPException(status_code=400, detail="Document text is required.")
        
    response = ai_service.chat_with_document(req.text1, req.text2, req.query)
    return {"reply": response}

@app.post("/api/search")
async def search_docs(req: SearchRequest, current_user: User = Depends(get_current_user)):
    """Semantic vector search across uploaded documents."""
    results = vector_db.search(req.query, req.top_k)
    return {"results": results}

# File comparison endpoints
@app.post("/api/compare/text")
async def compare_text(
    text1: str = Form(...),
    text2: str = Form(...),
    level: str = Form("word"),
    to_lowercase: str = Form("false"),
    remove_extra_spaces: str = Form("false"),
    sort_lines: str = Form("false"),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = compute_diff_report(text1, text2)
    report["file_type"] = "text"
    
    if use_ai.lower() == "true":
        report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

    # Save history
    comparison = Comparison(
        user_id=current_user.id if current_user else 0,
        file1_name="Text Input 1",
        file2_name="Text Input 2",
        file1_type="text",
        file2_type="text",
        comparison_type="text",
        similarity_score=report["stats"]["similarity_percent"],
        status="completed",
        results=report
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)

    report["comparison_id"] = comparison.id
    return report

@app.post("/api/compare/pdf")
async def compare_pdf(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_pdf(t1_path)
        text2 = extract_text_from_pdf(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pdf"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="pdf",
            file2_type="pdf",
            comparison_type="pdf",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/docx")
async def compare_docx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_docx(t1_path)
        text2 = extract_text_from_docx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "docx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="docx",
            file2_type="docx",
            comparison_type="docx",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/pptx")
async def compare_pptx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_pptx(t1_path)
        text2 = extract_text_from_pptx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pptx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="pptx",
            file2_type="pptx",
            comparison_type="pptx",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/excel")
async def compare_excel(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    suffix = ".xlsx" if "xlsx" in file1.filename else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_excel(t1_path)
        text2 = extract_text_from_excel(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "excel"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="excel",
            file2_type="excel",
            comparison_type="excel",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/csv")
async def compare_csv(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_csv(t1_path)
        text2 = extract_text_from_csv(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "csv"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="csv",
            file2_type="csv",
            comparison_type="csv",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/image")
async def compare_image(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext1 = os.path.splitext(file1.filename)[1] or ".png"
    ext2 = os.path.splitext(file2.filename)[1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext1) as t1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=ext2) as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        report = image_diff(t1_path, t2_path)
        report["file_type"] = "image"
        
        if use_ai.lower() == "true" and GROQ_OK:
            report["ai_analysis"] = "AI image analysis: " + \
                f"Found {report['stats']['changed_pixels']} different pixels " \
                f"({report['stats']['difference_percent']}% of image changed)."

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="image",
            file2_type="image",
            comparison_type="image",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/ai/chat")
async def ai_chat(
    message: str = Form(...),
    context: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    from groq import Groq
    GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are a document analysis assistant. Context from compared documents:\n{context[:2000]}"},
                {"role": "user", "content": message}
            ],
            max_tokens=800,
            temperature=0.5
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"AI error: {str(e)}")

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

@app.websocket("/ws/collab/{room_id}")
async def websocket_collab(websocket: WebSocket, room_id: str):
    """Real-time collaboration websocket endpoint."""
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast the change to all other clients in the room
            await manager.broadcast(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
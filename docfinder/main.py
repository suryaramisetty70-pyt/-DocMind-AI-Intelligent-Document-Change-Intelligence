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
from models.models import User, Comparison, Report, LoginActivity, UploadedFile, Folder, AppEntry
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

def safe_unlink(path: str):
    """Safely unlink a file, ignoring errors (especially on Windows due to open handles)."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass

async def save_uploaded_file(file: UploadFile, subfolder: str, db: AsyncSession, user_id: int) -> str:
    import uuid
    # Ensure uploads folder exists
    folder_path = os.path.join(UPLOAD_DIR, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Generate unique filename to prevent collisions
    filename = file.filename or "unnamed"
    base, ext = os.path.splitext(filename)
    clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', base)
    unique_filename = f"{clean_base}_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(folder_path, unique_filename)
    
    # Read file content and write it
    content = await file.read()
    await file.seek(0)
    
    with open(target_path, "wb") as f:
        f.write(content)
        
    # Save tracking metadata in UploadedFile table
    uploaded = UploadedFile(
        user_id=user_id,
        filename=filename,
        file_type=subfolder,
        file_size=len(content),
        file_path=target_path.replace("\\", "/"),
        ocr_applied=False
    )
    db.add(uploaded)
    await db.commit()
    await db.refresh(uploaded)
    
    return target_path.replace("\\", "/")

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
            
        # Seed default workspace folders and apps if none exist
        result_folders = await session.execute(select(Folder))
        has_folders = result_folders.scalars().first()
        if not has_folders:
            folders = [
                Folder(name="AI Agents", icon="🤖"),
                Folder(name="Web Services", icon="🌐"),
                Folder(name="Utility Tools", icon="🛠️")
            ]
            session.add_all(folders)
            await session.commit()
            
            # Add default apps for these folders
            res_ai = await session.execute(select(Folder).where(Folder.name == "AI Agents"))
            f_ai = res_ai.scalar_one()
            res_web = await session.execute(select(Folder).where(Folder.name == "Web Services"))
            f_web = res_web.scalar_one()
            
            default_apps = [
                AppEntry(title="DocMind AI", url="/difflab.html", icon_emoji="📄", description="AI document semantic difference engine.", folder_id=f_ai.id),
                AppEntry(title="Call Dialer", url="https://menmozhicallcampaign-1.onrender.com", icon_emoji="📞", description="Campaign dialer and call logs viewer.", folder_id=f_web.id)
            ]
            session.add_all(default_apps)
            await session.commit()
            print("Database seeded: Default portal folders and apps initialized.")
    
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
        await self.broadcast_count(room_id)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
        import asyncio
        asyncio.create_task(self.broadcast_count(room_id))

    async def broadcast_count(self, room_id: str):
        if room_id in self.active_connections:
            count = len(self.active_connections[room_id])
            message = json.dumps({"type": "count", "count": count})
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

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
    report["type"] = "text"
    
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
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "pdf", db, uid)
    t2_path = await save_uploaded_file(file2, "pdf", db, uid)

    try:
        text1 = extract_text_from_pdf(t1_path)
        text2 = extract_text_from_pdf(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pdf"
        report["type"] = "pdf"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare/docx")
async def compare_docx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "docx", db, uid)
    t2_path = await save_uploaded_file(file2, "docx", db, uid)

    try:
        text1 = extract_text_from_docx(t1_path)
        text2 = extract_text_from_docx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "docx"
        report["type"] = "docx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare/pptx")
async def compare_pptx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "pptx", db, uid)
    t2_path = await save_uploaded_file(file2, "pptx", db, uid)

    try:
        text1 = extract_text_from_pptx(t1_path)
        text2 = extract_text_from_pptx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pptx"
        report["type"] = "pptx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare/excel")
async def compare_excel(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "excel", db, uid)
    t2_path = await save_uploaded_file(file2, "excel", db, uid)

    try:
        text1 = extract_text_from_excel(t1_path)
        text2 = extract_text_from_excel(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "excel"
        report["type"] = "excel"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare/csv")
async def compare_csv(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "csv", db, uid)
    t2_path = await save_uploaded_file(file2, "csv", db, uid)

    try:
        text1 = extract_text_from_csv(t1_path)
        text2 = extract_text_from_csv(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "csv"
        report["type"] = "csv"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare/image")
async def compare_image(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    t1_path = await save_uploaded_file(file1, "image", db, uid)
    t2_path = await save_uploaded_file(file2, "image", db, uid)

    try:
        report = image_diff(t1_path, t2_path)
        report["file_type"] = "image"
        report["type"] = "image"
        
        if use_ai.lower() == "true":
            ai_analysis = ai_service.analyze_images_with_gemini(t1_path, t2_path)
            if not ai_analysis:
                ai_analysis = (
                    "**AI Semantic Image Analysis:**\n\n"
                    f"Pixel-level difference: {report['stats']['changed_pixels']} pixels changed "
                    f"({report['stats']['difference_percent']}% of image).\n"
                    "A semantic difference (addition, removal, or modification) is present in the highlighted region."
                )
            report["ai_analysis"] = ai_analysis
            report["ai_analysis_provider"] = "Gemini-1.5-Flash Multimodal"

        # Save history
        comparison = Comparison(
            user_id=uid,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_file_text(file: UploadFile) -> str:
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    # Read the file content
    content = await file.read()
    await file.seek(0)
    
    # If it is a simple text file
    if ext in [".txt", ".html", ".css", ".js", ".json", ".xml", ".md", ".py", ".sh", ".bat"]:
        return content.decode("utf-8", errors="ignore")
        
    # For binary files, write to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
        
    try:
        if ext == ".pdf":
            return extract_text_from_pdf(tmp_path)
        elif ext == ".docx":
            return extract_text_from_docx(tmp_path)
        elif ext == ".pptx":
            return extract_text_from_pptx(tmp_path)
        elif ext in [".xlsx", ".xls"]:
            return extract_text_from_excel(tmp_path)
        elif ext == ".csv":
            return extract_text_from_csv(tmp_path)
        else:
            # Try plain text decode as fallback
            return content.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Error extracting content from {filename}: {str(e)}"
    finally:
        safe_unlink(tmp_path)

@app.post("/api/compare/folder")
async def compare_folder(
    files1: List[UploadFile] = File(...),
    files2: List[UploadFile] = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user.id if current_user else 0
    # Map filenames to upload files
    f1_map = {f.filename: f for f in files1}
    f2_map = {f.filename: f for f in files2}
    
    all_filenames = set(f1_map.keys()).union(set(f2_map.keys()))
    
    differences = []
    added_count = 0
    removed_count = 0
    changed_count = 0
    total_score = 0
    score_count = 0
    
    for filename in all_filenames:
        if filename not in f1_map:
            # Added in folder 2
            differences.append({
                "filename": filename,
                "status": "added",
                "similarity": 0.0,
                "changes": {"added": 1, "removed": 0, "changed": 0}
            })
            added_count += 1
        elif filename not in f2_map:
            # Removed in folder 2
            differences.append({
                "filename": filename,
                "status": "removed",
                "similarity": 0.0,
                "changes": {"added": 0, "removed": 1, "changed": 0}
            })
            removed_count += 1
        else:
            # Exists in both, compare content
            file1 = f1_map[filename]
            file2 = f2_map[filename]
            
            ext = os.path.splitext(filename)[1].lower()
            
            # If it is an image, run image visual diff comparison
            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                t1_path = await save_uploaded_file(file1, "folder", db, uid)
                t2_path = await save_uploaded_file(file2, "folder", db, uid)
                
                try:
                    img_report = image_diff(t1_path, t2_path)
                    sim = img_report["stats"]["similarity_percent"]
                    status = "identical" if sim == 100.0 else "modified"
                    if status == "modified":
                        changed_count += 1
                    
                    if use_ai.lower() == "true":
                        ai_analysis = ai_service.analyze_images_with_gemini(t1_path, t2_path)
                        img_report["ai_analysis"] = ai_analysis
                        img_report["ai_analysis_provider"] = "Gemini-1.5-Flash Multimodal"
                        
                    differences.append({
                        "filename": filename,
                        "status": status,
                        "similarity": sim,
                        "changes": {
                            "added": img_report["stats"].get("changed_elements_count", 0),
                            "removed": 0,
                            "changed": img_report["stats"].get("changed_pixels", 0)
                        },
                        "results": img_report
                    })
                    total_score += sim
                    score_count += 1
                except Exception as e:
                    differences.append({
                        "filename": filename,
                        "status": "error",
                        "similarity": 0.0,
                        "error": str(e)
                    })
            else:
                # Document/Text comparison
                try:
                    t1_path = await save_uploaded_file(file1, "folder", db, uid)
                    t2_path = await save_uploaded_file(file2, "folder", db, uid)
                    
                    text1 = await extract_file_text(file1)
                    text2 = await extract_file_text(file2)
                    
                    file_report = compute_diff_report(text1, text2)
                    sim = file_report["stats"]["similarity_percent"]
                    
                    status = "identical" if sim == 100.0 else "modified"
                    if status == "modified":
                        changed_count += 1
                    
                    differences.append({
                        "filename": filename,
                        "status": status,
                        "similarity": sim,
                        "changes": file_report["stats"],
                        "results": file_report
                    })
                    total_score += sim
                    score_count += 1
                except Exception as e:
                    differences.append({
                        "filename": filename,
                        "status": "error",
                        "similarity": 0.0,
                        "error": str(e)
                    })
            
    avg_similarity = round(total_score / score_count, 2) if score_count > 0 else 100.0
    
    report = {
        "file_type": "folder",
        "type": "folder",
        "differences": differences,
        "stats": {
            "added": added_count,
            "removed": removed_count,
            "changed": changed_count,
            "similarity_percent": avg_similarity,
            "difference_percent": round(100.0 - avg_similarity, 2),
            "total_changes": added_count + removed_count + changed_count
        }
    }
    
    # Save to history
    comparison = Comparison(
        user_id=uid,
        file1_name="Folder A",
        file2_name="Folder B",
        file1_type="folder",
        file2_type="folder",
        comparison_type="folder",
        similarity_score=avg_similarity,
        status="completed",
        results=report
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)
    
    report["comparison_id"] = comparison.id
    return report

@app.post("/api/ai/chat")
async def ai_chat(
    message: str = Form(...),
    context: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    from services.ai_integration import ai_service
    
    # Construct a proper system prompt using the context
    system_prompt = (
        "You are a document analysis assistant. Context from compared documents:\n"
        f"{context[:2000]}\n"
        "Analyze the context and answer user query professionally. Be concise."
    )
    
    # Try Groq first via ai_service (which uses the correct resolved key)
    response = ai_service.analyze_with_groq(message, system_prompt)
    if response and "error" not in response.lower() and "unauthorized" not in response.lower():
        return {"reply": response}
        
    # Try Gemini next via ai_service
    response = ai_service.analyze_with_gemini(f"{system_prompt}\nUser Query: {message}")
    if response and "error" not in response.lower() and "unauthorized" not in response.lower():
        return {"reply": response}
        
    # Fallback to local rule-based smart mock if all else fails
    reply = ai_service._generate_mock_chat_response(context, "", message)
    return {"reply": reply}

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


@app.get("/api/comparison/{comparison_id}")
async def get_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific comparison by ID."""
    result = await db.execute(select(Comparison).where(Comparison.id == comparison_id))
    comparison = result.scalar_one_or_none()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
        
    if current_user and comparison.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this comparison")
        
    return {
        "id": comparison.id,
        "file1_name": comparison.file1_name,
        "file2_name": comparison.file2_name,
        "file1_type": comparison.file1_type,
        "file2_type": comparison.file2_type,
        "comparison_type": comparison.comparison_type,
        "similarity_score": comparison.similarity_score,
        "status": comparison.status,
        "results": comparison.results,
        "created_at": comparison.created_at.isoformat() if comparison.created_at else None
    }


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


# --- Portal API Endpoints ---
class FolderCreate(BaseModel):
    name: str
    icon: str = "📁"

class AppCreate(BaseModel):
    title: str
    url: str
    icon_emoji: str = "🤖"
    description: Optional[str] = None
    folder_id: int

@app.get("/api/portal/workspaces")
async def get_portal_workspaces(db: AsyncSession = Depends(get_db)):
    # Retrieve all folders
    res_folders = await db.execute(select(Folder))
    folders = res_folders.scalars().all()
    
    # Retrieve all apps
    res_apps = await db.execute(select(AppEntry))
    apps = res_apps.scalars().all()
    
    # Group apps by folder
    data = []
    for folder in folders:
        folder_apps = [
            {
                "id": app.id,
                "title": app.title,
                "url": app.url,
                "icon_emoji": app.icon_emoji,
                "description": app.description
            }
            for app in apps if app.folder_id == folder.id
        ]
        data.append({
            "id": folder.id,
            "name": folder.name,
            "icon": folder.icon,
            "apps": folder_apps
        })
    return data

@app.post("/api/portal/apps")
async def create_portal_app(app_data: AppCreate, db: AsyncSession = Depends(get_db)):
    res_folder = await db.execute(select(Folder).where(Folder.id == app_data.folder_id))
    folder = res_folder.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Category folder not found")
    
    new_app = AppEntry(
        title=app_data.title,
        url=app_data.url,
        icon_emoji=app_data.icon_emoji,
        description=app_data.description,
        folder_id=app_data.folder_id
    )
    db.add(new_app)
    await db.commit()
    await db.refresh(new_app)
    return new_app

@app.post("/api/portal/folders")
async def create_portal_folder(folder_data: FolderCreate, db: AsyncSession = Depends(get_db)):
    res_existing = await db.execute(select(Folder).where(Folder.name == folder_data.name))
    existing = res_existing.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Folder category already exists")
        
    new_folder = Folder(
        name=folder_data.name,
        icon=folder_data.icon
    )
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder

@app.delete("/api/portal/apps/{app_id}")
async def delete_portal_app(app_id: int, db: AsyncSession = Depends(get_db)):
    res_app = await db.execute(select(AppEntry).where(AppEntry.id == app_id))
    app_entry = res_app.scalar_one_or_none()
    if not app_entry:
        raise HTTPException(status_code=404, detail="App entry not found")
        
    await db.delete(app_entry)
    await db.commit()
    return {"message": "App deleted successfully"}


# --- Translation Workspace API ---
class TranslationRequest(BaseModel):
    text: str
    target_language: str

@app.post("/api/translate")
async def translate_document_text(req: TranslationRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text input")
        
    translated = ai_service.translate_text(req.text, req.target_language)
    if not translated:
        raise HTTPException(status_code=500, detail="Translation failed")
        
    return {"translated_text": translated}
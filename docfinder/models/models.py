"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
from database.config import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verified via OTP
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Comparison(Base):
    """Comparison model."""
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    file1_name = Column(String(255))
    file2_name = Column(String(255))
    file1_type = Column(String(20))  # txt, pdf, excel, csv
    file2_type = Column(String(20))
    comparison_type = Column(String(50))  # text, semantic, structural
    similarity_score = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending, completed, failed
    results = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Report(Base):
    """Report model."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    comparison_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    report_type = Column(String(20))  # pdf, excel
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginActivity(Base):
    """Login activity tracking."""
    __tablename__ = "login_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String(50))
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    status = Column(String(20))  # success, failed
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedFile(Base):
    """Uploaded files tracking."""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    filename = Column(String(255))
    file_type = Column(String(20))
    file_size = Column(Integer)
    file_path = Column(String(500), nullable=True)
    ocr_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
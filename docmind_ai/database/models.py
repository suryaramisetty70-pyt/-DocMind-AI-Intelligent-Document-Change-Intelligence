"""
DocMind AI - Database Models
SQLAlchemy models for data persistence
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    organization = Column(String(255))
    hashed_password = Column(String(255))
    api_key = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    comparisons = relationship("Comparison", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"


class Document(Base):
    """Document model"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))  # pdf, docx, xlsx, txt, etc.
    file_size = Column(BigInteger)
    page_count = Column(Integer)
    hash = Column(String(64))  # SHA-256 hash
    extracted_text = Column(Text)
    extracted_tables = Column(JSON, default=[])
    signatures_detected = Column(JSON, default=[])
    stamps_detected = Column(JSON, default=[])
    ocr_confidence = Column(Float)
    ocr_processed = Column(Boolean, default=False)
    metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document")
    comparisons_as_original = relationship("Comparison", foreign_keys="Comparison.original_document_id", back_populates="original_document")
    comparisons_as_modified = relationship("Comparison", foreign_keys="Comparison.modified_document_id", back_populates="modified_document")
    
    def __repr__(self):
        return f"<Document {self.name}>"


class DocumentVersion(Base):
    """Document version model"""
    __tablename__ = "document_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"))
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500))
    extracted_text = Column(Text)
    extracted_tables = Column(JSON, default=[])
    signatures_detected = Column(JSON, default=[])
    stamps_detected = Column(JSON, default=[])
    ocr_confidence = Column(Float)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    
    def __repr__(self):
        return f"<DocumentVersion {self.document_id} v{self.version_number}>"


class Comparison(Base):
    """Comparison model"""
    __tablename__ = "comparisons"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    original_document_id = Column(String(36), ForeignKey("documents.id"))
    modified_document_id = Column(String(36), ForeignKey("documents.id"))
    
    # Similarity scores
    overall_similarity = Column(Float, default=0.0)
    semantic_similarity = Column(Float, default=0.0)
    structural_similarity = Column(Float, default=0.0)
    lexical_similarity = Column(Float, default=0.0)
    
    # Statistics
    total_changes = Column(Integer, default=0)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    modifications = Column(Integer, default=0)
    movements = Column(Integer, default=0)
    
    # Risk and fraud scores
    risk_score = Column(Float, default=0.0)
    fraud_score = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)
    
    # Results
    changes_summary = Column(JSON, default={})
    risk_analysis = Column(JSON, default={})
    fraud_detection = Column(JSON, default={})
    executive_summary = Column(JSON, default={})
    
    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # Metadata
    language = Column(String(10), default="en")
    processing_time = Column(Float, default=0.0)
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="comparisons")
    original_document = relationship("Document", foreign_keys=[original_document_id], back_populates="comparisons_as_original")
    modified_document = relationship("Document", foreign_keys=[modified_document_id], back_populates="comparisons_as_modified")
    changes = relationship("Change", back_populates="comparison", cascade="all, delete-orphan")
    risk_records = relationship("RiskRecord", back_populates="comparison", cascade="all, delete-orphan")
    fraud_records = relationship("FraudRecord", back_populates="comparison", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Comparison {self.id}>"


class Change(Base):
    """Change model - individual change records"""
    __tablename__ = "changes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_id = Column(String(36), ForeignKey("comparisons.id"))
    
    # Change details
    change_type = Column(String(50))  # character, word, sentence, paragraph, etc.
    category = Column(String(100))  # content, structure, formatting, data, compliance
    severity = Column(String(20))  # critical, significant, moderate, minor
    
    # Location
    location = Column(JSON)  # {page, line_start, line_end, section, etc.}
    
    # Content
    original_content = Column(Text)
    modified_content = Column(Text)
    
    # Analysis
    similarity_score = Column(Float, default=0.0)
    semantic_significance = Column(Float, default=0.0)
    business_impact = Column(String(50))
    
    # Additional metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comparison = relationship("Comparison", back_populates="changes")
    
    def __repr__(self):
        return f"<Change {self.change_type} {self.severity}>"


class RiskRecord(Base):
    """Risk analysis record"""
    __tablename__ = "risk_records"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_id = Column(String(36), ForeignKey("comparisons.id"))
    
    # Risk scores
    overall_risk_score = Column(Float, default=0.0)
    financial_risk = Column(Float, default=0.0)
    legal_risk = Column(Float, default=0.0)
    compliance_risk = Column(Float, default=0.0)
    operational_risk = Column(Float, default=0.0)
    
    # Risk level
    risk_level = Column(String(20))  # critical, high, medium, low, minimal
    
    # Details
    risk_factors = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    compliance_checks = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comparison = relationship("Comparison", back_populates="risk_records")
    
    def __repr__(self):
        return f"<RiskRecord {self.risk_level}>"


class FraudRecord(Base):
    """Fraud detection record"""
    __tablename__ = "fraud_records"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_id = Column(String(36), ForeignKey("comparisons.id"))
    
    # Fraud scores
    fraud_score = Column(Float, default=0.0)
    fraud_level = Column(String(20))  # critical, high, medium, low, suspicious
    
    # Indicators
    indicators = Column(JSON, default=[])
    critical_findings = Column(JSON, default=[])
    
    # Summary
    summary = Column(Text)
    recommendations = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comparison = relationship("Comparison", back_populates="fraud_records")
    
    def __repr__(self):
        return f"<FraudRecord {self.fraud_level}>"


class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # Action details
    action = Column(String(100), nullable=False)  # create, read, update, delete, export
    resource_type = Column(String(50))  # document, comparison, user, etc.
    resource_id = Column(String(36))
    
    # Additional details
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type}>"


class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # Session details
    token = Column(String(500), unique=True, index=True)
    refresh_token = Column(String(500))
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)


# Database utility functions
def init_db(database_url: str):
    """Initialize database connection"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    return engine, SessionLocal


def get_session(database_url: str):
    """Get database session"""
    engine, SessionLocal = init_db(database_url)
    return SessionLocal()
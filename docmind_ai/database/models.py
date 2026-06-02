"""
DocMind AI - Database Models
SQLAlchemy models for data persistence
"""

import uuid
from datetime import datetime

try:
    from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, BigInteger
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

Base = object


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


# Simple fallback models when SQLAlchemy is not available
class SimpleUser:
    """User model without SQLAlchemy"""
    def __init__(self, email, name=None, organization=None):
        self.id = generate_uuid()
        self.email = email
        self.name = name
        self.organization = organization
        self.preferences = {}
        self.created_at = datetime.utcnow()


class SimpleDocument:
    """Document model without SQLAlchemy"""
    def __init__(self, user_id, name, file_type):
        self.id = generate_uuid()
        self.user_id = user_id
        self.name = name
        self.file_type = file_type
        self.created_at = datetime.utcnow()


class SimpleComparison:
    """Comparison model without SQLAlchemy"""
    def __init__(self, user_id):
        self.id = generate_uuid()
        self.user_id = user_id
        self.created_at = datetime.utcnow()


# Export correct classes based on availability
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
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
        
        def __repr__(self):
            return f"<User {self.email}>"
    
    class Document(Base):
        """Document model"""
        __tablename__ = "documents"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        user_id = Column(String(36), ForeignKey("users.id"))
        name = Column(String(255), nullable=False)
        file_path = Column(String(500))
        file_type = Column(String(50))
        file_size = Column(BigInteger)
        page_count = Column(Integer)
        hash = Column(String(64))
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
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f"<DocumentVersion {self.document_id} v{self.version_number}>"
    
    class Comparison(Base):
        """Comparison model"""
        __tablename__ = "comparisons"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        user_id = Column(String(36), ForeignKey("users.id"))
        original_document_id = Column(String(36), ForeignKey("documents.id"))
        modified_document_id = Column(String(36), ForeignKey("documents.id"))
        overall_similarity = Column(Float, default=0.0)
        semantic_similarity = Column(Float, default=0.0)
        structural_similarity = Column(Float, default=0.0)
        lexical_similarity = Column(Float, default=0.0)
        total_changes = Column(Integer, default=0)
        insertions = Column(Integer, default=0)
        deletions = Column(Integer, default=0)
        modifications = Column(Integer, default=0)
        movements = Column(Integer, default=0)
        risk_score = Column(Float, default=0.0)
        fraud_score = Column(Float, default=0.0)
        health_score = Column(Float, default=0.0)
        changes_summary = Column(JSON, default={})
        risk_analysis = Column(JSON, default={})
        fraud_detection = Column(JSON, default={})
        executive_summary = Column(JSON, default={})
        status = Column(String(50), default="pending")
        error_message = Column(Text)
        language = Column(String(10), default="en")
        processing_time = Column(Float, default=0.0)
        metadata = Column(JSON, default={})
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f"<Comparison {self.id}>"
    
    class Change(Base):
        """Change model"""
        __tablename__ = "changes"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        comparison_id = Column(String(36), ForeignKey("comparisons.id"))
        change_type = Column(String(50))
        category = Column(String(100))
        severity = Column(String(20))
        location = Column(JSON)
        original_content = Column(Text)
        modified_content = Column(Text)
        similarity_score = Column(Float, default=0.0)
        semantic_significance = Column(Float, default=0.0)
        business_impact = Column(String(50))
        metadata = Column(JSON, default={})
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f"<Change {self.change_type}>"
    
    class RiskRecord(Base):
        """Risk analysis record"""
        __tablename__ = "risk_records"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        comparison_id = Column(String(36), ForeignKey("comparisons.id"))
        overall_risk_score = Column(Float, default=0.0)
        financial_risk = Column(Float, default=0.0)
        legal_risk = Column(Float, default=0.0)
        compliance_risk = Column(Float, default=0.0)
        operational_risk = Column(Float, default=0.0)
        risk_level = Column(String(20))
        risk_factors = Column(JSON, default=[])
        recommendations = Column(JSON, default=[])
        compliance_checks = Column(JSON, default={})
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f"<RiskRecord {self.risk_level}>"
    
    class FraudRecord(Base):
        """Fraud detection record"""
        __tablename__ = "fraud_records"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        comparison_id = Column(String(36), ForeignKey("comparisons.id"))
        fraud_score = Column(Float, default=0.0)
        fraud_level = Column(String(20))
        indicators = Column(JSON, default=[])
        critical_findings = Column(JSON, default=[])
        summary = Column(Text)
        recommendations = Column(JSON, default=[])
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f"<FraudRecord {self.fraud_level}>"
    
    class AuditLog(Base):
        """Audit log for tracking user actions"""
        __tablename__ = "audit_logs"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        user_id = Column(String(36), ForeignKey("users.id"))
        action = Column(String(100), nullable=False)
        resource_type = Column(String(50))
        resource_id = Column(String(36))
        details = Column(JSON, default={})
        ip_address = Column(String(45))
        user_agent = Column(String(500))
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def __repr__(self):
            return f"<AuditLog {self.action}>"
    
    class Session(Base):
        """User session model"""
        __tablename__ = "sessions"
        id = Column(String(36), primary_key=True, default=generate_uuid)
        user_id = Column(String(36), ForeignKey("users.id"))
        token = Column(String(500), unique=True, index=True)
        refresh_token = Column(String(500))
        ip_address = Column(String(45))
        user_agent = Column(String(500))
        created_at = Column(DateTime, default=datetime.utcnow)
        expires_at = Column(DateTime)
        last_activity = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
    
    def init_db(database_url: str):
        """Initialize database connection"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        return engine, SessionLocal
    
    def get_session(database_url: str):
        """Get database session"""
        engine, SessionLocal = init_db(database_url)
        return SessionLocal()

else:
    # Use simple classes when SQLAlchemy is not available
    User = SimpleUser
    Document = SimpleDocument
    Comparison = SimpleComparison
    DocumentVersion = None
    Change = None
    RiskRecord = None
    FraudRecord = None
    AuditLog = None
    Session = None
    
    def init_db(database_url: str):
        """Simple init without database"""
        return None, None
    
    def get_session(database_url: str):
        """Simple session getter"""
        return None

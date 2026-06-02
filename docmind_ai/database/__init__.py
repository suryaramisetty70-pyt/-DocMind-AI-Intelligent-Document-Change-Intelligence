"""
DocMind AI - Database Module
"""

from .models import (
    Base,
    User,
    Document,
    DocumentVersion,
    Comparison,
    Change,
    RiskRecord,
    FraudRecord,
    AuditLog,
    Session,
    init_db,
    get_session
)

__all__ = [
    "Base",
    "User",
    "Document",
    "DocumentVersion",
    "Comparison",
    "Change",
    "RiskRecord",
    "FraudRecord",
    "AuditLog",
    "Session",
    "init_db",
    "get_session"
]
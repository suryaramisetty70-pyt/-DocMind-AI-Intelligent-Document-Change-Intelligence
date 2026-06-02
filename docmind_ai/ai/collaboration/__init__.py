"""
DocMind AI - Collaboration Module
"""

from .collaboration_engine import (
    CollaborationEngine,
    CollaborationWebSocketHandler,
    CollabSession,
    CollabUser,
    Comment,
    Annotation,
    Activity,
    UserRole,
    ActivityType,
    PresenceManager,
    CommentManager,
    AnnotationManager,
    ActivityTracker
)

__all__ = [
    "CollaborationEngine",
    "CollaborationWebSocketHandler",
    "CollabSession",
    "CollabUser",
    "Comment",
    "Annotation",
    "Activity",
    "UserRole",
    "ActivityType",
    "PresenceManager",
    "CommentManager",
    "AnnotationManager",
    "ActivityTracker"
]
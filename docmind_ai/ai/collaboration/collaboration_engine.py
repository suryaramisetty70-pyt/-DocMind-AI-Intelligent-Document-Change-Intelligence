"""
DocMind AI - Real-time Collaboration Engine
WebSocket-based multi-user document review
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import json
from datetime import datetime
from collections import defaultdict


class UserRole(Enum):
    """User roles in collaboration"""
    VIEWER = "viewer"
    REVIEWER = "reviewer"
    EDITOR = "editor"
    ADMIN = "admin"


class ActivityType(Enum):
    """Types of user activities"""
    VIEW = "view"
    COMMENT = "comment"
    ANNOTATE = "annotate"
    APPROVE = "approve"
    REJECT = "reject"
    RESOLVE = "resolve"


@dataclass
class CollabUser:
    """Collaborative user"""
    user_id: str
    name: str
    email: str
    role: UserRole
    avatar_url: Optional[str] = None
    color: str = "#3B82F6"
    is_online: bool = False
    last_activity: Optional[datetime] = None


@dataclass
class Comment:
    """Comment on a document change"""
    comment_id: str
    user_id: str
    change_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    replies: List['Comment'] = field(default_factory=list)


@dataclass
class Annotation:
    """Annotation on document content"""
    annotation_id: str
    user_id: str
    page_number: int
    position: Dict[str, float]
    content: str
    annotation_type: str
    created_at: datetime
    color: str = "#FFFF00"


@dataclass
class Activity:
    """User activity log"""
    activity_id: str
    user_id: str
    activity_type: ActivityType
    target_id: str
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class CollabSession:
    """Collaboration session"""
    session_id: str
    comparison_id: str
    created_at: datetime
    created_by: str
    participants: List[CollabUser]
    comments: List[Comment]
    annotations: List[Annotation]
    activities: List[Activity]
    is_active: bool = True


class PresenceManager:
    """Track user presence in real-time"""
    
    def __init__(self):
        self._presence: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def update_presence(self, session_id: str, user_id: str, status: str) -> None:
        """Update user presence status"""
        self._presence[session_id][user_id] = {
            "status": status,
            "last_seen": datetime.now().isoformat(),
            "cursor_position": None
        }
    
    def get_online_users(self, session_id: str) -> List[str]:
        """Get list of online users in a session"""
        presence = self._presence.get(session_id, {})
        return [
            user_id for user_id, data in presence.items()
            if data.get("status") == "online"
        ]
    
    def update_cursor(self, session_id: str, user_id: str, position: Dict[str, Any]) -> None:
        """Update user cursor position"""
        if session_id in self._presence:
            if user_id in self._presence[session_id]:
                self._presence[session_id][user_id]["cursor_position"] = position


class CommentManager:
    """Manage comments on changes"""
    
    def __init__(self):
        self._comments: Dict[str, List[Comment]] = defaultdict(list)
    
    def add_comment(
        self,
        session_id: str,
        user_id: str,
        change_id: str,
        content: str
    ) -> Comment:
        """Add a comment to a change"""
        comment = Comment(
            comment_id=f"comment_{len(self._comments[session_id]) + 1}",
            user_id=user_id,
            change_id=change_id,
            content=content,
            created_at=datetime.now()
        )
        
        self._comments[session_id].append(comment)
        return comment
    
    def reply_to_comment(
        self,
        session_id: str,
        parent_comment_id: str,
        user_id: str,
        content: str
    ) -> Optional[Comment]:
        """Add a reply to an existing comment"""
        for comment in self._comments[session_id]:
            if comment.comment_id == parent_comment_id:
                reply = Comment(
                    comment_id=f"reply_{len(comment.replies) + 1}",
                    user_id=user_id,
                    change_id=comment.change_id,
                    content=content,
                    created_at=datetime.now()
                )
                comment.replies.append(reply)
                return reply
        return None
    
    def resolve_comment(self, session_id: str, comment_id: str, user_id: str) -> bool:
        """Mark a comment as resolved"""
        for comment in self._comments[session_id]:
            if comment.comment_id == comment_id:
                comment.resolved = True
                comment.resolved_by = user_id
                comment.updated_at = datetime.now()
                return True
        return False
    
    def get_comments_for_change(self, session_id: str, change_id: str) -> List[Comment]:
        """Get all comments for a specific change"""
        return [
            c for c in self._comments[session_id]
            if c.change_id == change_id and not c.resolved
        ]


class AnnotationManager:
    """Manage annotations on documents"""
    
    def __init__(self):
        self._annotations: Dict[str, List[Annotation]] = defaultdict(list)
    
    def add_annotation(
        self,
        session_id: str,
        user_id: str,
        page_number: int,
        position: Dict[str, float],
        content: str,
        ann_type: str = "note"
    ) -> Annotation:
        """Add an annotation to the document"""
        annotation = Annotation(
            annotation_id=f"annot_{len(self._annotations[session_id]) + 1}",
            user_id=user_id,
            page_number=page_number,
            position=position,
            content=content,
            annotation_type=ann_type,
            created_at=datetime.now()
        )
        
        self._annotations[session_id].append(annotation)
        return annotation
    
    def get_page_annotations(self, session_id: str, page_number: int) -> List[Annotation]:
        """Get all annotations for a specific page"""
        return [
            a for a in self._annotations[session_id]
            if a.page_number == page_number
        ]
    
    def delete_annotation(self, session_id: str, annotation_id: str) -> bool:
        """Delete an annotation"""
        for i, annotation in enumerate(self._annotations[session_id]):
            if annotation.annotation_id == annotation_id:
                del self._annotations[session_id][i]
                return True
        return False


class ActivityTracker:
    """Track and log user activities"""
    
    def __init__(self):
        self._activities: Dict[str, List[Activity]] = defaultdict(list)
    
    def log_activity(
        self,
        session_id: str,
        user_id: str,
        activity_type: ActivityType,
        target_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Activity:
        """Log a user activity"""
        activity = Activity(
            activity_id=f"activity_{len(self._activities[session_id]) + 1}",
            user_id=user_id,
            activity_type=activity_type,
            target_id=target_id,
            details=details or {},
            timestamp=datetime.now()
        )
        
        self._activities[session_id].append(activity)
        return activity
    
    def get_recent_activities(self, session_id: str, limit: int = 50) -> List[Activity]:
        """Get recent activities in a session"""
        activities = self._activities.get(session_id, [])
        return sorted(activities, key=lambda x: x.timestamp, reverse=True)[:limit]


class CollaborationEngine:
    """Main collaboration engine coordinating all components"""
    
    def __init__(self):
        self.presence = PresenceManager()
        self.comments = CommentManager()
        self.annotations = AnnotationManager()
        self.activity_tracker = ActivityTracker()
        self._sessions: Dict[str, CollabSession] = {}
    
    def create_session(
        self,
        comparison_id: str,
        created_by: CollabUser,
        participants: List[CollabUser]
    ) -> CollabSession:
        """Create a new collaboration session"""
        session_id = f"session_{comparison_id}_{datetime.now().timestamp()}"
        
        session = CollabSession(
            session_id=session_id,
            comparison_id=comparison_id,
            created_at=datetime.now(),
            created_by=created_by.user_id,
            participants=participants,
            comments=[],
            annotations=[],
            activities=[]
        )
        
        self._sessions[session_id] = session
        
        self.activity_tracker.log_activity(
            session_id,
            created_by.user_id,
            ActivityType.VIEW,
            session_id,
            {"action": "session_created"}
        )
        
        return session
    
    def join_session(self, session_id: str, user: CollabUser) -> bool:
        """Add a user to an existing session"""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        if any(p.user_id == user.user_id for p in session.participants):
            return True
        
        user.is_online = True
        session.participants.append(user)
        
        self.presence.update_presence(session_id, user.user_id, "online")
        
        self.activity_tracker.log_activity(
            session_id,
            user.user_id,
            ActivityType.VIEW,
            session_id,
            {"action": "joined_session"}
        )
        
        return True
    
    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Remove a user from a session"""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        for participant in session.participants:
            if participant.user_id == user_id:
                participant.is_online = False
        
        self.presence.update_presence(session_id, user_id, "offline")
        
        return True
    
    def add_comment(
        self,
        session_id: str,
        user_id: str,
        change_id: str,
        content: str
    ) -> Optional[Comment]:
        """Add a comment"""
        if session_id not in self._sessions:
            return None
        
        comment = self.comments.add_comment(session_id, user_id, change_id, content)
        
        self.activity_tracker.log_activity(
            session_id,
            user_id,
            ActivityType.COMMENT,
            comment.comment_id,
            {"change_id": change_id, "content_preview": content[:50]}
        )
        
        return comment
    
    def add_annotation(
        self,
        session_id: str,
        user_id: str,
        page_number: int,
        position: Dict[str, float],
        content: str,
        ann_type: str = "note"
    ) -> Optional[Annotation]:
        """Add an annotation"""
        if session_id not in self._sessions:
            return None
        
        annotation = self.annotations.add_annotation(
            session_id, user_id, page_number, position, content, ann_type
        )
        
        self.activity_tracker.log_activity(
            session_id,
            user_id,
            ActivityType.ANNOTATE,
            annotation.annotation_id,
            {"page": page_number, "type": ann_type}
        )
        
        return annotation
    
    def resolve_comment(self, session_id: str, comment_id: str, user_id: str) -> bool:
        """Resolve a comment"""
        result = self.comments.resolve_comment(session_id, comment_id, user_id)
        
        if result:
            self.activity_tracker.log_activity(
                session_id,
                user_id,
                ActivityType.RESOLVE,
                comment_id,
                {}
            )
        
        return result
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a session"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        return {
            "session_id": session_id,
            "comparison_id": session.comparison_id,
            "participants": [
                {
                    "user_id": p.user_id,
                    "name": p.name,
                    "role": p.role.value,
                    "is_online": p.is_online
                }
                for p in session.participants
            ],
            "online_users": self.presence.get_online_users(session_id),
            "comments_count": len(self.comments._comments.get(session_id, [])),
            "annotations_count": len(self.annotations._annotations.get(session_id, [])),
            "recent_activities": [
                {
                    "user_id": a.user_id,
                    "type": a.activity_type.value,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.activity_tracker.get_recent_activities(session_id, 10)
            ]
        }
    
    def broadcast_update(self, session_id: str, update_type: str, data: Dict[str, Any]) -> str:
        """Create a broadcast message for session updates"""
        return json.dumps({
            "type": update_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })


class CollaborationWebSocketHandler:
    """WebSocket handler for real-time collaboration"""
    
    def __init__(self, collab_engine: CollaborationEngine):
        self.engine = collab_engine
        self._handlers: Dict[str, Callable] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers"""
        self._handlers = {
            "join": self._handle_join,
            "leave": self._handle_leave,
            "comment": self._handle_comment,
            "annotate": self._handle_annotate,
            "cursor": self._handle_cursor,
            "resolve": self._handle_resolve
        }
    
    async def handle_message(self, session_id: str, user_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WebSocket message"""
        action = message.get("action")
        
        if action in self._handlers:
            handler = self._handlers[action]
            return await handler(session_id, user_id, message)
        
        return {"error": f"Unknown action: {action}"}
    
    async def _handle_join(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle user join"""
        user = CollabUser(
            user_id=user_id,
            name=message.get("name", "Unknown"),
            email=message.get("email", ""),
            role=UserRole(message.get("role", "viewer"))
        )
        
        self.engine.join_session(session_id, user)
        
        return {
            "type": "user_joined",
            "user_id": user_id,
            "state": self.engine.get_session_state(session_id)
        }
    
    async def _handle_leave(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle user leave"""
        self.engine.leave_session(session_id, user_id)
        
        return {
            "type": "user_left",
            "user_id": user_id
        }
    
    async def _handle_comment(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle new comment"""
        comment = self.engine.add_comment(
            session_id,
            user_id,
            message.get("change_id", ""),
            message.get("content", "")
        )
        
        if comment:
            return {
                "type": "new_comment",
                "comment": {
                    "comment_id": comment.comment_id,
                    "user_id": comment.user_id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat()
                }
            }
        return {"error": "Failed to add comment"}
    
    async def _handle_annotate(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle new annotation"""
        annotation = self.engine.add_annotation(
            session_id,
            user_id,
            message.get("page", 1),
            message.get("position", {}),
            message.get("content", ""),
            message.get("annotation_type", "note")
        )
        
        if annotation:
            return {
                "type": "new_annotation",
                "annotation": {
                    "annotation_id": annotation.annotation_id,
                    "page": annotation.page_number,
                    "content": annotation.content
                }
            }
        return {"error": "Failed to add annotation"}
    
    async def _handle_cursor(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle cursor position update"""
        self.engine.presence.update_cursor(
            session_id,
            user_id,
            message.get("position", {})
        )
        
        return {
            "type": "cursor_updated",
            "user_id": user_id
        }
    
    async def _handle_resolve(self, session_id: str, user_id: str, message: Dict) -> Dict[str, Any]:
        """Handle comment resolution"""
        self.engine.resolve_comment(
            session_id,
            message.get("comment_id", ""),
            user_id
        )
        
        return {
            "type": "comment_resolved",
            "comment_id": message.get("comment_id")
        }
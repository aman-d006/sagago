from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    actor_username: str
    actor_avatar: Optional[str] = None
    story_title: Optional[str] = None
    story_id: Optional[int] = None
    comment_preview: Optional[str] = None
    content: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    pages: int

class NotificationCountResponse(BaseModel):
    unread_count: int

class NotificationMarkRead(BaseModel):
    message: str
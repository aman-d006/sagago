from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    receiver_id: int

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime
    sender_username: str
    sender_avatar: Optional[str] = None
    receiver_username: str
    receiver_avatar: Optional[str] = None

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    last_message: str
    last_message_at: datetime
    unread_count: int
    is_online: bool = False

    class Config:
        from_attributes = True

class ConversationDetailResponse(BaseModel):
    id: int
    user: dict
    messages: List[MessageResponse]
    total: int
    page: int
    pages: int

class UnreadCountResponse(BaseModel):
    total_unread: int
    conversations: List[dict]

class MarkReadResponse(BaseModel):
    message: str
    marked_count: int
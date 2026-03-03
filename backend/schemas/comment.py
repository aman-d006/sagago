from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    story_id: int
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    user_avatar: Optional[str] = None
    story_id: int
    parent_id: Optional[int] = None
    like_count: int
    reply_count: int
    is_edited: bool
    created_at: datetime
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True

class CommentListResponse(BaseModel):
    id: int
    content: str
    username: str
    user_avatar: Optional[str] = None
    like_count: int
    reply_count: int
    created_at: datetime
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True
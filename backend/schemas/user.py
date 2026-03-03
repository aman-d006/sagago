from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    pass

class UserProfileResponse(UserBase):
    followers_count: int = 0
    following_count: int = 0
    stories_count: int = 0

class UserStoryResponse(BaseModel):
    id: int
    title: str
    excerpt: Optional[str] = None
    created_at: datetime
    like_count: int
    comment_count: int
    view_count: int
    story_type: Optional[str] = None  # Add this line

    class Config:
        from_attributes = True
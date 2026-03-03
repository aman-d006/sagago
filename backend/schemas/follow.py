from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FollowResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    followed_at: datetime

    class Config:
        from_attributes = True

class FollowStats(BaseModel):
    followers_count: int
    following_count: int
    is_following: bool = False
    is_follower: bool = False

class FollowAction(BaseModel):
    message: str
    is_following: bool
    followers_count: int
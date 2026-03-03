from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FeedStoryAuthor(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class FeedStoryResponse(BaseModel):
    id: int
    title: str
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    author: FeedStoryAuthor
    like_count: int
    comment_count: int
    created_at: datetime
    is_liked_by_current_user: bool = False
    is_boosted_by_current_user: bool = False

    class Config:
        from_attributes = True

class FeedResponse(BaseModel):
    stories: List[FeedStoryResponse]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool

class FeedFilter(BaseModel):
    feed_type: str = "following"  
    timeframe: Optional[str] = "all"  
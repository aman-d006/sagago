from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BookmarkBase(BaseModel):
    story_id: int

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    story_id: int
    created_at: datetime
    is_read: bool
    story_title: str
    story_excerpt: Optional[str] = None
    story_author: str
    story_cover: Optional[str] = None

    class Config:
        from_attributes = True

class BookmarkUpdate(BaseModel):
    is_read: bool

class BookmarkListResponse(BaseModel):
    bookmarks: list[BookmarkResponse]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool
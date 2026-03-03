from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

class StoryOptionsSchema(BaseModel):
    text: str
    node_id: Optional[int] = None

class StoryNodeBase(BaseModel):
    content: str
    is_ending: bool = False
    is_winning_ending: bool = False

class CompleteStoryNodeResponse(StoryNodeBase):
    id: int
    options: List[StoryOptionsSchema] = []

    class Config:
        from_attributes = True

class StoryBase(BaseModel):
    title: str
    session_id: Optional[str] = None

    class Config:
        from_attributes = True

class CreatyStoryRequest(BaseModel):
    theme: str

class StoryAuthor(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class CompleteStoryResponse(StoryBase):
    id: int
    content: Optional[str] = None
    created_at: datetime
    root_node: Optional[CompleteStoryNodeResponse] = None
    all_nodes: Optional[Dict[int, CompleteStoryNodeResponse]] = None
    like_count: int = 0
    comment_count: int = 0
    view_count: int = 0
    is_liked_by_current_user: bool = False
    author: Optional[StoryAuthor] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FullStoryResponse(BaseModel):
    id: int
    title: str
    content: str
    excerpt: str
    cover_image: Optional[str] = None
    author: StoryAuthor
    like_count: int
    comment_count: int
    view_count: int
    created_at: datetime
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TemplateStructure(BaseModel):
    outline: List[str]
    characters: Optional[List[Dict[str, str]]] = None
    settings: Optional[List[str]] = None
    plot_points: Optional[List[str]] = None

class TemplateBase(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    content_structure: Dict[str, Any]
    prompt: Optional[str] = None
    cover_image: Optional[str] = None
    is_premium: bool = False

class TemplateCreate(TemplateBase):
    pass

class TemplateResponse(TemplateBase):
    id: int
    usage_count: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_username: Optional[str] = None
    is_favorite: bool = False

    class Config:
        from_attributes = True

class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    content_structure: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None
    cover_image: Optional[str] = None
    is_premium: Optional[bool] = None

class WritingPromptResponse(BaseModel):
    id: int
    prompt: str
    genre: Optional[str] = None
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int
    page: int
    pages: int

class UseTemplateRequest(BaseModel):
    template_id: int
    custom_title: Optional[str] = None

class UseTemplateResponse(BaseModel):
    story_id: int
    title: str
    message: str
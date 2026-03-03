from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class StoryJobBase(BaseModel):
    theme :str

class StoryJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    story_id: Optional[int] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StoryJobCreate(StoryJobBase):
    pass
from pydantic import BaseModel
from datetime import datetime

class LikeResponse(BaseModel):
    id: int
    user_id: int
    story_id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class LikeAction(BaseModel):
    message: str
    liked: bool
    like_count: int
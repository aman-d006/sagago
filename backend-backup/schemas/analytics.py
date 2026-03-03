from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StoryAnalytics(BaseModel):
    story_id: int
    title: str
    created_at: datetime
    views: int
    likes: int
    comments: int
    engagement_rate: float

    class Config:
        from_attributes = True

class UserAnalytics(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str] = None
    joined_date: datetime
    total_stories: int
    total_views: int
    total_likes_received: int
    total_comments_received: int
    followers_count: int
    following_count: int
    top_stories: List[StoryAnalytics]

    class Config:
        from_attributes = True

class DailyMetricResponse(BaseModel):
    date: str
    new_users: int
    new_stories: int
    total_views: int
    total_likes: int
    total_comments: int
    active_users: int

class TimeSeriesData(BaseModel):
    labels: List[str]
    views: List[int]
    likes: List[int]
    comments: List[int]
    users: List[int]

class PlatformOverview(BaseModel):
    total_users: int
    total_stories: int
    total_views: int
    total_likes: int
    total_comments: int
    avg_stories_per_user: float
    avg_views_per_story: float
    engagement_rate: float

class StoryEngagementResponse(BaseModel):
    story_id: int
    title: str
    views: int
    likes: int
    comments: int
    like_rate: float
    comment_rate: float
    completion_rate: Optional[float] = None
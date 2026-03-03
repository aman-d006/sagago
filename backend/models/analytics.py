from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class StoryView(Base):
    __tablename__ = "story_views"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String, nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())

    story = relationship("Story", back_populates="views")
    user = relationship("User")

class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    total_stories = Column(Integer, default=0)
    new_stories = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
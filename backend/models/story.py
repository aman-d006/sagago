from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    genre = Column(String, nullable=True, index=True)
    session_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_published = Column(Boolean, default=False)
    story_type = Column(String, default="interactive")

    nodes = relationship("StoryNode", back_populates="story", cascade="all, delete-orphan")
    author = relationship("User", back_populates="stories")
    likes = relationship("StoryLike", back_populates="story", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="story", cascade="all, delete-orphan")
    views = relationship("StoryView", back_populates="story", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="story", cascade="all, delete-orphan")

    @property
    def like_count(self):
        return len(self.likes)

    @property
    def comment_count(self):
        return len(self.comments)
    
    @property
    def view_count(self):
        return len(self.views)

class StoryNode(Base):
    __tablename__ = "story_nodes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    content = Column(String)
    is_root = Column(Boolean, default=False)
    is_ending = Column(Boolean, default=False)
    is_winning_ending = Column(Boolean, default=False)
    options = Column(JSON, default=list)

    story = relationship("Story", back_populates="nodes")
    
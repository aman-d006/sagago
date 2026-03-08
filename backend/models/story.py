from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import json

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text, nullable=True)
    excerpt = Column(String, nullable=True)
    cover_image = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, index=True)
    story_type = Column(String, default="written")  
    genre = Column(String, nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
   
    author = relationship("User", back_populates="stories")
    nodes = relationship("StoryNode", back_populates="story", cascade="all, delete-orphan")
    likes = relationship("StoryLike", back_populates="story", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="story", cascade="all, delete-orphan")
    views = relationship("StoryView", back_populates="story", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="story", cascade="all, delete-orphan")

class StoryNode(Base):
    __tablename__ = "story_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"))
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    is_root = Column(Boolean, default=False)
    is_ending = Column(Boolean, default=False)
    is_winning_ending = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
 
    story = relationship("Story", back_populates="nodes")
    outgoing_options = relationship("StoryOption", 
                                   foreign_keys="StoryOption.node_id",
                                   back_populates="node", 
                                   cascade="all, delete-orphany")
    incoming_options = relationship("StoryOption",
                                   foreign_keys="StoryOption.next_node_id",
                                   back_populates="next_node")

class StoryOption(Base):
    __tablename__ = "story_options"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("story_nodes.id", ondelete="CASCADE"))
    next_node_id = Column(Integer, ForeignKey("story_nodes.id", ondelete="CASCADE"))
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
  
    node = relationship("StoryNode", foreign_keys=[node_id], back_populates="outgoing_options")
    next_node = relationship("StoryNode", foreign_keys=[next_node_id], back_populates="incoming_options")

class StoryView(Base):
    __tablename__ = "story_views"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String, nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
 
    story = relationship("Story", back_populates="views")
    user = relationship("User", back_populates="story_views")
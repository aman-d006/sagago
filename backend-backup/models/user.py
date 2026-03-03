from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)

    stories = relationship("Story", back_populates="author", cascade="all, delete-orphan")
    liked_stories = relationship("StoryLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following", cascade="all, delete-orphan")
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete-orphan")
    story_views = relationship("StoryView", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan")
    conversations_as_user1 = relationship("Conversation", foreign_keys="Conversation.user1_id", cascade="all, delete-orphan")
    conversations_as_user2 = relationship("Conversation", foreign_keys="Conversation.user2_id", cascade="all, delete-orphan")
    created_templates = relationship("Template", foreign_keys="Template.created_by", back_populates="creator")
    saved_templates = relationship("UserTemplate", back_populates="user")

    @property
    def followers_count(self):
        return len([f for f in self.followers if f.is_active])

    @property
    def following_count(self):
        return len([f for f in self.following if f.is_active])
    
    @property
    def stories_count(self):
        return len(self.stories)
    
    @property
    def total_story_views(self):
        return sum(story.view_count for story in self.stories)
    
    @property
    def total_likes_received(self):
        return sum(story.like_count for story in self.stories)
    
    @property
    def total_comments_received(self):
        return sum(story.comment_count for story in self.stories)
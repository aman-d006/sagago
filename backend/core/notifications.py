from datetime import datetime
import logging
from db import helpers
from db.database import settings

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def create_follow_notification(db, followed_user_id: int, follower_id: int):
        """Create a notification when someone follows a user"""
        try:
            content = f" started following you"
            
            if settings.USE_TURSO:
                # Use Turso helper
                helpers.create_notification(
                    user_id=followed_user_id,
                    type="follow",
                    content=content,
                    related_id=follower_id
                )
                logger.info(f"Created follow notification in Turso: {follower_id} -> {followed_user_id}")
            else:
                # Use SQLAlchemy
                from models.notification import Notification
                from models.user import User
                
                follower = db.query(User).filter(User.id == follower_id).first()
                if follower:
                    notification = Notification(
                        user_id=followed_user_id,
                        notification_type="follow",
                        content=f"@{follower.username} started following you",
                        actor_id=follower_id
                    )
                    db.add(notification)
                    db.commit()
                    logger.info(f"Created follow notification in SQLite: {follower_id} -> {followed_user_id}")
        except Exception as e:
            logger.error(f"Error creating follow notification: {e}")
    
    @staticmethod
    def create_like_notification(db, story_owner_id: int, actor_id: int, story_id: int):
        """Create a notification when someone likes a story"""
        try:
            content = f" liked your story"
            
            if settings.USE_TURSO:
                helpers.create_notification(
                    user_id=story_owner_id,
                    type="like",
                    content=content,
                    related_id=story_id
                )
                logger.info(f"Created like notification in Turso: {actor_id} -> story {story_id}")
            else:
                from models.notification import Notification
                from models.user import User
                from models.story import Story
                
                actor = db.query(User).filter(User.id == actor_id).first()
                story = db.query(Story).filter(Story.id == story_id).first()
                if actor and story:
                    notification = Notification(
                        user_id=story_owner_id,
                        notification_type="like",
                        content=f"@{actor.username} liked your story '{story.title}'",
                        actor_id=actor_id,
                        story_id=story_id
                    )
                    db.add(notification)
                    db.commit()
                    logger.info(f"Created like notification in SQLite: {actor_id} -> story {story_id}")
        except Exception as e:
            logger.error(f"Error creating like notification: {e}")
    
    @staticmethod
    def create_comment_notification(db, story_owner_id: int, actor_id: int, story_id: int, comment_id: int, comment_content: str):
        """Create a notification when someone comments on a story"""
        try:
            content = f" commented on your story"
            
            if settings.USE_TURSO:
                helpers.create_notification(
                    user_id=story_owner_id,
                    type="comment",
                    content=content,
                    related_id=story_id
                )
                logger.info(f"Created comment notification in Turso: {actor_id} -> story {story_id}")
            else:
                from models.notification import Notification
                from models.user import User
                from models.story import Story
                
                actor = db.query(User).filter(User.id == actor_id).first()
                story = db.query(Story).filter(Story.id == story_id).first()
                if actor and story:
                    notification = Notification(
                        user_id=story_owner_id,
                        notification_type="comment",
                        content=f"@{actor.username} commented on your story '{story.title}'",
                        actor_id=actor_id,
                        story_id=story_id,
                        comment_id=comment_id
                    )
                    db.add(notification)
                    db.commit()
                    logger.info(f"Created comment notification in SQLite: {actor_id} -> story {story_id}")
        except Exception as e:
            logger.error(f"Error creating comment notification: {e}")
    
    @staticmethod
    def create_reply_notification(db, parent_comment_owner_id: int, actor_id: int, story_id: int, comment_id: int, reply_content: str):
        """Create a notification when someone replies to a comment"""
        try:
            content = f" replied to your comment"
            
            if settings.USE_TURSO:
                helpers.create_notification(
                    user_id=parent_comment_owner_id,
                    type="reply",
                    content=content,
                    related_id=story_id
                )
                logger.info(f"Created reply notification in Turso: {actor_id} -> comment {comment_id}")
            else:
                from models.notification import Notification
                from models.user import User
                
                actor = db.query(User).filter(User.id == actor_id).first()
                if actor:
                    notification = Notification(
                        user_id=parent_comment_owner_id,
                        notification_type="reply",
                        content=f"@{actor.username} replied to your comment",
                        actor_id=actor_id,
                        story_id=story_id,
                        comment_id=comment_id
                    )
                    db.add(notification)
                    db.commit()
                    logger.info(f"Created reply notification in SQLite: {actor_id} -> comment {comment_id}")
        except Exception as e:
            logger.error(f"Error creating reply notification: {e}")
from sqlalchemy.orm import Session
from models.notification import Notification
from models.user import User
from models.story import Story
from models.comment import Comment

class NotificationService:
    
    @staticmethod
    def create_like_notification(
        db: Session,
        story_owner_id: int,
        actor_id: int,
        story_id: int
    ):
        if story_owner_id == actor_id:
            return  # Don't notify if liking own story
        
        notification = Notification(
            user_id=story_owner_id,
            actor_id=actor_id,
            notification_type="like",
            story_id=story_id
        )
        db.add(notification)
        db.commit()
    
    @staticmethod
    def create_comment_notification(
        db: Session,
        story_owner_id: int,
        actor_id: int,
        story_id: int,
        comment_id: int,
        comment_content: str
    ):
        if story_owner_id == actor_id:
            return  # Don't notify if commenting on own story
        
        notification = Notification(
            user_id=story_owner_id,
            actor_id=actor_id,
            notification_type="comment",
            story_id=story_id,
            comment_id=comment_id,
            content=comment_content[:100]
        )
        db.add(notification)
        db.commit()
    
    @staticmethod
    def create_reply_notification(
        db: Session,
        parent_comment_owner_id: int,
        actor_id: int,
        story_id: int,
        comment_id: int,
        reply_content: str
    ):
        if parent_comment_owner_id == actor_id:
            return  # Don't notify if replying to own comment
        
        notification = Notification(
            user_id=parent_comment_owner_id,
            actor_id=actor_id,
            notification_type="reply",
            story_id=story_id,
            comment_id=comment_id,
            content=reply_content[:100]
        )
        db.add(notification)
        db.commit()
    
    @staticmethod
    def create_follow_notification(
        db: Session,
        followed_user_id: int,
        follower_id: int
    ):
        if followed_user_id == follower_id:
            return  # Don't notify if following self
        
        notification = Notification(
            user_id=followed_user_id,
            actor_id=follower_id,
            notification_type="follow"
        )
        db.add(notification)
        db.commit()
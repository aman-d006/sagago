# routers/comment.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user, get_current_user_optional
from core.notifications import NotificationService

router = APIRouter(prefix="/comments", tags=["comments"])
logger = logging.getLogger(__name__)

@router.post("", response_model=dict)
def create_comment(
    comment_data: dict,
    current_user = Depends(get_current_active_user)
):
    content = comment_data.get("content")
    story_id = comment_data.get("story_id")
    parent_id = comment_data.get("parent_id")
    
    if not content or not story_id:
        raise HTTPException(status_code=400, detail="Content and story_id are required")
    
    logger.info(f"📝 Creating comment for story {story_id} by user {current_user.id}")
    
    if settings.USE_TURSO:
        # Check if story exists
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        # Check if parent comment exists if provided
        if parent_id:
            parent = helpers.get_comment(parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent comment not found")
        
        # Create comment
        comment = helpers.create_comment(story_id, current_user.id, content, parent_id)
        if not comment:
            raise HTTPException(status_code=500, detail="Failed to create comment")
        
        # Create notifications
        if parent_id and parent:
            # This is a reply to a comment
            if parent["user_id"] != current_user.id:
                NotificationService.create_reply_notification(
                    db=None,
                    parent_comment_owner_id=parent["user_id"],
                    actor_id=current_user.id,
                    story_id=story_id,
                    comment_id=parent["id"],
                    reply_content=content
                )
        else:
            # This is a comment on a story
            if story["user_id"] and story["user_id"] != current_user.id:
                NotificationService.create_comment_notification(
                    db=None,
                    story_owner_id=story["user_id"],
                    actor_id=current_user.id,
                    story_id=story_id,
                    comment_id=comment["id"],
                    comment_content=content
                )
        
        return comment
    
    else:
        from sqlalchemy.orm import Session
        from models.user import User
        from models.story import Story
        from models.comment import Comment, CommentLike
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        parent = None
        if parent_id:
            parent = db.query(Comment).filter(Comment.id == parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent comment not found")
        
        db_comment = Comment(
            content=content,
            user_id=current_user.id,
            story_id=story_id,
            parent_id=parent_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        
        # Create notifications
        if parent_id and parent:
            if parent.user_id != current_user.id:
                NotificationService.create_reply_notification(
                    db=db,
                    parent_comment_owner_id=parent.user_id,
                    actor_id=current_user.id,
                    story_id=story_id,
                    comment_id=parent.id,
                    reply_content=content
                )
        else:
            if story.user_id and story.user_id != current_user.id:
                NotificationService.create_comment_notification(
                    db=db,
                    story_owner_id=story.user_id,
                    actor_id=current_user.id,
                    story_id=story_id,
                    comment_id=db_comment.id,
                    comment_content=content
                )
        
        return {
            "id": db_comment.id,
            "content": db_comment.content,
            "user_id": current_user.id,
            "username": current_user.username,
            "user_avatar": current_user.avatar_url,
            "story_id": db_comment.story_id,
            "parent_id": db_comment.parent_id,
            "like_count": 0,
            "reply_count": 0,
            "is_edited": False,
            "created_at": db_comment.created_at,
            "is_liked_by_current_user": False
        }

@router.get("/story/{story_id}", response_model=List[dict])
def get_story_comments(
    story_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        comments = helpers.get_story_comments(story_id)
        
        # Apply pagination
        paginated_comments = comments[skip:skip+limit]
        
        result = []
        for comment in paginated_comments:
            is_liked = False
            if current_user:
                is_liked = helpers.is_comment_liked(current_user.id, comment["id"])
            
            # Get replies count
            replies = helpers.get_comment_replies(comment["id"])
            
            result.append({
                "id": comment["id"],
                "content": comment["content"],
                "username": comment.get("username", "Unknown"),
                "user_avatar": comment.get("avatar_url"),
                "like_count": comment.get("like_count", 0),
                "reply_count": len(replies),
                "created_at": comment.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return result
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.story import Story
        from models.comment import Comment, CommentLike
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        comments = db.query(Comment).filter(
            Comment.story_id == story_id,
            Comment.parent_id == None
        ).order_by(desc(Comment.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for comment in comments:
            is_liked = False
            if current_user:
                is_liked = db.query(CommentLike).filter(
                    CommentLike.user_id == current_user.id,
                    CommentLike.comment_id == comment.id
                ).first() is not None
            
            result.append({
                "id": comment.id,
                "content": comment.content,
                "username": comment.author.username,
                "user_avatar": comment.author.avatar_url,
                "like_count": comment.like_count,
                "reply_count": comment.reply_count,
                "created_at": comment.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return result

@router.get("/{comment_id}/replies", response_model=List[dict])
def get_comment_replies(
    comment_id: int,
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        comment = helpers.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        replies = helpers.get_comment_replies(comment_id)
        
        result = []
        for reply in replies:
            is_liked = False
            if current_user:
                is_liked = helpers.is_comment_liked(current_user.id, reply["id"])
            
            result.append({
                "id": reply["id"],
                "content": reply["content"],
                "username": reply.get("username", "Unknown"),
                "user_avatar": reply.get("avatar_url"),
                "like_count": reply.get("like_count", 0),
                "reply_count": 0,
                "created_at": reply.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return result
    
    else:
        from sqlalchemy.orm import Session
        from models.comment import Comment, CommentLike
        
        db = next(get_db())
        
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        replies = db.query(Comment).filter(Comment.parent_id == comment_id).order_by(Comment.created_at).all()
        
        result = []
        for reply in replies:
            is_liked = False
            if current_user:
                is_liked = db.query(CommentLike).filter(
                    CommentLike.user_id == current_user.id,
                    CommentLike.comment_id == reply.id
                ).first() is not None
            
            result.append({
                "id": reply.id,
                "content": reply.content,
                "username": reply.author.username,
                "user_avatar": reply.author.avatar_url,
                "like_count": reply.like_count,
                "reply_count": reply.reply_count,
                "created_at": reply.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return result

@router.put("/{comment_id}")
def update_comment(
    comment_id: int,
    comment_update: dict,
    current_user = Depends(get_current_active_user)
):
    content = comment_update.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    if settings.USE_TURSO:
        comment = helpers.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
        
        success = helpers.update_comment(comment_id, current_user.id, content)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update comment")
        
        return {"message": "Comment updated successfully"}
    
    else:
        from sqlalchemy.orm import Session
        from models.comment import Comment
        
        db = next(get_db())
        
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
        
        comment.content = content
        comment.is_edited = True
        db.commit()
        
        return {"message": "Comment updated successfully"}

@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        comment = helpers.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        success = helpers.delete_comment(comment_id, current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete comment")
        
        return {"message": "Comment deleted successfully"}
    
    else:
        from sqlalchemy.orm import Session
        from models.comment import Comment
        
        db = next(get_db())
        
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        db.delete(comment)
        db.commit()
        
        return {"message": "Comment deleted successfully"}

@router.post("/{comment_id}/like")
def like_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        comment = helpers.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        result = helpers.toggle_comment_like(current_user.id, comment_id)
        
        return {
            "message": "Comment liked" if result["liked"] else "Comment unliked",
            "liked": result["liked"],
            "like_count": result["like_count"]
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.comment import Comment, CommentLike
        
        db = next(get_db())
        
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        existing_like = db.query(CommentLike).filter(
            CommentLike.user_id == current_user.id,
            CommentLike.comment_id == comment_id
        ).first()
        
        if existing_like:
            db.delete(existing_like)
            db.commit()
            message = "Comment unliked"
            liked = False
        else:
            new_like = CommentLike(
                user_id=current_user.id,
                comment_id=comment_id
            )
            db.add(new_like)
            db.commit()
            message = "Comment liked"
            liked = True
        
        like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
        
        return {
            "message": message,
            "liked": liked,
            "like_count": like_count
        }
# routers/like.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user
from core.notifications import NotificationService

router = APIRouter(prefix="/stories", tags=["likes"])
logger = logging.getLogger(__name__)

@router.post("/{story_id}/like", response_model=dict)
def like_story(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"❤️ Like/unlike story {story_id} by user {current_user.id}")
    
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        result = helpers.toggle_story_like(current_user.id, story_id)
        
        # Create notification if liked
        if result["liked"] and story["user_id"] and story["user_id"] != current_user.id:
            NotificationService.create_like_notification(
                db=None,
                story_owner_id=story["user_id"],
                actor_id=current_user.id,
                story_id=story_id
            )
        
        return {
            "message": "Story liked" if result["liked"] else "Story unliked",
            "liked": result["liked"],
            "like_count": result["like_count"]
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.like import StoryLike
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        existing_like = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story_id
        ).first()
        
        if existing_like:
            db.delete(existing_like)
            db.commit()
            message = "Story unliked"
            liked = False
        else:
            new_like = StoryLike(
                user_id=current_user.id,
                story_id=story_id
            )
            db.add(new_like)
            db.commit()
            message = "Story liked"
            liked = True
            
            if story.user_id and story.user_id != current_user.id:
                NotificationService.create_like_notification(
                    db=db,
                    story_owner_id=story.user_id,
                    actor_id=current_user.id,
                    story_id=story_id
                )
        
        like_count = db.query(StoryLike).filter(StoryLike.story_id == story_id).count()
        
        return {
            "message": message,
            "liked": liked,
            "like_count": like_count
        }

@router.get("/{story_id}/likes/count")
def get_like_count(
    story_id: int
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        return {
            "story_id": story_id,
            "like_count": story.get("like_count", 0)
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.like import StoryLike
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        like_count = db.query(StoryLike).filter(StoryLike.story_id == story_id).count()
        return {"story_id": story_id, "like_count": like_count}

@router.get("/{story_id}/liked")
def check_if_liked(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        liked = helpers.is_liked(current_user.id, story_id)
        
        return {"story_id": story_id, "liked": liked}
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.like import StoryLike
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        liked = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story_id
        ).first() is not None
        
        return {"story_id": story_id, "liked": liked}
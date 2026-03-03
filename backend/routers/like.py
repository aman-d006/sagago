from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.story import Story
from models.like import StoryLike
from schemas.like import LikeAction
from core.auth import get_current_active_user
from core.notifications import NotificationService

router = APIRouter(prefix="/stories", tags=["likes"])

@router.post("/{story_id}/like", response_model=LikeAction)
def like_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
        
        # Create notification
        if story.user_id and story.user_id != current_user.id:
            NotificationService.create_like_notification(
                db=db,
                story_owner_id=story.user_id,
                actor_id=current_user.id,
                story_id=story_id
            )

    like_count = db.query(StoryLike).filter(StoryLike.story_id == story_id).count()

    return LikeAction(
        message=message,
        liked=liked,
        like_count=like_count
    )

@router.get("/{story_id}/likes/count")
def get_like_count(
    story_id: int,
    db: Session = Depends(get_db)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    like_count = db.query(StoryLike).filter(StoryLike.story_id == story_id).count()
    return {"story_id": story_id, "like_count": like_count}

@router.get("/{story_id}/liked")
def check_if_liked(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    liked = db.query(StoryLike).filter(
        StoryLike.user_id == current_user.id,
        StoryLike.story_id == story_id
    ).first() is not None

    return {"story_id": story_id, "liked": liked}
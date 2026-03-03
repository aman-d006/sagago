from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from db.database import get_db
from models.user import User
from models.story import Story
from models.comment import Comment, CommentLike
from schemas.comment import CommentCreate, CommentResponse, CommentUpdate, CommentListResponse
from core.auth import get_current_active_user
from core.notifications import NotificationService

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("", response_model=CommentResponse)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == comment.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    parent = None
    if comment.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    db_comment = Comment(
        content=comment.content,
        user_id=current_user.id,
        story_id=comment.story_id,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Create notification
    if comment.parent_id and parent:
        # This is a reply to a comment
        if parent.user_id != current_user.id:
            NotificationService.create_reply_notification(
                db=db,
                parent_comment_owner_id=parent.user_id,
                actor_id=current_user.id,
                story_id=comment.story_id,
                comment_id=parent.id,
                reply_content=comment.content
            )
    else:
        # This is a comment on a story
        if story.user_id and story.user_id != current_user.id:
            NotificationService.create_comment_notification(
                db=db,
                story_owner_id=story.user_id,
                actor_id=current_user.id,
                story_id=comment.story_id,
                comment_id=db_comment.id,
                comment_content=comment.content
            )

    return CommentResponse(
        id=db_comment.id,
        content=db_comment.content,
        user_id=current_user.id,
        username=current_user.username,
        user_avatar=current_user.avatar_url,
        story_id=db_comment.story_id,
        parent_id=db_comment.parent_id,
        like_count=0,
        reply_count=0,
        is_edited=False,
        created_at=db_comment.created_at,
        is_liked_by_current_user=False
    )

@router.get("/story/{story_id}", response_model=List[CommentListResponse])
def get_story_comments(
    story_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
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

        result.append(CommentListResponse(
            id=comment.id,
            content=comment.content,
            username=comment.author.username,
            user_avatar=comment.author.avatar_url,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            created_at=comment.created_at,
            is_liked_by_current_user=is_liked
        ))

    return result

@router.get("/{comment_id}/replies", response_model=List[CommentListResponse])
def get_comment_replies(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
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

        result.append(CommentListResponse(
            id=reply.id,
            content=reply.content,
            username=reply.author.username,
            user_avatar=reply.author.avatar_url,
            like_count=reply.like_count,
            reply_count=reply.reply_count,
            created_at=reply.created_at,
            is_liked_by_current_user=is_liked
        ))

    return result

@router.put("/{comment_id}")
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    comment.content = comment_update.content
    comment.is_edited = True
    db.commit()

    return {"message": "Comment updated successfully"}

@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
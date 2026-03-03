from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from db.database import get_db
from models.user import User
from models.story import Story
from models.bookmark import Bookmark
from schemas.bookmark import (
    BookmarkCreate,
    BookmarkResponse,
    BookmarkUpdate,
    BookmarkListResponse
)
from core.auth import get_current_active_user

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])

@router.post("/", response_model=BookmarkResponse)
def add_bookmark(
    bookmark: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == bookmark.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.story_id == bookmark.story_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Story already bookmarked")
    
    db_bookmark = Bookmark(
        user_id=current_user.id,
        story_id=bookmark.story_id
    )
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    
    return BookmarkResponse(
        id=db_bookmark.id,
        user_id=db_bookmark.user_id,
        story_id=db_bookmark.story_id,
        created_at=db_bookmark.created_at,
        is_read=db_bookmark.is_read,
        story_title=story.title,
        story_excerpt=story.excerpt,
        story_author=story.author.username if story.author else "Unknown",
        story_cover=story.cover_image
    )

@router.delete("/{story_id}")
def remove_bookmark(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.story_id == story_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "Bookmark removed successfully"}

@router.get("/", response_model=BookmarkListResponse)
def get_bookmarks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    read_status: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)
    
    if read_status is not None:
        query = query.filter(Bookmark.is_read == read_status)
    
    query = query.order_by(desc(Bookmark.created_at))
    
    total = query.count()
    pages = (total + per_page - 1) // per_page
    bookmarks = query.offset((page - 1) * per_page).limit(per_page).all()
    
    bookmark_responses = []
    for bookmark in bookmarks:
        story = bookmark.story
        bookmark_responses.append(BookmarkResponse(
            id=bookmark.id,
            user_id=bookmark.user_id,
            story_id=bookmark.story_id,
            created_at=bookmark.created_at,
            is_read=bookmark.is_read,
            story_title=story.title,
            story_excerpt=story.excerpt,
            story_author=story.author.username if story.author else "Unknown",
            story_cover=story.cover_image
        ))
    
    return BookmarkListResponse(
        bookmarks=bookmark_responses,
        total=total,
        page=page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )

@router.put("/{story_id}/read")
def mark_as_read(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.story_id == story_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    bookmark.is_read = True
    db.commit()
    
    return {"message": "Bookmark marked as read"}

@router.get("/check/{story_id}")
def check_bookmark(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.story_id == story_id
    ).first()
    
    return {
        "is_bookmarked": bookmark is not None,
        "is_read": bookmark.is_read if bookmark else False
    }
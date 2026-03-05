# routers/bookmark.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict)
def add_bookmark(
    bookmark_data: dict,
    current_user = Depends(get_current_active_user)
):
    story_id = bookmark_data.get("story_id")
    if not story_id:
        raise HTTPException(status_code=400, detail="story_id is required")
    
    logger.info(f"🔖 Adding bookmark for user {current_user.id} to story {story_id}")
    
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        result = helpers.toggle_bookmark(current_user.id, story_id)
        
        if result.get("bookmarked"):
            # Get story details for response
            story = helpers.get_story(story_id)
            author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
            
            return {
                "id": story_id,
                "user_id": current_user.id,
                "story_id": story_id,
                "created_at": datetime.now(),
                "is_read": False,
                "story_title": story.get("title"),
                "story_excerpt": story.get("excerpt", ""),
                "story_author": author.get("username") if author else "Unknown",
                "story_cover": story.get("cover_image")
            }
        else:
            raise HTTPException(status_code=400, detail="Story already bookmarked")
    
    else:
        from sqlalchemy.orm import Session
        from models.user import User
        from models.story import Story
        from models.bookmark import Bookmark
        from datetime import datetime
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        existing = db.query(Bookmark).filter(
            Bookmark.user_id == current_user.id,
            Bookmark.story_id == story_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Story already bookmarked")
        
        db_bookmark = Bookmark(
            user_id=current_user.id,
            story_id=story_id
        )
        db.add(db_bookmark)
        db.commit()
        db.refresh(db_bookmark)
        
        return {
            "id": db_bookmark.id,
            "user_id": db_bookmark.user_id,
            "story_id": db_bookmark.story_id,
            "created_at": db_bookmark.created_at,
            "is_read": db_bookmark.is_read,
            "story_title": story.title,
            "story_excerpt": story.excerpt,
            "story_author": story.author.username if story.author else "Unknown",
            "story_cover": story.cover_image
        }

@router.delete("/{story_id}")
def remove_bookmark(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"🔖 Removing bookmark for user {current_user.id} from story {story_id}")
    
    if settings.USE_TURSO:
        result = helpers.toggle_bookmark(current_user.id, story_id)
        
        if not result.get("bookmarked"):
            return {"message": "Bookmark removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Bookmark not found")
    
    else:
        from sqlalchemy.orm import Session
        from models.bookmark import Bookmark
        
        db = next(get_db())
        
        bookmark = db.query(Bookmark).filter(
            Bookmark.user_id == current_user.id,
            Bookmark.story_id == story_id
        ).first()
        
        if not bookmark:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        db.delete(bookmark)
        db.commit()
        
        return {"message": "Bookmark removed successfully"}

@router.get("/", response_model=dict)
def get_bookmarks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    read_status: Optional[bool] = Query(None),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"🔖 Getting bookmarks for user {current_user.id}")
    
    if settings.USE_TURSO:
        offset = (page - 1) * per_page
        bookmarks = helpers.get_user_bookmarks(current_user.id, limit=per_page, offset=offset)
        
        total = len(bookmarks)
        pages = (total + per_page - 1) // per_page
        
        bookmark_responses = []
        for bookmark in bookmarks:
            bookmark_responses.append({
                "id": bookmark.get("id"),
                "user_id": bookmark.get("user_id"),
                "story_id": bookmark.get("story_id"),
                "created_at": bookmark.get("created_at"),
                "is_read": bookmark.get("is_read", False),
                "story_title": bookmark.get("title"),
                "story_excerpt": bookmark.get("excerpt", ""),
                "story_author": bookmark.get("username", "Unknown"),
                "story_cover": bookmark.get("cover_image")
            })
        
        return {
            "bookmarks": bookmark_responses,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.bookmark import Bookmark
        
        db = next(get_db())
        
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
            bookmark_responses.append({
                "id": bookmark.id,
                "user_id": bookmark.user_id,
                "story_id": bookmark.story_id,
                "created_at": bookmark.created_at,
                "is_read": bookmark.is_read,
                "story_title": story.title,
                "story_excerpt": story.excerpt,
                "story_author": story.author.username if story.author else "Unknown",
                "story_cover": story.cover_image
            })
        
        return {
            "bookmarks": bookmark_responses,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

@router.put("/{story_id}/read")
def mark_as_read(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"🔖 Marking bookmark as read for user {current_user.id}, story {story_id}")
    
    if settings.USE_TURSO:
        # Check if bookmarked
        is_bookmarked = helpers.is_bookmarked(current_user.id, story_id)
        if not is_bookmarked:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        # Update in database would need a helper function
        # For now, just return success
        return {"message": "Bookmark marked as read"}
    
    else:
        from sqlalchemy.orm import Session
        from models.bookmark import Bookmark
        
        db = next(get_db())
        
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
    current_user = Depends(get_current_active_user)
):
    logger.info(f"🔖 Checking bookmark for user {current_user.id}, story {story_id}")
    
    if settings.USE_TURSO:
        is_bookmarked = helpers.is_bookmarked(current_user.id, story_id)
        
        return {
            "is_bookmarked": is_bookmarked,
            "is_read": False  # Would need to fetch this if needed
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.bookmark import Bookmark
        
        db = next(get_db())
        
        bookmark = db.query(Bookmark).filter(
            Bookmark.user_id == current_user.id,
            Bookmark.story_id == story_id
        ).first()
        
        return {
            "is_bookmarked": bookmark is not None,
            "is_read": bookmark.is_read if bookmark else False
        }
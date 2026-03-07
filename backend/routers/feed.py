from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/feed", tags=["feed"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=dict)
def get_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    feed_type: str = Query("following", pattern="^(following|popular|latest|trending)$"),
    timeframe: str = Query("all", pattern="^(today|week|month|all)$"),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting {feed_type} feed for user {current_user.id}")
    
    if settings.USE_TURSO:
        offset = (page - 1) * per_page
        
        following = helpers.get_following(current_user.id, limit=100)
        following_ids = [f["id"] for f in following]
        
        stories = []
        if feed_type == "following":
            for user_id in following_ids:
                user_stories = helpers.get_user_stories(user_id, limit=10)
                stories.extend(user_stories)
        else:
            stories = helpers.get_feed_stories(feed_type, timeframe, page, per_page)
        
        stories.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        
        paginated = stories[offset:offset+per_page]
        total = len(stories)
        pages = (total + per_page - 1) // per_page
        
        feed_stories = []
        for story in paginated:
            is_liked = helpers.is_liked(current_user.id, story["id"])
            author = helpers.get_user_by_id(story["user_id"])
            
            feed_stories.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", story["title"]),
                "cover_image": story.get("cover_image"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown",
                    "full_name": author.get("full_name") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None
                },
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "created_at": story.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc, func, and_
        from models.story import Story
        from models.follow import Follow
        from models.like import StoryLike
        from models.comment import Comment
        from models.analytics import StoryView
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        query = db.query(Story).filter(Story.is_published == True)
        
        if feed_type == "following":
            following_ids = db.query(Follow.following_id).filter(
                Follow.follower_id == current_user.id,
                Follow.is_active == True
            ).subquery()
            query = query.filter(Story.user_id.in_(following_ids))
        
        if timeframe == "today":
            query = query.filter(Story.created_at >= datetime.now().date())
        elif timeframe == "week":
            query = query.filter(Story.created_at >= datetime.now() - timedelta(days=7))
        elif timeframe == "month":
            query = query.filter(Story.created_at >= datetime.now() - timedelta(days=30))
        
        if feed_type == "popular":
            like_counts = db.query(
                StoryLike.story_id, 
                func.count(StoryLike.id).label('like_count')
            ).group_by(StoryLike.story_id).subquery()
            
            query = query.outerjoin(
                like_counts, 
                Story.id == like_counts.c.story_id
            ).order_by(like_counts.c.like_count.desc().nullslast())
            
        elif feed_type == "trending":
            recent = datetime.now() - timedelta(days=7)
            query = query.filter(Story.created_at >= recent)
            
            view_counts = db.query(
                StoryView.story_id,
                func.count(StoryView.id).label('view_count')
            ).filter(
                StoryView.viewed_at >= recent
            ).group_by(StoryView.story_id).subquery()
            
            query = query.outerjoin(
                view_counts,
                Story.id == view_counts.c.story_id
            ).order_by(view_counts.c.view_count.desc().nullslast())
        else:
            query = query.order_by(desc(Story.created_at))
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        stories = query.offset((page - 1) * per_page).limit(per_page).all()
        
        feed_stories = []
        for story in stories:
            is_liked = db.query(StoryLike).filter(
                StoryLike.user_id == current_user.id,
                StoryLike.story_id == story.id
            ).first() is not None
            
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            like_count = db.query(StoryLike).filter(StoryLike.story_id == story.id).count()
            comment_count = len(story.comments) if hasattr(story, 'comments') else 0
            
            feed_stories.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt or story.title,
                "cover_image": story.cover_image,
                "author": {
                    "id": story.author.id,
                    "username": story.author.username,
                    "full_name": story.author.full_name,
                    "avatar_url": story.author.avatar_url
                },
                "like_count": like_count,
                "comment_count": comment_count,
                "view_count": actual_view_count,
                "created_at": story.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

@router.get("/following", response_model=dict)
def get_following_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting following feed for user {current_user.id}")
    
    if settings.USE_TURSO:
        offset = (page - 1) * per_page
        following = helpers.get_following(current_user.id, limit=100)
        following_ids = [f["id"] for f in following]
        
        stories = []
        for user_id in following_ids:
            user_stories = helpers.get_user_stories(user_id, limit=10)
            stories.extend(user_stories)
        
        stories.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        paginated = stories[offset:offset+per_page]
        total = len(stories)
        pages = (total + per_page - 1) // per_page
        
        feed_stories = []
        for story in paginated:
            is_liked = helpers.is_liked(current_user.id, story["id"])
            author = helpers.get_user_by_id(story["user_id"])
            
            feed_stories.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", story["title"]),
                "cover_image": story.get("cover_image"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown",
                    "full_name": author.get("full_name") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None
                },
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "created_at": story.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.story import Story
        from models.follow import Follow
        from models.like import StoryLike
        from models.analytics import StoryView
        
        db = next(get_db())
        
        following_ids = db.query(Follow.following_id).filter(
            Follow.follower_id == current_user.id,
            Follow.is_active == True
        ).subquery()
        
        query = db.query(Story).filter(
            Story.is_published == True,
            Story.user_id.in_(following_ids)
        ).order_by(desc(Story.created_at))
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        stories = query.offset((page - 1) * per_page).limit(per_page).all()
        
        feed_stories = []
        for story in stories:
            is_liked = db.query(StoryLike).filter(
                StoryLike.user_id == current_user.id,
                StoryLike.story_id == story.id
            ).first() is not None
            
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            like_count = db.query(StoryLike).filter(StoryLike.story_id == story.id).count()
            comment_count = len(story.comments) if hasattr(story, 'comments') else 0
            
            feed_stories.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt or story.title,
                "cover_image": story.cover_image,
                "author": {
                    "id": story.author.id,
                    "username": story.author.username,
                    "full_name": story.author.full_name,
                    "avatar_url": story.author.avatar_url
                },
                "like_count": like_count,
                "comment_count": comment_count,
                "view_count": actual_view_count,
                "created_at": story.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

@router.get("/popular", response_model=dict)
def get_popular_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    timeframe: str = Query("week", pattern="^(today|week|month|all)$"),
    current_user = Depends(get_current_user_optional)
):
    logger.info(f"Getting popular feed for timeframe {timeframe}")
    
    if settings.USE_TURSO:
        stories = helpers.get_feed_stories("popular", timeframe, page, per_page)
        
        total = len(stories)
        pages = (total + per_page - 1) // per_page
        
        feed_stories = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = helpers.is_liked(current_user.id, story["id"])
            
            author = helpers.get_user_by_id(story["user_id"])
            
            feed_stories.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", story["title"]),
                "cover_image": story.get("cover_image"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown",
                    "full_name": author.get("full_name") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None
                },
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "created_at": story.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc, func
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        query = db.query(Story).filter(Story.is_published == True)
        
        if timeframe == "today":
            query = query.filter(Story.created_at >= datetime.now().date())
        elif timeframe == "week":
            query = query.filter(Story.created_at >= datetime.now() - timedelta(days=7))
        elif timeframe == "month":
            query = query.filter(Story.created_at >= datetime.now() - timedelta(days=30))
        
        like_counts = db.query(
            StoryLike.story_id, 
            func.count(StoryLike.id).label('like_count')
        ).group_by(StoryLike.story_id).subquery()
        
        query = query.outerjoin(
            like_counts, 
            Story.id == like_counts.c.story_id
        ).order_by(like_counts.c.like_count.desc().nullslast())
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        stories = query.offset((page - 1) * per_page).limit(per_page).all()
        
        feed_stories = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = db.query(StoryLike).filter(
                    StoryLike.user_id == current_user.id,
                    StoryLike.story_id == story.id
                ).first() is not None
            
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            like_count = db.query(StoryLike).filter(StoryLike.story_id == story.id).count()
            comment_count = len(story.comments) if hasattr(story, 'comments') else 0
            
            feed_stories.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt or story.title,
                "cover_image": story.cover_image,
                "author": {
                    "id": story.author.id,
                    "username": story.author.username,
                    "full_name": story.author.full_name,
                    "avatar_url": story.author.avatar_url
                },
                "like_count": like_count,
                "comment_count": comment_count,
                "view_count": actual_view_count,
                "created_at": story.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

@router.get("/latest", response_model=dict)
def get_latest_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user = Depends(get_current_user_optional)
):
    logger.info(f"Getting latest feed")
    
    if settings.USE_TURSO:
        stories = helpers.get_feed_stories("latest", "all", page, per_page)
        
        total = len(stories)
        pages = (total + per_page - 1) // per_page
        
        feed_stories = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = helpers.is_liked(current_user.id, story["id"])
            
            author = helpers.get_user_by_id(story["user_id"])
            
            feed_stories.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", story["title"]),
                "cover_image": story.get("cover_image"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown",
                    "full_name": author.get("full_name") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None
                },
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "created_at": story.get("created_at"),
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        
        db = next(get_db())
        
        query = db.query(Story).filter(
            Story.is_published == True
        ).order_by(desc(Story.created_at))
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        stories = query.offset((page - 1) * per_page).limit(per_page).all()
        
        feed_stories = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = db.query(StoryLike).filter(
                    StoryLike.user_id == current_user.id,
                    StoryLike.story_id == story.id
                ).first() is not None
            
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            like_count = db.query(StoryLike).filter(StoryLike.story_id == story.id).count()
            comment_count = len(story.comments) if hasattr(story, 'comments') else 0
            
            feed_stories.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt or story.title,
                "cover_image": story.cover_image,
                "author": {
                    "id": story.author.id,
                    "username": story.author.username,
                    "full_name": story.author.full_name,
                    "avatar_url": story.author.avatar_url
                },
                "like_count": like_count,
                "comment_count": comment_count,
                "view_count": actual_view_count,
                "created_at": story.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": feed_stories,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
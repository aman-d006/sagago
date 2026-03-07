import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Query, File, UploadFile, Form
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user, get_current_user_optional
from core.story_generator import StoryGenerator
from core.groq_client import GroqLLM
from core.analytics import AnalyticsService
from core.config import settings as app_settings
from core.upload import save_upload_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stories", tags=["stories"])

def get_session_id(session_id: Optional[str] = None):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/create", response_model=dict)
def create_story(
    request: dict,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_session_id),
    current_user = Depends(get_current_user_optional)
):
    theme = request.get("theme")
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    
    if settings.USE_TURSO:
        job_data = {
            "job_id": job_id,
            "theme": theme,
            "status": "pending"
        }
        helpers.create_job(job_data)
        
        background_tasks.add_task(
            generate_story_task,
            job_id=job_id,
            theme=theme,
            session_id=session_id,
            user_id=current_user.id if current_user else None
        )
        
        return {"job_id": job_id, "status": "pending"}
    
    else:
        from models.job import StoryJob
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        
        job = StoryJob(
            job_id=job_id,
            session_id=session_id,
            theme=theme,
            status="pending"
        )
        db.add(job)
        db.commit()
        
        background_tasks.add_task(
            generate_story_task,
            job_id=job_id,
            theme=theme,
            session_id=session_id,
            user_id=current_user.id if current_user else None
        )
        
        return job

@router.post("/publish/{story_id}")
def publish_story(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.get("user_id"):
            raise HTTPException(status_code=400, detail="Story already published")
        
        helpers.update_story(story_id, current_user.id, {
            "user_id": current_user.id,
            "is_published": True
        })
        
        return {"message": "Story published successfully", "story_id": story_id}
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.user_id:
            raise HTTPException(status_code=400, detail="Story already published")
        
        story.user_id = current_user.id
        story.is_published = True
        db.commit()
        
        return {"message": "Story published successfully", "story_id": story.id}

@router.get("/my-stories", response_model=List[dict])
def get_my_stories(
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        stories = helpers.get_user_stories(current_user.id, limit=100)
        
        result = []
        for story in stories:
            author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
            
            result.append({
                "id": story["id"],
                "title": story["title"],
                "content": story.get("content", ""),
                "created_at": story.get("created_at"),
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "story_type": story.get("story_type", "written"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown Author",
                    "full_name": author.get("full_name") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None
                } if author else None
            })
        
        return result
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        from models.story import StoryNode
        
        db = next(get_db())
        
        stories = db.query(Story).filter(Story.user_id == current_user.id).all()
        
        result = []
        for story in stories:
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            
            author_data = {
                "id": story.author.id if story.author else 0,
                "username": story.author.username if story.author else "Unknown Author",
                "full_name": story.author.full_name if story.author else None,
                "avatar_url": story.author.avatar_url if story.author else None
            }
            
            is_liked = db.query(StoryLike).filter(
                StoryLike.user_id == current_user.id,
                StoryLike.story_id == story.id
            ).first() is not None
            
            result.append({
                "id": story.id,
                "title": story.title,
                "content": story.content,
                "created_at": story.created_at,
                "like_count": len(story.likes),
                "comment_count": len(story.comments),
                "view_count": actual_view_count,
                "is_liked_by_current_user": is_liked,
                "story_type": story.story_type,
                "author": author_data
            })
        
        return result

@router.get("/metadata/{story_id}", response_model=dict)
def get_story_metadata(
    story_id: int
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        return {
            "id": story["id"],
            "title": story["title"],
            "story_type": story.get("story_type", "written"),
            "has_nodes": False
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story, StoryNode
        from db.database import get_db
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        return {
            "id": story.id,
            "title": story.title,
            "story_type": story.story_type,
            "has_nodes": db.query(StoryNode).filter(StoryNode.story_id == story_id).count() > 0
        }

@router.get("/explore", response_model=dict)
def get_explore_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    genre: Optional[str] = Query(None),
    sort: str = Query("latest", pattern="^(latest|popular|trending)$"),
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        offset = (page - 1) * limit
        stories = helpers.get_feed_stories(sort, "week" if sort == "trending" else "all", page, limit)
        
        total = len(stories)
        pages = (total + limit - 1) // limit if total > 0 else 1
        
        story_responses = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = helpers.is_liked(current_user.id, story["id"])
            
            author = helpers.get_user_by_id(story["user_id"])
            
            story_responses.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", ""),
                "cover_image": story.get("cover_image"),
                "genre": story.get("genre"),
                "author": {
                    "id": author["id"] if author else 0,
                    "username": author["username"] if author else "Unknown Author",
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
            "stories": story_responses,
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
        from models.user import User
        from models.like import StoryLike
        from models.analytics import StoryView
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        query = db.query(Story).filter(Story.is_published == True)
        
        if genre and genre != 'all':
            genre_map = {
                'fantasy': 'Fantasy',
                'sci-fi': 'Sci-Fi',
                'mystery': 'Mystery',
                'romance': 'Romance',
                'horror': 'Horror',
                'adventure': 'Adventure',
                'thriller': 'Thriller',
                'drama': 'Drama',
                'comedy': 'Comedy'
            }
            db_genre = genre_map.get(genre.lower(), genre.title())
            query = query.filter(Story.genre == db_genre)
        
        if sort == 'popular':
            like_counts = db.query(
                StoryLike.story_id, 
                func.count(StoryLike.id).label('like_count')
            ).group_by(StoryLike.story_id).subquery()
            query = query.outerjoin(
                like_counts, 
                Story.id == like_counts.c.story_id
            ).order_by(like_counts.c.like_count.desc().nullslast())
        elif sort == 'trending':
            recent = datetime.now() - timedelta(days=7)
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
        stories = query.offset((page - 1) * limit).limit(limit).all()
        pages = (total + limit - 1) // limit
        
        story_responses = []
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
            
            story_responses.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt,
                "cover_image": story.cover_image,
                "genre": getattr(story, 'genre', None),
                "author": {
                    "id": story.author.id if story.author else 0,
                    "username": story.author.username if story.author else "Unknown Author",
                    "full_name": story.author.full_name if story.author else None,
                    "avatar_url": story.author.avatar_url if story.author else None
                },
                "like_count": like_count,
                "comment_count": comment_count,
                "view_count": actual_view_count,
                "created_at": story.created_at,
                "is_liked_by_current_user": is_liked
            })
        
        return {
            "stories": story_responses,
            "total": total,
            "page": page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

@router.get("/user/{username}", response_model=List[dict])
def get_user_stories(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        user = helpers.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stories = helpers.get_user_stories(user["id"], limit=limit, offset=skip)
        
        result = []
        for story in stories:
            if not story.get("is_published"):
                continue
                
            is_liked = False
            if current_user:
                is_liked = helpers.is_liked(current_user.id, story["id"])
            
            result.append({
                "id": story["id"],
                "title": story["title"],
                "content": story.get("content", ""),
                "excerpt": story.get("excerpt", ""),
                "cover_image": story.get("cover_image"),
                "created_at": story.get("created_at"),
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "story_type": story.get("story_type", "written"),
                "is_liked_by_current_user": is_liked
            })
        
        return result
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.user import User
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        
        db = next(get_db())
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stories = db.query(Story).filter(
            Story.user_id == user.id,
            Story.is_published == True
        ).order_by(desc(Story.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for story in stories:
            actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
            is_liked = False
            if current_user:
                is_liked = db.query(StoryLike).filter(
                    StoryLike.user_id == current_user.id,
                    StoryLike.story_id == story.id
                ).first() is not None
            
            result.append({
                "id": story.id,
                "title": story.title,
                "content": story.content,
                "excerpt": story.excerpt,
                "cover_image": story.cover_image,
                "created_at": story.created_at,
                "like_count": len(story.likes),
                "comment_count": len(story.comments),
                "view_count": actual_view_count,
                "story_type": story.story_type,
                "is_liked_by_current_user": is_liked
            })
        
        return result

@router.post("/generate-full", response_model=dict)
def generate_full_story(
    request: dict,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
):
    theme = request.get("theme")
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    
    if settings.USE_TURSO:
        job_data = {
            "job_id": job_id,
            "theme": theme,
            "status": "pending"
        }
        helpers.create_job(job_data)
        
        background_tasks.add_task(
            generate_full_story_task,
            job_id=job_id,
            theme=theme,
            user_id=current_user.id if current_user else None
        )
        
        return {"job_id": job_id, "status": "pending"}
    
    else:
        from models.job import StoryJob
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        
        job = StoryJob(
            job_id=job_id,
            session_id=str(uuid.uuid4()),
            theme=theme,
            status="pending"
        )
        db.add(job)
        db.commit()
        
        background_tasks.add_task(
            generate_full_story_task,
            job_id=job_id,
            theme=theme,
            user_id=current_user.id if current_user else None
        )
        
        return job

@router.get("/{story_id}", response_model=dict)
def get_story_by_id(
    story_id: int,
    request: Request,
    session_id: str = Depends(get_session_id),
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(None, story_id, user_id, session_id)
        
        author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
        
        is_liked = False
        if current_user:
            is_liked = helpers.is_liked(current_user.id, story_id)
        
        return {
            "id": story["id"],
            "title": story["title"],
            "content": story.get("content", ""),
            "excerpt": story.get("excerpt", ""),
            "cover_image": story.get("cover_image"),
            "created_at": story.get("created_at"),
            "like_count": story.get("like_count", 0),
            "comment_count": story.get("comment_count", 0),
            "view_count": story.get("view_count", 0),
            "story_type": story.get("story_type", "written"),
            "is_liked_by_current_user": is_liked,
            "author": {
                "id": author["id"] if author else 0,
                "username": author["username"] if author else "Unknown Author",
                "full_name": author.get("full_name") if author else None,
                "avatar_url": author.get("avatar_url") if author else None
            } if author else None
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        from db.database import get_db
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(db, story_id, user_id, session_id)
        
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
        
        author_data = {
            "id": story.author.id if story.author else 0,
            "username": story.author.username if story.author else "Unknown Author",
            "full_name": story.author.full_name if story.author else None,
            "avatar_url": story.author.avatar_url if story.author else None
        }
        
        is_liked = False
        if current_user:
            is_liked = db.query(StoryLike).filter(
                StoryLike.user_id == current_user.id,
                StoryLike.story_id == story.id
            ).first() is not None
        
        return {
            "id": story.id,
            "title": story.title,
            "content": story.content,
            "excerpt": story.excerpt,
            "cover_image": story.cover_image,
            "created_at": story.created_at,
            "like_count": len(story.likes),
            "comment_count": len(story.comments),
            "view_count": actual_view_count,
            "story_type": story.story_type,
            "is_liked_by_current_user": is_liked,
            "author": author_data
        }

@router.get("/{story_id}/stats")
def get_story_stats(
    story_id: int
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        return {
            "story_id": story["id"],
            "title": story["title"],
            "views": story.get("view_count", 0),
            "likes": story.get("like_count", 0),
            "comments": story.get("comment_count", 0),
            "published": story.get("is_published", False),
            "created_at": story.get("created_at")
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.analytics import StoryView
        from db.database import get_db
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
        
        return {
            "story_id": story.id,
            "title": story.title,
            "views": actual_view_count,
            "likes": len(story.likes),
            "comments": len(story.comments),
            "published": story.is_published,
            "created_at": story.created_at
        }

@router.put("/{story_id}", response_model=dict)
def update_story(
    story_id: int,
    story_data: dict,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this story")
        
        update_data = {}
        for field in ["title", "content", "excerpt", "cover_image"]:
            if field in story_data:
                update_data[field] = story_data[field]
        
        if update_data:
            helpers.update_story(story_id, current_user.id, update_data)
        
        updated_story = helpers.get_story(story_id)
        
        author = helpers.get_user_by_id(updated_story["user_id"])
        is_liked = helpers.is_liked(current_user.id, story_id)
        
        return {
            "id": updated_story["id"],
            "title": updated_story["title"],
            "content": updated_story.get("content", ""),
            "created_at": updated_story.get("created_at"),
            "like_count": updated_story.get("like_count", 0),
            "comment_count": updated_story.get("comment_count", 0),
            "view_count": updated_story.get("view_count", 0),
            "is_liked_by_current_user": is_liked,
            "author": {
                "id": author["id"] if author else 0,
                "username": author["username"] if author else "Unknown Author"
            }
        }
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from models.like import StoryLike
        from models.analytics import StoryView
        from db.database import get_db
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this story")
        
        if "title" in story_data:
            story.title = story_data["title"]
        if "content" in story_data:
            story.content = story_data["content"]
        if "excerpt" in story_data:
            story.excerpt = story_data["excerpt"]
        if "cover_image" in story_data:
            story.cover_image = story_data["cover_image"]
        
        db.commit()
        db.refresh(story)
        
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
        is_liked = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story.id
        ).first() is not None
        
        author_data = {
            "id": story.author.id if story.author else 0,
            "username": story.author.username if story.author else "Unknown Author"
        }
        
        return {
            "id": story.id,
            "title": story.title,
            "content": story.content,
            "created_at": story.created_at,
            "like_count": len(story.likes),
            "comment_count": len(story.comments),
            "view_count": actual_view_count,
            "is_liked_by_current_user": is_liked,
            "author": author_data
        }

@router.delete("/{story_id}")
def delete_story(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this story")
        
        helpers.delete_story(story_id, current_user.id)
        
        return {"message": "Story deleted successfully"}
    
    else:
        from sqlalchemy.orm import Session
        from models.story import Story
        from db.database import get_db
        
        db = next(get_db())
        
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this story")
        
        db.delete(story)
        db.commit()
        
        return {"message": "Story deleted successfully"}

@router.post("/upload-image")
async def upload_story_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    try:
        file_url = await save_upload_file(file, "stories")
        return {"url": file_url, "message": "Image uploaded successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def generate_story_task(job_id: str, theme: str, session_id: str, user_id: Optional[int] = None):
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            story_data = {
                "title": f"Story about {theme}",
                "content": f"Generated content about {theme}",
                "user_id": user_id,
                "is_published": True if user_id else False
            }
            
            story = helpers.create_story(story_data, user_id) if user_id else None
            
            helpers.update_job_status(job_id, "completed", f"Story ID: {story['id'] if story else 'unknown'}")
            
        except Exception as e:
            helpers.update_job_status(job_id, "failed", str(e))
    
    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        from models.story import Story
        from db.database import SessionLocal
        from core.story_generator import StoryGenerator
        
        db = SessionLocal()
        try:
            job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
            if not job:
                return
            
            job.status = "processing"
            db.commit()
            
            story = StoryGenerator.generate_story(db, session_id, theme)
            
            if user_id:
                story.user_id = user_id
                story.is_published = True
                db.commit()
            
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as e:
            if job:
                job.status = "failed"
                job.completed_at = datetime.now()
                job.error = str(e)
                db.commit()
        finally:
            db.close()

def generate_full_story_task(job_id: str, theme: str, user_id: Optional[int] = None):
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            from core.prompts import FULL_STORY_PROMPT
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", FULL_STORY_PROMPT),
                ("human", "Theme: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else response
            
            story_data = {
                "title": f"The {theme.title()} Story",
                "content": story_text,
                "excerpt": story_text[:150] + "...",
                "user_id": user_id,
                "is_published": True,
                "story_type": "written"
            }
            
            story = helpers.create_story(story_data, user_id) if user_id else None
            
            helpers.update_job_status(job_id, "completed", f"Story ID: {story['id'] if story else 'unknown'}")
            
        except Exception as e:
            helpers.update_job_status(job_id, "failed", str(e))
    
    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        from models.story import Story
        from db.database import SessionLocal
        from core.groq_client import GroqLLM
        from core.prompts import FULL_STORY_PROMPT
        from langchain_core.prompts import ChatPromptTemplate
        import uuid
        
        db = SessionLocal()
        try:
            job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
            if not job:
                return
            
            job.status = "processing"
            db.commit()
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", FULL_STORY_PROMPT),
                ("human", "Theme: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else response
            
            story = Story(
                title=f"The {theme.title()} Story",
                content=story_text,
                excerpt=story_text[:150] + "...",
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                is_published=True,
                story_type="written"
            )
            db.add(story)
            db.flush()
            
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
            
        except Exception as e:
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

@router.post("/generate-assisted", response_model=dict)
def generate_assisted_story(
    request: dict,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
):
    theme = request.get("theme")
    cover_image = request.get("cover_image")
    
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    
    if settings.USE_TURSO:
        job_data = {
            "job_id": job_id,
            "theme": theme,
            "status": "pending"
        }
        helpers.create_job(job_data)
        
        background_tasks.add_task(
            generate_assisted_story_task,
            job_id=job_id,
            theme=theme,
            cover_image=cover_image,
            user_id=current_user.id if current_user else None
        )
        
        return {"job_id": job_id, "status": "pending"}
    
    else:
        from models.job import StoryJob
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        
        job = StoryJob(
            job_id=job_id,
            session_id=str(uuid.uuid4()),
            theme=theme,
            status="pending"
        )
        db.add(job)
        db.commit()
        
        background_tasks.add_task(
            generate_assisted_story_task,
            job_id=job_id,
            theme=theme,
            cover_image=cover_image,
            user_id=current_user.id if current_user else None
        )
        
        return job

def generate_assisted_story_task(job_id: str, theme: str, cover_image: Optional[str] = None, user_id: Optional[int] = None):
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            from core.prompts import ASSISTED_STORY_PROMPT
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", ASSISTED_STORY_PROMPT),
                ("human", "Story prompt: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else response
            story_text = story_text.strip()
            
            lines = story_text.split('\n')
            title = lines[0].strip() if lines else f"Story about {theme}"
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else story_text
            if not content:
                content = story_text
            
            excerpt = content[:150] + "..." if len(content) > 150 else content
            
            story_data = {
                "title": title,
                "content": content,
                "excerpt": excerpt,
                "cover_image": cover_image,
                "user_id": user_id,
                "is_published": True,
                "story_type": "written"
            }
            
            story = helpers.create_story(story_data, user_id) if user_id else None
            
            helpers.update_job_status(job_id, "completed", f"Story ID: {story['id'] if story else 'unknown'}")
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            helpers.update_job_status(job_id, "failed", str(e))
    
    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        from models.story import Story
        from db.database import SessionLocal
        from core.groq_client import GroqLLM
        from core.prompts import ASSISTED_STORY_PROMPT
        from langchain_core.prompts import ChatPromptTemplate
        import uuid
        
        db = SessionLocal()
        try:
            job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
            if not job:
                return
            
            job.status = "processing"
            db.commit()
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", ASSISTED_STORY_PROMPT),
                ("human", "Story prompt: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else response
            story_text = story_text.strip()
            
            lines = story_text.split('\n')
            title = lines[0].strip() if lines else f"Story about {theme}"
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else story_text
            if not content:
                content = story_text
            
            excerpt = content[:150] + "..." if len(content) > 150 else content
            
            story = Story(
                title=title,
                content=content,
                excerpt=excerpt,
                cover_image=cover_image,
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                is_published=True,
                story_type="written"
            )
            db.add(story)
            db.flush()
            
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
            
        except Exception as e:
            logger.error(f"Error in story generation: {e}")
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

@router.get("/debug/uploads")
def debug_uploads():
    import os
    from core.config import settings as app_settings
    
    upload_dir = os.path.join(app_settings.UPLOAD_DIR, "stories")
    files = []
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
    
    return {
        "upload_dir": upload_dir,
        "exists": os.path.exists(upload_dir),
        "files": files,
        "absolute_path": os.path.abspath(upload_dir)
    }
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging

from db.database import get_db, settings
from db import helpers
from core.story_generator import StoryGenerator
from core.auth import get_current_user_optional

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict)
def create_job(
    job_data: dict,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
):
    theme = job_data.get("theme")
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    logger.info(f"Creating job {job_id} with theme: {theme}")
    
    if settings.USE_TURSO:
        job = {
            "job_id": job_id,
            "session_id": session_id,
            "theme": theme,
            "status": "pending"
        }
        
        helpers.create_job(job)
        
        background_tasks.add_task(
            process_story_job,
            job_id=job_id,
            theme=theme,
            session_id=session_id,
            user_id=current_user.id if current_user else None
        )
        
        return {"job_id": job_id, "status": "pending"}
    
    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        
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
            process_story_job,
            job_id=job_id,
            theme=theme,
            session_id=session_id,
            user_id=current_user.id if current_user else None
        )
        
        return {"job_id": job_id, "status": "pending"}

@router.get("/{job_id}", response_model=dict)
def get_job_status(
    job_id: str
):
    logger.info(f"Getting status for job {job_id}")
    
    if settings.USE_TURSO:
        try:
            job = helpers.get_job(job_id)
            if not job:
                # Return a default response instead of 404 to prevent frontend errors
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "message": "Job not found or expired"
                }
            return job
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "error",
                "message": str(e)
            }

    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        
        db = next(get_db())
        
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "story_id": job.story_id,
            "error": job.error,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }

def process_story_job(job_id: str, theme: str, session_id: str, user_id: Optional[int] = None):
    logger.info(f"Processing job {job_id}")
    
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            story_data = {
                "title": f"Story about {theme}",
                "content": f"This is a generated story about {theme}.",
                "excerpt": f"A story about {theme}",
                "user_id": user_id,
                "is_published": True if user_id else False,
                "story_type": "written"
            }
            
            if user_id:
                story = helpers.create_story(story_data, user_id)
                story_id = story["id"] if story else None
            else:
                story_id = None
            
            result = f"Story ID: {story_id}" if story_id else "Story generated"
            helpers.update_job_status(job_id, "completed", result)
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
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
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

def get_current_user_optional():
    from core.auth import get_current_user_optional as auth_get_current_user
    return auth_get_current_user()
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.job import StoryJob
from schemas.job import StoryJobResponse, StoryJobCreate
from core.story_generator import StoryGenerator 

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/", response_model=StoryJobResponse)
def create_job(
    job_data: StoryJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    
    job = StoryJob(
        job_id=job_id,
        session_id="temp_session", 
        theme=job_data.theme,
        status="pending"
    )
    db.add(job)
    db.commit()
    

    background_tasks.add_task(
        process_story_job,
        job_id=job_id,
        theme=job_data.theme
    )
    
    return job

@router.get("/{job_id}", response_model=StoryJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def process_story_job(job_id: str, theme: str):
    db = SessionLocal()
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()
        

        story = StoryGenerator.generate_story(db, job.session_id, theme)
        
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
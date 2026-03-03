import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Cookie, Response, BackgroundTasks, Request, Query
from sqlalchemy import desc, func, inspect
from sqlalchemy.orm import Session, joinedload
import logging

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode
from models.job import StoryJob
from models.user import User
from models.like import StoryLike
from models.analytics import StoryView
from schemas.story import (
    CompleteStoryNodeResponse,
    CompleteStoryResponse,
    CreatyStoryRequest,
    FullStoryResponse
)
from schemas.job import StoryJobResponse
from schemas.feed import FeedResponse
from core.story_generator import StoryGenerator
from core.groq_client import GroqLLM
from core.auth import get_current_active_user, get_current_user_optional
from core.analytics import AnalyticsService
from core.config import settings
from core.upload import save_upload_file, delete_upload_file
from fastapi import File, UploadFile, Form

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stories",
    tags=["stories"]
)

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/create", response_model=StoryJobResponse)
def create_story(
    request: CreatyStoryRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    job_id = str(uuid.uuid4())

    job = StoryJob(
        job_id=job_id,
        session_id=session_id,
        theme=request.theme,
        status="pending"
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_story_task, 
        job_id=job_id, 
        theme=request.theme, 
        session_id=session_id,
        user_id=current_user.id if current_user else None
        )
    
    return job

@router.post("/publish/{story_id}")
def publish_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if story.user_id:
        raise HTTPException(status_code=400, detail="Story already published")
    
    story.user_id = current_user.id
    story.is_published = True
    db.commit()
    
    return {"message": "Story published successfully", "story_id": story.id}

@router.get("/my-stories", response_model=List[CompleteStoryResponse])
def get_my_stories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    stories = db.query(Story).filter(Story.user_id == current_user.id).all()
    
    result = []
    for story in stories:
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
        
        if story.story_type == "interactive":
            try:
                complete_story = build_complete_story_tree(db, story, current_user)
                complete_story.view_count = actual_view_count
                result.append(complete_story)
            except HTTPException:
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
                
                result.append(CompleteStoryResponse(
                    id=story.id,
                    title=story.title,
                    content=story.content,
                    session_id=story.session_id,
                    created_at=story.created_at,
                    root_node=None,
                    all_nodes={},
                    like_count=len(story.likes),
                    comment_count=len(story.comments),
                    view_count=actual_view_count,
                    is_liked_by_current_user=is_liked,
                    author=author_data
                ))
        else:
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
            
            result.append(CompleteStoryResponse(
                id=story.id,
                title=story.title,
                content=story.content,
                session_id=story.session_id,
                created_at=story.created_at,
                root_node=None,
                all_nodes={},
                like_count=len(story.likes),
                comment_count=len(story.comments),
                view_count=actual_view_count,
                is_liked_by_current_user=is_liked,
                author=author_data
            ))
    
    return result

@router.get("/metadata/{story_id}", response_model=dict)
def get_story_metadata(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return {
        "id": story.id,
        "title": story.title,
        "story_type": story.story_type,
        "has_nodes": db.query(StoryNode).filter(StoryNode.story_id == story_id).count() > 0
    }

@router.get("/explore", response_model=FeedResponse)
def get_explore_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    genre: Optional[str] = Query(None),
    sort: str = Query("latest", pattern="^(latest|popular|trending)$"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
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
            "is_liked_by_current_user": is_liked,
            "is_boosted_by_current_user": False
        })
    
    return {
        "stories": story_responses,
        "total": total,
        "page": page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }

@router.get("/user/{username}", response_model=List[CompleteStoryResponse])
def get_user_stories(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
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
        
        if story.story_type == "interactive":
            try:
                complete_story = build_complete_story_tree(db, story, current_user)
                complete_story.view_count = actual_view_count
                result.append(complete_story)
            except HTTPException:
                logger.warning(f"Story {story.id} has no nodes, creating basic response")
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
                
                result.append(CompleteStoryResponse(
                    id=story.id,
                    title=story.title,
                    content=story.content,
                    session_id=story.session_id,
                    created_at=story.created_at,
                    root_node=None,
                    all_nodes={},
                    like_count=len(story.likes),
                    comment_count=len(story.comments),
                    view_count=actual_view_count,
                    is_liked_by_current_user=is_liked,
                    author=author_data
                ))
        else:
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
            
            result.append(CompleteStoryResponse(
                id=story.id,
                title=story.title,
                content=story.content,
                session_id=story.session_id,
                created_at=story.created_at,
                root_node=None,
                all_nodes={},
                like_count=len(story.likes),
                comment_count=len(story.comments),
                view_count=actual_view_count,
                is_liked_by_current_user=is_liked,
                author=author_data
            ))
    
    return result

@router.post("/generate-full", response_model=StoryJobResponse)
def generate_full_story(
    request: CreatyStoryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    job_id = str(uuid.uuid4())
    
    job = StoryJob(
        job_id=job_id,
        session_id=str(uuid.uuid4()),
        theme=request.theme,
        status="pending"
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        generate_full_story_task, 
        job_id=job_id, 
        theme=request.theme,
        user_id=current_user.id if current_user else None
    )
    
    return job

@router.get("/{story_id}", response_model=CompleteStoryResponse)
def get_story_by_id(
    story_id: int,
    request: Request,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:     
        raise HTTPException(status_code=404, detail="Story not found")
    
    user_id = current_user.id if current_user else None
    
    AnalyticsService.track_story_view(db, story_id, user_id, session_id)
    
    actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
    
    if story.story_type == "interactive":
        try:
            complete_story = build_complete_story_tree(db, story, current_user)
            complete_story.view_count = actual_view_count
            return complete_story
        except HTTPException:
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
            
            return CompleteStoryResponse(
                id=story.id,
                title=story.title,
                content=story.content,
                session_id=story.session_id,
                created_at=story.created_at,
                root_node=None,
                all_nodes={},
                like_count=len(story.likes),
                comment_count=len(story.comments),
                view_count=actual_view_count,
                is_liked_by_current_user=is_liked,
                author=author_data
            )
    else:
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
        
        return CompleteStoryResponse(
            id=story.id,
            title=story.title,
            content=story.content,
            session_id=story.session_id,
            created_at=story.created_at,
            root_node=None,
            all_nodes={},
            like_count=len(story.likes),
            comment_count=len(story.comments),
            view_count=actual_view_count,
            is_liked_by_current_user=is_liked,
            author=author_data
        )

@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(
    story_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:     
        raise HTTPException(status_code=404, detail="Story not found")
    
    user_id = current_user.id if current_user else None
    
    AnalyticsService.track_story_view(db, story_id, user_id, session_id)
    
    actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
    
    complete_story = build_complete_story_tree(db, story, current_user)
    complete_story.view_count = actual_view_count
    
    return complete_story

@router.get("/{story_id}/full", response_model=FullStoryResponse)
def get_full_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    user_id = current_user.id if current_user else None
    
    AnalyticsService.track_story_view(db, story_id, user_id, None)
    
    actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
    
    is_liked = False
    if current_user:
        is_liked = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story.id
        ).first() is not None
    
    author_data = {
        "id": story.author.id if story.author else 0,
        "username": story.author.username if story.author else "Unknown Author",
        "full_name": story.author.full_name if story.author else None,
        "avatar_url": story.author.avatar_url if story.author else None
    }
    
    return FullStoryResponse(
        id=story.id,
        title=story.title,
        content=story.content or "",
        excerpt=story.excerpt or "",
        cover_image=story.cover_image,
        author=author_data,
        like_count=len(story.likes),
        comment_count=len(story.comments),
        view_count=actual_view_count,
        created_at=story.created_at,
        is_liked_by_current_user=is_liked
    )

@router.get("/{story_id}/stats")
def get_story_stats(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
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

def generate_story_task(job_id: str, theme: str, session_id: str, user_id: Optional[int] = None):
    db = SessionLocal()

    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            return

        try: 
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
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()

def build_complete_story_tree(db: Session, story: Story, current_user: Optional[User] = None) -> CompleteStoryResponse:
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()
    node_dict = {}
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=node.options
        )
        node_dict[node.id] = node_response

    root_node = next((node for node in nodes if node.is_root), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Root node not found for the story")
    
    is_liked = False
    if current_user:
        is_liked = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story.id
        ).first() is not None
    
    author_data = {
        "id": story.author.id if story.author else 0,
        "username": story.author.username if story.author else "Unknown Author",
        "full_name": story.author.full_name if story.author else None,
        "avatar_url": story.author.avatar_url if story.author else None
    }
    
    actual_view_count = db.query(StoryView).filter(StoryView.story_id == story.id).count()
    
    return CompleteStoryResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict,
        like_count=len(story.likes),
        comment_count=len(story.comments),
        view_count=actual_view_count,
        is_liked_by_current_user=is_liked,
        author=author_data
    )

def generate_full_story_task(job_id: str, theme: str, user_id: Optional[int] = None):
    db = SessionLocal()
    
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()
        
        from core.prompts import FULL_STORY_PROMPT
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = GroqLLM(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
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


@router.post("/generate-assisted", response_model=StoryJobResponse)
def generate_assisted_story(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Generate a full paragraph-style story based on user prompt"""
    theme = request.get("theme")
    cover_image = request.get("cover_image")
    
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    
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
    db = SessionLocal()
    
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()
        
        from core.prompts import ASSISTED_STORY_PROMPT
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = GroqLLM(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
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

        print(f"📝 Creating story with cover_image: {cover_image}")  # Add this log

        story = Story(
            title=title,
            content=content,
            excerpt=excerpt,
            cover_image=cover_image,  # Make sure this is included
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            is_published=True,
            story_type="written"
        )
        db.add(story)
        db.flush()
        
        print(f"✅ Story created with ID: {story.id}, cover_image: {story.cover_image}")  # Add this log
        
        job.story_id = story.id
        job.status = "completed"
        job.completed_at = datetime.now()
        db.commit()
        
    except Exception as e:
        print(f"❌ Error in story generation: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()
            db.commit()
    finally:
        db.close()

@router.get("/debug/genres")
def debug_genres(db: Session = Depends(get_db)):
    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('stories')]
        
        result = {
            "has_genre_column": 'genre' in columns,
            "columns": columns,
            "total_stories": db.query(Story).count(),
            "published_stories": db.query(Story).filter(Story.is_published == True).count(),
        }
        
        if 'genre' in columns:
            stories_with_genre = db.query(Story).filter(Story.genre.isnot(None)).count()
            unique_genres = db.query(Story.genre).filter(
                Story.genre.isnot(None)
            ).distinct().all()
            
            result["stories_with_genre"] = stories_with_genre
            result["unique_genres"] = [g[0] for g in unique_genres if g[0]]
            
            sample_stories = db.query(Story).filter(
                Story.genre.isnot(None)
            ).limit(5).all()
            
            result["sample_stories"] = [
                {
                    "id": s.id,
                    "title": s.title,
                    "genre": s.genre
                } for s in sample_stories
            ]
        
        return result
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/debug/schema")
def debug_schema(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        
        columns = inspector.get_columns('stories')
        
        result = {
            "table_exists": 'stories' in [t for t in inspector.get_table_names()],
            "columns": [
                {
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col['nullable']
                } for col in columns
            ]
        }
        
        has_genre = any(col['name'] == 'genre' for col in columns)
        result["has_genre_column"] = has_genre
        
        if has_genre:
            stories = db.query(Story).filter(Story.is_published == True).limit(5).all()
            result["sample_stories"] = [
                {
                    "id": s.id,
                    "title": s.title,
                    "genre": getattr(s, 'genre', None)
                } for s in stories
            ]
        
        return result
    except Exception as e:
        return {"error": str(e)}
    
@router.put("/{story_id}", response_model=CompleteStoryResponse)
def update_story(
    story_id: int,
    story_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    is_liked = False
    if current_user:
        is_liked = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story.id
        ).first() is not None
    
    author_data = {
        "id": story.author.id if story.author else 0,
        "username": story.author.username if story.author else "Unknown Author",
        "full_name": story.author.full_name if story.author else None,
        "avatar_url": story.author.avatar_url if story.author else None
    }
    
    return CompleteStoryResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=None,
        all_nodes={},
        like_count=len(story.likes),
        comment_count=len(story.comments),
        view_count=actual_view_count,
        is_liked_by_current_user=is_liked,
        author=author_data
    )

@router.delete("/{story_id}")
def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this story")
    
    db.delete(story)
    db.commit()
    
    return {"message": "Story deleted successfully"}

@router.post("/{story_id}/publish-interactive")
def publish_interactive_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if story.user_id:
        raise HTTPException(status_code=400, detail="Story already published")
    
    story.user_id = current_user.id
    story.is_published = True
    db.commit()
    
    return {"message": "Interactive story published successfully", "story_id": story.id}
  
@router.post("/upload-image")
async def upload_story_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload an image for story thumbnail"""
    try:
        file_url = await save_upload_file(file, "stories")
        return {"url": file_url, "message": "Image uploaded successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    

@router.get("/debug/uploads")
def debug_uploads(db: Session = Depends(get_db)):
    """Debug endpoint to check uploads directory"""
    import os
    from core.config import settings
    
    upload_dir = os.path.join(settings.UPLOAD_DIR, "stories")
    files = []
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
    
    return {
        "upload_dir": upload_dir,
        "exists": os.path.exists(upload_dir),
        "files": files,
        "absolute_path": os.path.abspath(upload_dir)
    }
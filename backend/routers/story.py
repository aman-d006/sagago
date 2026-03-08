import os
import uuid
import json
import re
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Query, File, UploadFile, Form, Cookie, Response
import logging

from db.database import get_db, settings, get_turso_client
from db import helpers
from core.auth import get_current_active_user, get_current_user_optional
from core.story_generator import StoryGenerator
from core.groq_client import GroqLLM
from core.analytics import AnalyticsService
from core.config import settings as app_settings
from core.upload import save_upload_file
from core.prompts import INTERACTIVE_STORY_PROMPT, FULL_STORY_PROMPT, ASSISTED_STORY_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stories", tags=["stories"])

def get_value(cell):
    if cell is None:
        return None
    if isinstance(cell, dict):
        return cell.get('value')
    return cell

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

def build_complete_story_tree(story_id: int, current_user=None) -> Optional[dict]:
    if settings.USE_TURSO:
        try:
            story = helpers.get_story(story_id)
            if not story:
                logger.error(f"Story {story_id} not found")
                return None
            
            with get_turso_client() as client:
                nodes = client.query(
                    f"SELECT * FROM story_nodes WHERE story_id = {story_id} ORDER BY id",
                    []
                )
                
                if not nodes or len(nodes) == 0:
                    logger.warning(f"No nodes found for story {story_id}")
                    return None
                
                node_dict = {}
                root_node = None
                
                for node in nodes:
                    node_id = int(get_value(node[0]))
                    is_root = bool(int(get_value(node[4]))) if get_value(node[4]) else False
                    
                    node_dict[node_id] = {
                        "id": node_id,
                        "content": get_value(node[3]),
                        "is_ending": bool(int(get_value(node[5]))) if get_value(node[5]) else False,
                        "is_winning_ending": bool(int(get_value(node[6]))) if get_value(node[6]) else False,
                        "options": []
                    }
                    
                    if is_root:
                        root_node = node_dict[node_id]
                
                for node_id in node_dict:
                    options = client.query(
                        f"SELECT next_node_id, text FROM story_options WHERE node_id = {node_id} ORDER BY id",
                        []
                    )
                    for opt in options:
                        node_dict[node_id]["options"].append({
                            "node_id": int(get_value(opt[0])),
                            "text": get_value(opt[1])
                        })
                
                if not root_node and node_dict:
                    root_node = list(node_dict.values())[0]
                
                is_liked = False
                if current_user:
                    is_liked = helpers.is_liked(current_user.id, story_id)
                
                author = helpers.get_user_by_id(story["user_id"])
                
                return {
                    "id": story["id"],
                    "title": story["title"],
                    "content": story.get("content", ""),
                    "session_id": story.get("session_id"),
                    "created_at": story.get("created_at"),
                    "root_node": root_node,
                    "all_nodes": node_dict,
                    "like_count": story.get("like_count", 0),
                    "comment_count": story.get("comment_count", 0),
                    "view_count": story.get("view_count", 0),
                    "is_liked_by_current_user": is_liked,
                    "author": {
                        "id": author["id"] if author else 0,
                        "username": author["username"] if author else "Unknown Author",
                        "full_name": author.get("full_name"),
                        "avatar_url": author.get("avatar_url")
                    }
                }
        except Exception as e:
            logger.error(f"Error building story tree: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    return None

@router.post("/generate-interactive", response_model=dict)
def generate_interactive_story(
    request: dict,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
):
    theme = request.get("theme")
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    job_id = str(uuid.uuid4())
    logger.info(f"Creating interactive story job {job_id} with theme: {theme[:50]}...")
    
    if settings.USE_TURSO:
        try:
            job_data = {
                "job_id": job_id,
                "session_id": str(uuid.uuid4()),
                "theme": theme,
                "status": "pending"
            }
            
            helpers.create_job(job_data)
            
            background_tasks.add_task(
                generate_interactive_story_task,
                job_id=job_id,
                theme=theme,
                user_id=current_user.id if current_user else None
            )
            
            return {"job_id": job_id, "status": "pending"}
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return {"job_id": job_id, "status": "pending", "warning": str(e)}
    
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
            generate_interactive_story_task,
            job_id=job_id,
            theme=theme,
            user_id=current_user.id if current_user else None
        )
        
        return job

def generate_interactive_story_task(job_id: str, theme: str, user_id: Optional[int] = None):
    logger.info(f"Generating interactive story for job {job_id} with theme: {theme}")
    
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", INTERACTIVE_STORY_PROMPT),
                ("human", "Create an interactive story with this theme: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_json = response.content if hasattr(response, "content") else str(response)
            
            json_match = re.search(r'\{.*\}', story_json, re.DOTALL)
            if json_match:
                story_json = json_match.group()
            
            story_data = json.loads(story_json)
            
            story_record = {
                "title": story_data.get("title", f"Interactive: {theme}"),
                "content": story_data.get("premise", ""),
                "excerpt": story_data.get("premise", "")[:150] + "...",
                "user_id": user_id,
                "is_published": False,
                "story_type": "interactive",
                "genre": None
            }
            
            story = helpers.create_story(story_record, user_id)
            story_id = story["id"] if story else None
            
            if story_id and story_data.get("nodes"):
                with get_turso_client() as client:
                    nodes = story_data.get("nodes", [])
                    
                    for node in nodes:
                        node_id = node.get("id")
                        content = node.get("content", "").replace("'", "''")
                        is_root = 1 if node.get("is_root", False) else 0
                        is_ending = 1 if node.get("is_ending", False) else 0
                        is_winning = 1 if node.get("is_winning_ending", False) else 0
                        
                        client.execute(
                            f"""
                            INSERT INTO story_nodes (id, story_id, content, is_root, is_ending, is_winning_ending)
                            VALUES ({node_id}, {story_id}, '{content}', {is_root}, {is_ending}, {is_winning})
                            """,
                            []
                        )
                        
                        options = node.get("options", [])
                        for option in options:
                            next_node_id = option.get("next_node_id")
                            text = option.get("text", "").replace("'", "''")
                            
                            client.execute(
                                f"""
                                INSERT INTO story_options (node_id, next_node_id, text)
                                VALUES ({node_id}, {next_node_id}, '{text}')
                                """,
                                []
                            )
                    
                    logger.info(f"Inserted {len(nodes)} nodes for story {story_id}")
            
            result = f"Story ID: {story_id}" if story_id else "Story generated"
            helpers.update_job_status(job_id, "completed", result)
            logger.info(f"Interactive story generated for job {job_id}, result: {result}")
            
        except Exception as e:
            logger.error(f"Error generating interactive story: {e}")
            import traceback
            logger.error(traceback.format_exc())
            helpers.update_job_status(job_id, "failed", str(e))
    
    else:
        from sqlalchemy.orm import Session
        from models.job import StoryJob
        from models.story import Story, StoryNode, StoryOption
        from db.database import SessionLocal
        import json
        
        db = SessionLocal()
        try:
            job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = "processing"
            db.commit()
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", INTERACTIVE_STORY_PROMPT),
                ("human", "Create an interactive story with this theme: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_json = response.content if hasattr(response, "content") else str(response)
            
            json_match = re.search(r'\{.*\}', story_json, re.DOTALL)
            if json_match:
                story_json = json_match.group()
            
            story_data = json.loads(story_json)
            
            story = Story(
                title=story_data.get("title", f"Interactive: {theme}"),
                content=story_data.get("premise", ""),
                excerpt=story_data.get("premise", "")[:150] + "...",
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                is_published=False,
                story_type="interactive"
            )
            db.add(story)
            db.flush()
            
            if story_data.get("nodes"):
                nodes = story_data.get("nodes", [])
                for node_data in nodes:
                    node = StoryNode(
                        story_id=story.id,
                        content=node_data.get("content", ""),
                        is_root=node_data.get("is_root", False),
                        is_ending=node_data.get("is_ending", False),
                        is_winning_ending=node_data.get("is_winning_ending", False)
                    )
                    db.add(node)
                    db.flush()
                    
                    for option_data in node_data.get("options", []):
                        option = StoryOption(
                            node_id=node.id,
                            next_node_id=option_data.get("next_node_id"),
                            text=option_data.get("text", "")
                        )
                        db.add(option)
            
            db.commit()
            
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
            
            logger.info(f"Interactive story generated for job {job_id}, story_id: {story.id}")
            
        except Exception as e:
            logger.error(f"Error in interactive story generation: {e}")
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

@router.post("/create", response_model=dict)
def create_story(
    request: dict,
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Depends(get_session_id),
    current_user = Depends(get_current_user_optional)
):
    theme = request.get("theme")
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    job_id = str(uuid.uuid4())
    if settings.USE_TURSO:
        try:
            job_data = {
                "job_id": job_id,
                "session_id": session_id,
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
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return {"job_id": job_id, "status": "pending", "warning": str(e)}
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
        return {"job_id": job_id, "status": "pending"}

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

@router.post("/{story_id}/publish-interactive")
def publish_interactive_story(
    story_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Publishing interactive story {story_id} for user {current_user.id}")
    
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.get("user_id"):
            raise HTTPException(status_code=400, detail="Story already published")
        
        with get_turso_client() as client:
            nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story_id}", [])
            has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
            
            if not has_nodes:
                raise HTTPException(status_code=400, detail="Cannot publish interactive story without nodes")
        
        helpers.update_story(story_id, current_user.id, {
            "user_id": current_user.id,
            "is_published": True
        })
        
        return {"message": "Interactive story published successfully", "story_id": story_id}
    
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
        
        return {"message": "Interactive story published successfully", "story_id": story.id}

@router.get("/my-stories", response_model=List[dict])
def get_my_stories(
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        stories = helpers.get_user_stories(current_user.id, limit=100)
        result = []
        for story in stories:
            author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
            with get_turso_client() as client:
                nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story['id']}", [])
                has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
            result.append({
                "id": story["id"],
                "title": story["title"],
                "content": story.get("content", ""),
                "created_at": story.get("created_at"),
                "like_count": story.get("like_count", 0),
                "comment_count": story.get("comment_count", 0),
                "view_count": story.get("view_count", 0),
                "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
                "is_liked_by_current_user": helpers.is_liked(current_user.id, story["id"]) if current_user else False,
                "has_nodes": has_nodes,
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
            has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
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
                "story_type": "interactive" if has_nodes else story.story_type,
                "has_nodes": has_nodes,
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
        with get_turso_client() as client:
            nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story_id}", [])
            has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
        return {
            "id": story["id"],
            "title": story["title"],
            "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
            "has_nodes": has_nodes
        }
    else:
        from sqlalchemy.orm import Session
        from models.story import Story, StoryNode
        from db.database import get_db
        db = next(get_db())
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story_id).count() > 0
        return {
            "id": story.id,
            "title": story.title,
            "story_type": "interactive" if has_nodes else story.story_type,
            "has_nodes": has_nodes
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
        stories = helpers.get_feed_stories(sort, "week" if sort == "trending" else "all", page, limit)
        total = len(stories)
        pages = (total + limit - 1) // limit if total > 0 else 1
        story_responses = []
        for story in stories:
            is_liked = False
            if current_user:
                is_liked = helpers.is_liked(current_user.id, story["id"])
            author = helpers.get_user_by_id(story["user_id"])
            with get_turso_client() as client:
                nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story['id']}", [])
                has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
            story_responses.append({
                "id": story["id"],
                "title": story["title"],
                "excerpt": story.get("excerpt", ""),
                "cover_image": story.get("cover_image"),
                "genre": story.get("genre"),
                "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
                "has_nodes": has_nodes,
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
        from models.story import StoryNode
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
            has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
            story_responses.append({
                "id": story.id,
                "title": story.title,
                "excerpt": story.excerpt,
                "cover_image": story.cover_image,
                "genre": getattr(story, 'genre', None),
                "story_type": "interactive" if has_nodes else story.story_type,
                "has_nodes": has_nodes,
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
            with get_turso_client() as client:
                nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story['id']}", [])
                has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
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
                "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
                "has_nodes": has_nodes,
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
        from models.story import StoryNode
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
            has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
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
                "story_type": "interactive" if has_nodes else story.story_type,
                "has_nodes": has_nodes,
                "is_liked_by_current_user": is_liked
            })
        return result

@router.get("/{story_id}/full", response_model=dict)
def get_full_story(
    story_id: int,
    current_user = Depends(get_current_user_optional)
):
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(None, story_id, user_id, str(uuid.uuid4()))
        author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
        is_liked = False
        if current_user:
            is_liked = helpers.is_liked(current_user.id, story_id)
        with get_turso_client() as client:
            nodes = client.query(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story_id}", [])
            has_nodes = nodes and len(nodes) > 0 and int(get_value(nodes[0][0])) > 0
        return {
            "id": story["id"],
            "title": story["title"],
            "content": story.get("content", ""),
            "excerpt": story.get("excerpt", ""),
            "cover_image": story.get("cover_image"),
            "created_at": story.get("created_at"),
            "like_count": story.get("like_count", 0),
            "comment_count": story.get("comment_count", 0),
            "view_count": story.get("view_count", 0) + 1,
            "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
            "has_nodes": has_nodes,
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
        from models.story import StoryNode
        from db.database import get_db
        db = next(get_db())
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(db, story_id, user_id, str(uuid.uuid4()))
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
        has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story_id).count() > 0
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
            "view_count": actual_view_count + 1,
            "story_type": "interactive" if has_nodes else story.story_type,
            "has_nodes": has_nodes,
            "is_liked_by_current_user": is_liked,
            "author": author_data
        }

@router.get("/{story_id}", response_model=dict)
def get_story_by_id(
    story_id: int,
    request: Request,
    response: Response,
    session_id: str = Depends(get_session_id),
    current_user = Depends(get_current_user_optional)
):
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    
    if settings.USE_TURSO:
        story = helpers.get_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(None, story_id, user_id, session_id)
        
        with get_turso_client() as client:
            nodes_count = client.query_one(f"SELECT COUNT(*) FROM story_nodes WHERE story_id = {story_id}", [])
            has_nodes = nodes_count and int(get_value(nodes_count[0])) > 0
        
        if has_nodes:
            complete_story = build_complete_story_tree(story_id, current_user)
            if complete_story:
                return complete_story
        
        author = helpers.get_user_by_id(story["user_id"]) if story.get("user_id") else None
        is_liked = helpers.is_liked(current_user.id, story_id) if current_user else False
        
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
            "story_type": "interactive" if has_nodes else story.get("story_type", "written"),
            "has_nodes": has_nodes,
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
        from models.story import StoryNode
        from db.database import get_db
        db = next(get_db())
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        user_id = current_user.id if current_user else None
        AnalyticsService.track_story_view(db, story_id, user_id, session_id)
        actual_view_count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
        has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story_id).count() > 0
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
        if has_nodes:
            from routers.story import build_complete_story_tree as sql_build_tree
            complete_story = sql_build_tree(db, story, current_user)
            if complete_story:
                return complete_story.dict()
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
            "story_type": "interactive" if has_nodes else story.story_type,
            "has_nodes": has_nodes,
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
    story_id: Optional[int] = Form(None),
    current_user = Depends(get_current_active_user)
):
    try:
        file_url = await save_upload_file(
            file, 
            "stories", 
            user_id=current_user.id,
            story_id=story_id
        )
        
        if story_id and settings.USE_TURSO:
            story = helpers.get_story(story_id)
            if story and story["user_id"] == current_user.id:
                helpers.update_story(story_id, current_user.id, {
                    "cover_image": file_url
                })
                logger.info(f"Story {story_id} cover image updated")
        
        return {
            "url": file_url, 
            "message": "Image uploaded successfully",
            "filename": os.path.basename(file_url)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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
            "session_id": str(uuid.uuid4()),
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
    logger.info(f"Creating assisted story job {job_id} with theme: {theme[:50]}...")
    if settings.USE_TURSO:
        try:
            job_data = {
                "job_id": job_id,
                "session_id": str(uuid.uuid4()),
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
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return {"job_id": job_id, "status": "pending", "warning": str(e)}
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

def generate_story_task(job_id: str, theme: str, session_id: str, user_id: Optional[int] = None):
    logger.info(f"Generating story for job {job_id}")
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            from db.database import SessionLocal
            from core.story_generator import StoryGenerator
            db = SessionLocal()
            try:
                story = StoryGenerator.generate_story(db, session_id, theme)
                story_data = {
                    "title": story.title,
                    "content": story.content,
                    "excerpt": story.excerpt or story.content[:150] + "...",
                    "user_id": user_id,
                    "is_published": True if user_id else False,
                    "story_type": story.story_type,
                    "genre": getattr(story, 'genre', None)
                }
                if user_id:
                    turso_story = helpers.create_story(story_data, user_id)
                    story_id = turso_story["id"] if turso_story else None
                else:
                    story_id = None
                result = f"Story ID: {story_id}" if story_id else "Story generated"
                helpers.update_job_status(job_id, "completed", result)
                logger.info(f"Story generated successfully for job {job_id}, result: {result}")
            except Exception as e:
                logger.error(f"Error in story generation: {e}")
                helpers.update_job_status(job_id, "failed", str(e))
            finally:
                db.close()
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
                logger.error(f"Job {job_id} not found")
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
            logger.info(f"Story generated successfully for job {job_id}, story_id: {story.id}")
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

def generate_full_story_task(job_id: str, theme: str, user_id: Optional[int] = None):
    logger.info(f"Generating full story for job {job_id}")
    
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            from core.groq_client import GroqLLM
            from core.prompts import FULL_STORY_PROMPT
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", FULL_STORY_PROMPT),
                ("human", "Theme: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else str(response)
            
            story_data = {
                "title": f"The {theme.title()} Story",
                "content": story_text,
                "excerpt": story_text[:150] + "...",
                "user_id": user_id,
                "is_published": True,
                "story_type": "written",
                "genre": None
            }
            
            if user_id:
                story = helpers.create_story(story_data, user_id)
                story_id = story["id"] if story else None
            else:
                story_id = None
            
            result = f"Story ID: {story_id}" if story_id else "Story generated"
            helpers.update_job_status(job_id, "completed", result)
            logger.info(f"Full story generated for job {job_id}, result: {result}")
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
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
                logger.error(f"Job {job_id} not found")
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
            
            story_text = response.content if hasattr(response, "content") else str(response)
            
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
            
            logger.info(f"Full story generated for job {job_id}, story_id: {story.id}")
            
        except Exception as e:
            logger.error(f"Error in story generation: {e}")
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

def generate_assisted_story_task(job_id: str, theme: str, cover_image: Optional[str] = None, user_id: Optional[int] = None):
    logger.info(f"Generating assisted story for job {job_id}")
    
    if settings.USE_TURSO:
        try:
            helpers.update_job_status(job_id, "processing")
            
            from core.groq_client import GroqLLM
            from core.prompts import ASSISTED_STORY_PROMPT
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = GroqLLM(api_key=app_settings.GROQ_API_KEY, model=app_settings.GROQ_MODEL)
            prompt = ChatPromptTemplate.from_messages([
                ("system", ASSISTED_STORY_PROMPT),
                ("human", "Story prompt: {theme}")
            ])
            
            formatted_prompt = prompt.invoke({"theme": theme})
            response = llm.invoke(formatted_prompt)
            
            story_text = response.content if hasattr(response, "content") else str(response)
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
                "is_published": True if user_id else False,
                "story_type": "written"
            }
            
            story = None
            if user_id:
                story = helpers.create_story(story_data, user_id)
                story_id = story["id"] if story else None
            else:
                story_id = None
            
            result = f"Story ID: {story_id}" if story_id else "Story generated"
            helpers.update_job_status(job_id, "completed", result)
            
            logger.info(f"Assisted story generated successfully for job {job_id}, result: {result}")
            
        except Exception as e:
            logger.error(f"Error generating story for job {job_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
                logger.error(f"Job {job_id} not found")
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
            
            story_text = response.content if hasattr(response, "content") else str(response)
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
            
            logger.info(f"Assisted story generated for job {job_id}, story_id: {story.id}")
            
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
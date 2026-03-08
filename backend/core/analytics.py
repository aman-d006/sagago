import logging
from typing import Optional
from datetime import datetime
from db.database import get_turso_client, settings
from db import helpers

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    @staticmethod
    def track_story_view(db, story_id: int, user_id: Optional[int], session_id: str):
        try:
            if settings.USE_TURSO:
                from db.database import get_turso_client
                with get_turso_client() as client:
                    existing = client.query_one(
                        f"SELECT id FROM story_views WHERE story_id = {story_id} AND session_id = '{session_id}'",
                        []
                    )
                    if not existing:
                        user_id_str = str(user_id) if user_id else "NULL"
                        client.execute(
                            f"""
                            INSERT INTO story_views (story_id, user_id, session_id, viewed_at)
                            VALUES ({story_id}, {user_id_str}, '{session_id}', CURRENT_TIMESTAMP)
                            """,
                            []
                        )
            else:
                from models.analytics import StoryView
                existing_view = db.query(StoryView).filter(
                    StoryView.story_id == story_id,
                    StoryView.session_id == session_id
                ).first()
                if not existing_view:
                    story_view = StoryView(
                        story_id=story_id,
                        user_id=user_id,
                        session_id=session_id
                    )
                    db.add(story_view)
                    db.commit()
        except Exception as e:
            logger.error(f"Error tracking story view: {e}")
    
    @staticmethod
    def get_story_views_count(story_id: int) -> int:
        try:
            if settings.USE_TURSO:
                with get_turso_client() as client:
                    result = client.query_one(
                        f"SELECT COUNT(*) FROM story_views WHERE story_id = {story_id}",
                        []
                    )
                    if result and len(result) > 0:
                        val = result[0]['value'] if isinstance(result[0], dict) else result[0]
                        return int(val) if val else 0
                    return 0
            else:
                from sqlalchemy.orm import Session
                from models.analytics import StoryView
                from db.database import SessionLocal
                db = SessionLocal()
                try:
                    count = db.query(StoryView).filter(StoryView.story_id == story_id).count()
                    return count
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error getting story views count: {e}")
            return 0
    
    @staticmethod
    def get_user_story_views(user_id: int) -> int:
        try:
            if settings.USE_TURSO:
                with get_turso_client() as client:
                    result = client.query_one(
                        f"SELECT COUNT(*) FROM story_views WHERE user_id = {user_id}",
                        []
                    )
                    if result and len(result) > 0:
                        val = result[0]['value'] if isinstance(result[0], dict) else result[0]
                        return int(val) if val else 0
                    return 0
            else:
                from sqlalchemy.orm import Session
                from models.analytics import StoryView
                from db.database import SessionLocal
                db = SessionLocal()
                try:
                    count = db.query(StoryView).filter(StoryView.user_id == user_id).count()
                    return count
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error getting user story views: {e}")
            return 0
    
    @staticmethod
    def get_recent_story_views(days: int = 7) -> int:
        try:
            if settings.USE_TURSO:
                with get_turso_client() as client:
                    result = client.query_one(
                        f"SELECT COUNT(*) FROM story_views WHERE viewed_at > datetime('now', '-{days} days')",
                        []
                    )
                    if result and len(result) > 0:
                        val = result[0]['value'] if isinstance(result[0], dict) else result[0]
                        return int(val) if val else 0
                    return 0
            else:
                from sqlalchemy.orm import Session
                from models.analytics import StoryView
                from db.database import SessionLocal
                from datetime import datetime, timedelta
                db = SessionLocal()
                try:
                    cutoff = datetime.now() - timedelta(days=days)
                    count = db.query(StoryView).filter(StoryView.viewed_at >= cutoff).count()
                    return count
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error getting recent story views: {e}")
            return 0
    
    @staticmethod
    def get_unique_viewers(story_id: int) -> int:
        try:
            if settings.USE_TURSO:
                with get_turso_client() as client:
                    result = client.query_one(
                        f"SELECT COUNT(DISTINCT user_id) FROM story_views WHERE story_id = {story_id} AND user_id IS NOT NULL",
                        []
                    )
                    if result and len(result) > 0:
                        val = result[0]['value'] if isinstance(result[0], dict) else result[0]
                        return int(val) if val else 0
                    return 0
            else:
                from sqlalchemy.orm import Session
                from models.analytics import StoryView
                from db.database import SessionLocal
                db = SessionLocal()
                try:
                    count = db.query(StoryView.user_id).filter(
                        StoryView.story_id == story_id,
                        StoryView.user_id.isnot(None)
                    ).distinct().count()
                    return count
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error getting unique viewers: {e}")
            return 0
    
    @staticmethod
    def get_return_viewers(story_id: int) -> int:
        try:
            if settings.USE_TURSO:
                with get_turso_client() as client:
                    result = client.query_one(
                        f"""
                        SELECT COUNT(*) FROM (
                            SELECT user_id, COUNT(*) as view_count 
                            FROM story_views 
                            WHERE story_id = {story_id} AND user_id IS NOT NULL
                            GROUP BY user_id
                            HAVING view_count > 1
                        ) as return_viewers
                        """,
                        []
                    )
                    if result and len(result) > 0:
                        val = result[0]['value'] if isinstance(result[0], dict) else result[0]
                        return int(val) if val else 0
                    return 0
            else:
                from sqlalchemy.orm import Session
                from models.analytics import StoryView
                from db.database import SessionLocal
                from sqlalchemy import func
                db = SessionLocal()
                try:
                    result = db.query(
                        StoryView.user_id,
                        func.count(StoryView.id).label('view_count')
                    ).filter(
                        StoryView.story_id == story_id,
                        StoryView.user_id.isnot(None)
                    ).group_by(StoryView.user_id).having(func.count(StoryView.id) > 1).count()
                    return result
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error getting return viewers: {e}")
            return 0
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, date
from models.user import User
from models.story import Story
from models.like import StoryLike
from models.comment import Comment
from models.analytics import StoryView, DailyMetrics
from typing import List, Dict, Any

class AnalyticsService:
    
    @staticmethod
    def track_story_view(db: Session, story_id: int, user_id: int = None, session_id: str = None):
        if not user_id and not session_id:
            return
            
        existing_view = None
        if user_id:
            existing_view = db.query(StoryView).filter(
                StoryView.story_id == story_id,
                StoryView.user_id == user_id
            ).first()
        
        if not existing_view and not user_id and session_id:
            existing_view = db.query(StoryView).filter(
                StoryView.story_id == story_id,
                StoryView.session_id == session_id
            ).first()
        
        if not existing_view:
            view = StoryView(
                story_id=story_id,
                user_id=user_id,
                session_id=session_id
            )
            db.add(view)
            db.commit()
            
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.last_active = datetime.now()
                    db.commit()
    
    @staticmethod
    def get_story_analytics(db: Session, story_id: int) -> Dict[str, Any]:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return None
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        views_over_time = db.query(
            func.date(StoryView.viewed_at).label('date'),
            func.count(StoryView.id).label('count')
        ).filter(
            StoryView.story_id == story_id,
            StoryView.viewed_at >= seven_days_ago
        ).group_by(func.date(StoryView.viewed_at)).all()
        
        unique_viewers = db.query(StoryView.user_id).filter(
            StoryView.story_id == story_id,
            StoryView.user_id.isnot(None)
        ).distinct().count()
        
        total_views = db.query(StoryView).filter(StoryView.story_id == story_id).count()
        engagement = story.like_count + story.comment_count
        engagement_rate = (engagement / total_views * 100) if total_views > 0 else 0
        
        return {
            "story_id": story.id,
            "title": story.title,
            "total_views": total_views,
            "unique_viewers": unique_viewers,
            "likes": story.like_count,
            "comments": story.comment_count,
            "engagement_rate": round(engagement_rate, 2),
            "views_over_time": [
                {"date": str(v.date), "views": v.count} for v in views_over_time
            ]
        }
    
    @staticmethod
    def get_user_analytics(db: Session, user_id: int) -> Dict[str, Any]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        stories = db.query(Story).filter(Story.user_id == user_id).all()
        
        top_stories = []
        for story in sorted(stories, key=lambda s: s.view_count, reverse=True)[:5]:
            top_stories.append({
                "story_id": story.id,
                "title": story.title,
                "views": story.view_count,
                "likes": story.like_count,
                "comments": story.comment_count
            })
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        story_activity = db.query(
            func.date(Story.created_at).label('date'),
            func.count(Story.id).label('stories')
        ).filter(
            Story.user_id == user_id,
            Story.created_at >= thirty_days_ago
        ).group_by(func.date(Story.created_at)).all()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "total_stories": len(stories),
            "total_views": sum(s.view_count for s in stories),
            "total_likes_received": user.total_likes_received,
            "total_comments_received": user.total_comments_received,
            "followers_count": user.followers_count,
            "following_count": user.following_count,
            "top_stories": top_stories,
            "story_activity": [
                {"date": str(a.date), "stories": a.stories} for a in story_activity
            ]
        }
    
    @staticmethod
    def get_platform_overview(db: Session) -> Dict[str, Any]:
        total_users = db.query(User).count()
        total_stories = db.query(Story).filter(Story.is_published == True).count()
        total_views = db.query(StoryView).count()
        total_unique_views = db.query(StoryView.user_id).filter(StoryView.user_id.isnot(None)).distinct().count()
        total_likes = db.query(StoryLike).count()
        total_comments = db.query(Comment).count()
        
        avg_stories_per_user = total_stories / total_users if total_users > 0 else 0
        avg_views_per_story = total_views / total_stories if total_stories > 0 else 0
        engagement_rate = ((total_likes + total_comments) / total_views * 100) if total_views > 0 else 0
        
        today = date.today()
        new_users_today = db.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        new_stories_today = db.query(Story).filter(
            func.date(Story.created_at) == today
        ).count()
        
        active_users_today = db.query(StoryView.user_id).filter(
            func.date(StoryView.viewed_at) == today,
            StoryView.user_id.isnot(None)
        ).distinct().count()
        
        return {
            "total_users": total_users,
            "total_stories": total_stories,
            "total_views": total_views,
            "total_unique_viewers": total_unique_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avg_stories_per_user": round(avg_stories_per_user, 2),
            "avg_views_per_story": round(avg_views_per_story, 2),
            "engagement_rate": round(engagement_rate, 2),
            "new_users_today": new_users_today,
            "new_stories_today": new_stories_today,
            "active_users_today": active_users_today
        }
    
    @staticmethod
    def get_trending_stories(db: Session, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        since_date = datetime.now() - timedelta(days=days)
        
        trending = db.query(
            Story,
            func.count(StoryView.id).label('recent_views')
        ).join(
            StoryView, Story.id == StoryView.story_id
        ).filter(
            StoryView.viewed_at >= since_date,
            Story.is_published == True
        ).group_by(
            Story.id
        ).order_by(
            desc('recent_views')
        ).limit(limit).all()
        
        result = []
        for story, recent_views in trending:
            result.append({
                "story_id": story.id,
                "title": story.title,
                "author": story.author.username,
                "recent_views": recent_views,
                "total_views": story.view_count,
                "likes": story.like_count,
                "comments": story.comment_count
            })
        
        return result
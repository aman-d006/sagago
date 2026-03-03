from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta, date
from db.database import get_db
from models.user import User
from models.story import Story
from models.like import StoryLike
from models.comment import Comment
from models.follow import Follow
from models.analytics import StoryView, DailyMetrics
from schemas.analytics import (
    StoryAnalytics, UserAnalytics, DailyMetricResponse,
    TimeSeriesData, PlatformOverview, StoryEngagementResponse
)
from core.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard/me", response_model=dict)
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    stories = db.query(Story).filter(
        Story.user_id == current_user.id,
        Story.is_published == True
    ).order_by(desc(Story.created_at)).all()
    
    total_views = 0
    total_likes = 0
    total_comments = 0
    total_read_time = 0
    
    story_stats = []
    for story in stories:
        view_count = len(story.views)
        like_count = len(story.likes)
        comment_count = len(story.comments)
        
        total_views += view_count
        total_likes += like_count
        total_comments += comment_count
        
        word_count = len(story.content.split()) if story.content else 0
        reading_time = max(1, round(word_count / 200))
        total_read_time += reading_time * view_count
        
        story_stats.append({
            "id": story.id,
            "title": story.title,
            "created_at": story.created_at,
            "views": view_count,
            "likes": like_count,
            "comments": comment_count,
            "story_type": story.story_type,
            "reading_time": reading_time,
            "engagement_rate": round(((like_count + comment_count) / view_count * 100), 2) if view_count > 0 else 0
        })
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    daily_views = db.query(
        func.date(StoryView.viewed_at).label('date'),
        func.count(StoryView.id).label('count')
    ).join(
        Story, Story.id == StoryView.story_id
    ).filter(
        Story.user_id == current_user.id,
        StoryView.viewed_at >= thirty_days_ago
    ).group_by(func.date(StoryView.viewed_at)).order_by('date').all()
    
    daily_likes = db.query(
        func.date(StoryLike.created_at).label('date'),
        func.count(StoryLike.id).label('count')
    ).join(
        Story, Story.id == StoryLike.story_id
    ).filter(
        Story.user_id == current_user.id,
        StoryLike.created_at >= thirty_days_ago
    ).group_by(func.date(StoryLike.created_at)).order_by('date').all()
    
    follower_growth = db.query(
        func.date(Follow.created_at).label('date'),
        func.count(Follow.id).label('count')
    ).filter(
        Follow.following_id == current_user.id,
        Follow.is_active == True,
        Follow.created_at >= thirty_days_ago
    ).group_by(func.date(Follow.created_at)).order_by('date').all()
    
    top_stories = sorted(story_stats, key=lambda x: x['views'], reverse=True)[:5]
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_views = db.query(StoryView).join(
        Story, Story.id == StoryView.story_id
    ).filter(
        Story.user_id == current_user.id,
        StoryView.viewed_at >= seven_days_ago
    ).count()
    
    recent_likes = db.query(StoryLike).join(
        Story, Story.id == StoryLike.story_id
    ).filter(
        Story.user_id == current_user.id,
        StoryLike.created_at >= seven_days_ago
    ).count()
    
    recent_comments = db.query(Comment).join(
        Story, Story.id == Comment.story_id
    ).filter(
        Story.user_id == current_user.id,
        Comment.created_at >= seven_days_ago
    ).count()
    
    recent_followers = db.query(Follow).filter(
        Follow.following_id == current_user.id,
        Follow.is_active == True,
        Follow.created_at >= seven_days_ago
    ).count()
    
    avg_views_per_story = total_views / len(stories) if stories else 0
    avg_likes_per_view = (total_likes / total_views * 100) if total_views > 0 else 0
    avg_comments_per_view = (total_comments / total_views * 100) if total_views > 0 else 0
    
    return {
        "user": {
            "username": current_user.username,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "joined": current_user.created_at,
            "followers": current_user.followers_count,
            "following": current_user.following_count,
            "total_stories": len(stories)
        },
        "overview": {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_read_time": total_read_time,
            "avg_views_per_story": round(avg_views_per_story, 1),
            "avg_likes_per_view": round(avg_likes_per_view, 1),
            "avg_comments_per_view": round(avg_comments_per_view, 1)
        },
        "recent_activity": {
            "views_last_7_days": recent_views,
            "likes_last_7_days": recent_likes,
            "comments_last_7_days": recent_comments,
            "new_followers_last_7_days": recent_followers
        },
        "time_series": {
            "labels": [str(d.date) for d in daily_views],
            "views": [d.count for d in daily_views],
            "likes": [d.count for d in daily_likes],
            "followers": [d.count for d in follower_growth]
        },
        "top_stories": top_stories,
        "story_stats": story_stats
    }

@router.get("/story/{story_id}", response_model=dict)
def get_story_analytics(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these analytics")
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    views_over_time = db.query(
        func.date(StoryView.viewed_at).label('date'),
        func.count(StoryView.id).label('count')
    ).filter(
        StoryView.story_id == story_id,
        StoryView.viewed_at >= thirty_days_ago
    ).group_by(func.date(StoryView.viewed_at)).order_by('date').all()
    
    unique_viewers = db.query(StoryView.user_id).filter(
        StoryView.story_id == story_id,
        StoryView.user_id.isnot(None)
    ).distinct().count()
    
    return_viewers = db.query(
        StoryView.user_id,
        func.count(StoryView.id).label('view_count')
    ).filter(
        StoryView.story_id == story_id,
        StoryView.user_id.isnot(None)
    ).group_by(StoryView.user_id).having(func.count(StoryView.id) > 1).count()
    
    hourly_views = db.query(
        func.strftime('%H', StoryView.viewed_at).label('hour'),
        func.count(StoryView.id).label('count')
    ).filter(
        StoryView.story_id == story_id
    ).group_by('hour').order_by('hour').all()
    
    total_views = story.view_count
    engagement = story.like_count + story.comment_count
    engagement_rate = (engagement / total_views * 100) if total_views > 0 else 0
    
    return {
        "story_id": story.id,
        "title": story.title,
        "story_type": story.story_type,
        "created_at": story.created_at,
        "total_views": total_views,
        "unique_viewers": unique_viewers,
        "return_viewers": return_viewers,
        "likes": story.like_count,
        "comments": story.comment_count,
        "engagement_rate": round(engagement_rate, 2),
        "views_over_time": [
            {"date": str(v.date), "views": v.count} for v in views_over_time
        ],
        "hourly_distribution": [
            {"hour": h.hour, "views": h.count} for h in hourly_views
        ]
    }

@router.get("/user/{username}", response_model=dict)
def get_user_analytics(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these analytics")
    
    stories = db.query(Story).filter(Story.user_id == user.id).all()
    
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
        Story.user_id == user.id,
        Story.created_at >= thirty_days_ago
    ).group_by(func.date(Story.created_at)).all()
    
    return {
        "user_id": user.id,
        "username": user.username,
        "total_stories": len(stories),
        "total_views": sum(s.view_count for s in stories),
        "total_likes_received": sum(s.like_count for s in stories),
        "total_comments_received": sum(s.comment_count for s in stories),
        "followers_count": user.followers_count,
        "following_count": user.following_count,
        "top_stories": top_stories,
        "story_activity": [
            {"date": str(a.date), "stories": a.stories} for a in story_activity
        ]
    }

@router.get("/overview", response_model=PlatformOverview)
def get_platform_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = db.query(User).count()
    total_stories = db.query(Story).filter(Story.is_published == True).count()
    total_views = db.query(StoryView).count()
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
    
    return PlatformOverview(
        total_users=total_users,
        total_stories=total_stories,
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        avg_stories_per_user=round(avg_stories_per_user, 2),
        avg_views_per_story=round(avg_views_per_story, 2),
        engagement_rate=round(engagement_rate, 2),
        new_users_today=new_users_today,
        new_stories_today=new_stories_today,
        active_users_today=active_users_today
    )

@router.get("/trending", response_model=List[dict])
def get_trending_stories(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
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
            "author": story.author.username if story.author else "Unknown",
            "author_id": story.author.id if story.author else None,
            "recent_views": recent_views,
            "total_views": story.view_count,
            "likes": story.like_count,
            "comments": story.comment_count,
            "created_at": story.created_at
        })
    
    return result

@router.get("/time-series", response_model=TimeSeriesData)
def get_time_series_data(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    dates = []
    views_data = []
    likes_data = []
    comments_data = []
    users_data = []
    
    current = start_date
    while current <= end_date:
        next_day = current + timedelta(days=1)
        
        views = db.query(StoryView).filter(
            StoryView.viewed_at >= current,
            StoryView.viewed_at < next_day
        ).count()
        
        likes = db.query(StoryLike).filter(
            StoryLike.created_at >= current,
            StoryLike.created_at < next_day
        ).count()
        
        comments = db.query(Comment).filter(
            Comment.created_at >= current,
            Comment.created_at < next_day
        ).count()
        
        new_users = db.query(User).filter(
            User.created_at >= current,
            User.created_at < next_day
        ).count()
        
        dates.append(current.strftime("%Y-%m-%d"))
        views_data.append(views)
        likes_data.append(likes)
        comments_data.append(comments)
        users_data.append(new_users)
        
        current = next_day
    
    return TimeSeriesData(
        labels=dates,
        views=views_data,
        likes=likes_data,
        comments=comments_data,
        users=users_data
    )

@router.get("/stories/top", response_model=List[StoryEngagementResponse])
def get_top_stories(
    metric: str = Query("views", pattern="^(views|likes|comments|engagement)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if metric == "views":
        view_counts = db.query(
            StoryView.story_id, 
            func.count(StoryView.id).label('view_count')
        ).group_by(StoryView.story_id).subquery()
        
        stories = db.query(Story).outerjoin(
            view_counts, Story.id == view_counts.c.story_id
        ).filter(
            Story.is_published == True
        ).order_by(
            view_counts.c.view_count.desc().nullslast()
        ).limit(limit).all()
        
    elif metric == "likes":
        like_counts = db.query(
            StoryLike.story_id, 
            func.count(StoryLike.id).label('like_count')
        ).group_by(StoryLike.story_id).subquery()
        
        stories = db.query(Story).outerjoin(
            like_counts, Story.id == like_counts.c.story_id
        ).filter(
            Story.is_published == True
        ).order_by(
            like_counts.c.like_count.desc().nullslast()
        ).limit(limit).all()
        
    elif metric == "comments":
        comment_counts = db.query(
            Comment.story_id, 
            func.count(Comment.id).label('comment_count')
        ).group_by(Comment.story_id).subquery()
        
        stories = db.query(Story).outerjoin(
            comment_counts, Story.id == comment_counts.c.story_id
        ).filter(
            Story.is_published == True
        ).order_by(
            comment_counts.c.comment_count.desc().nullslast()
        ).limit(limit).all()
        
    else:
        stories = db.query(Story).filter(Story.is_published == True).all()
        
        story_scores = []
        for story in stories:
            view_count = len(story.views)
            if view_count > 0:
                engagement = (len(story.likes) + len(story.comments)) / view_count
            else:
                engagement = 0
            story_scores.append((story, engagement))
        
        story_scores.sort(key=lambda x: x[1], reverse=True)
        stories = [s[0] for s in story_scores[:limit]]
    
    result = []
    for story in stories:
        view_count = len(story.views)
        like_count = len(story.likes)
        comment_count = len(story.comments)
        
        like_rate = (like_count / view_count * 100) if view_count > 0 else 0
        comment_rate = (comment_count / view_count * 100) if view_count > 0 else 0
        
        result.append(StoryEngagementResponse(
            story_id=story.id,
            title=story.title,
            views=view_count,
            likes=like_count,
            comments=comment_count,
            like_rate=round(like_rate, 2),
            comment_rate=round(comment_rate, 2),
            completion_rate=None
        ))
    
    return result
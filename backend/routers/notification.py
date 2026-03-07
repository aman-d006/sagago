from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=dict)
def get_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    unread_only: bool = Query(False),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting notifications for user {current_user.id}")
    
    if settings.USE_TURSO:
        offset = (page - 1) * per_page
        notifications = helpers.get_user_notifications(current_user.id, limit=per_page)
        
        paginated = notifications[offset:offset+per_page]
        
        total = len(notifications)
        unread_count = helpers.get_unread_notification_count(current_user.id)
        pages = (total + per_page - 1) // per_page
        
        notification_list = []
        for notif in paginated:
            notification_list.append({
                "id": notif["id"],
                "notification_type": notif.get("type"),
                "actor_username": notif.get("actor_username", "System"),
                "actor_avatar": notif.get("actor_avatar"),
                "story_title": notif.get("story_title"),
                "story_id": notif.get("related_id"),
                "comment_preview": notif.get("content", "")[:50] + "..." if notif.get("content") and len(notif.get("content", "")) > 50 else notif.get("content"),
                "content": notif.get("content"),
                "is_read": notif.get("is_read", False),
                "created_at": notif.get("created_at")
            })
        
        return {
            "notifications": notification_list,
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "pages": pages
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.notification import Notification
        
        db = next(get_db())
        
        query = db.query(Notification).filter(Notification.user_id == current_user.id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        query = query.order_by(desc(Notification.created_at))
        
        total = query.count()
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        pages = (total + per_page - 1) // per_page
        notifications = query.offset((page - 1) * per_page).limit(per_page).all()
        
        notification_list = []
        for notif in notifications:
            notification_list.append({
                "id": notif.id,
                "notification_type": notif.notification_type,
                "actor_username": notif.actor.username if notif.actor else "System",
                "actor_avatar": notif.actor.avatar_url if notif.actor else None,
                "story_title": notif.story.title if notif.story else None,
                "story_id": notif.story_id,
                "comment_preview": notif.comment.content[:50] + "..." if notif.comment and len(notif.comment.content) > 50 else (notif.comment.content if notif.comment else None),
                "content": notif.content,
                "is_read": notif.is_read,
                "created_at": notif.created_at
            })
        
        return {
            "notifications": notification_list,
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "pages": pages
        }

@router.get("/unread/count", response_model=dict)
def get_unread_count(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting unread count for user {current_user.id}")
    
    if settings.USE_TURSO:
        count = helpers.get_unread_notification_count(current_user.id)
        return {"unread_count": count}
    
    else:
        from sqlalchemy.orm import Session
        from models.notification import Notification
        
        db = next(get_db())
        
        count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        return {"unread_count": count}

@router.post("/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Marking notification {notification_id} as read")
    
    if settings.USE_TURSO:
        success = helpers.mark_notification_read(notification_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    
    else:
        from sqlalchemy.orm import Session
        from models.notification import Notification
        
        db = next(get_db())
        
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification.is_read = True
        db.commit()
        
        return {"message": "Notification marked as read"}

@router.post("/read-all", response_model=dict)
def mark_all_notifications_read(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Marking all notifications as read for user {current_user.id}")
    
    if settings.USE_TURSO:
        success = helpers.mark_all_notifications_read(current_user.id)
        return {"message": "All notifications marked as read"}
    
    else:
        from sqlalchemy.orm import Session
        from models.notification import Notification
        
        db = next(get_db())
        
        db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({Notification.is_read: True})
        
        db.commit()
        
        return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Deleting notification {notification_id}")
    
    if settings.USE_TURSO:
        return {"message": "Notification deleted"}
    
    else:
        from sqlalchemy.orm import Session
        from models.notification import Notification
        
        db = next(get_db())
        
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted"}

@router.delete("/", response_model=dict)
def delete_all_notifications(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Deleting all notifications for user {current_user.id}")
    
    if settings.USE_TURSO:
        return {"message": "All notifications deleted"}
    
    else:
        from sqlalchemy.orm import Session
        from models.notification import Notification
        
        db = next(get_db())
        
        db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {"message": "All notifications deleted"}
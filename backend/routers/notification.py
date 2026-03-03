from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime
from db.database import get_db
from models.user import User
from models.story import Story
from models.comment import Comment
from models.notification import Notification
from schemas.notification import (
    NotificationResponse, 
    NotificationListResponse, 
    NotificationCountResponse,
    NotificationMarkRead
)
from core.auth import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
        notification_list.append(NotificationResponse(
            id=notif.id,
            notification_type=notif.notification_type,
            actor_username=notif.actor.username,
            actor_avatar=notif.actor.avatar_url,
            story_title=notif.story.title if notif.story else None,
            story_id=notif.story_id,
            comment_preview=notif.comment.content[:50] + "..." if notif.comment and len(notif.comment.content) > 50 else (notif.comment.content if notif.comment else None),
            content=notif.content,
            is_read=notif.is_read,
            created_at=notif.created_at
        ))
    
    return NotificationListResponse(
        notifications=notification_list,
        total=total,
        unread_count=unread_count,
        page=page,
        pages=pages
    )

@router.get("/unread/count", response_model=NotificationCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return NotificationCountResponse(unread_count=count)

@router.post("/{notification_id}/read", response_model=NotificationMarkRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return NotificationMarkRead(message="Notification marked as read")

@router.post("/read-all", response_model=NotificationMarkRead)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({Notification.is_read: True})
    
    db.commit()
    
    return NotificationMarkRead(message="All notifications marked as read")

@router.delete("/{notification_id}", response_model=NotificationMarkRead)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return NotificationMarkRead(message="Notification deleted")

@router.delete("/", response_model=NotificationMarkRead)
def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return NotificationMarkRead(message="All notifications deleted")
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from db.database import get_db
from models.user import User
from models.follow import Follow
from schemas.follow import FollowResponse, FollowStats, FollowAction
from core.auth import get_current_active_user
from core.notifications import NotificationService
from datetime import datetime

router = APIRouter(prefix="/users", tags=["follows"])

@router.post("/{username}/follow", response_model=FollowAction)
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    
    user_to_follow = db.query(User).filter(User.username == username).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_follow = db.query(Follow).filter(
        and_(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_to_follow.id
        )
    ).first()
    
    if existing_follow:
        if existing_follow.is_active:
            existing_follow.is_active = False
            message = f"Unfollowed {username}"
            is_following = False
        else:
            existing_follow.is_active = True
            message = f"Following {username}"
            is_following = True
            # Create notification when reactivating follow
            NotificationService.create_follow_notification(
                db=db,
                followed_user_id=user_to_follow.id,
                follower_id=current_user.id
            )
    else:
        new_follow = Follow(
            follower_id=current_user.id,
            following_id=user_to_follow.id,
            is_active=True
        )
        db.add(new_follow)
        message = f"Following {username}"
        is_following = True
        
        # Create notification for new follow
        NotificationService.create_follow_notification(
            db=db,
            followed_user_id=user_to_follow.id,
            follower_id=current_user.id
        )
    
    db.commit()
    
    followers_count = db.query(Follow).filter(
        Follow.following_id == user_to_follow.id,
        Follow.is_active == True
    ).count()
    
    return FollowAction(
        message=message,
        is_following=is_following,
        followers_count=followers_count
    )

@router.get("/{username}/followers", response_model=List[FollowResponse])
def get_followers(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = db.query(Follow).filter(
        Follow.following_id == user.id,
        Follow.is_active == True
    ).order_by(Follow.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for follow in followers:
        follower = follow.follower
        result.append(FollowResponse(
            id=follower.id,
            user_id=follower.id,
            username=follower.username,
            full_name=follower.full_name,
            avatar_url=follower.avatar_url,
            bio=follower.bio,
            followed_at=follow.created_at
        ))
    
    return result

@router.get("/{username}/following", response_model=List[FollowResponse])
def get_following(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = db.query(Follow).filter(
        Follow.follower_id == user.id,
        Follow.is_active == True
    ).order_by(Follow.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for follow in following:
        followed_user = follow.following
        result.append(FollowResponse(
            id=followed_user.id,
            user_id=followed_user.id,
            username=followed_user.username,
            full_name=followed_user.full_name,
            avatar_url=followed_user.avatar_url,
            bio=followed_user.bio,
            followed_at=follow.created_at
        ))
    
    return result

@router.get("/{username}/stats", response_model=FollowStats)
def get_follow_stats(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers_count = db.query(Follow).filter(
        Follow.following_id == user.id,
        Follow.is_active == True
    ).count()
    
    following_count = db.query(Follow).filter(
        Follow.follower_id == user.id,
        Follow.is_active == True
    ).count()
    
    is_following = False
    is_follower = False
    
    if current_user:
        is_following = db.query(Follow).filter(
            and_(
                Follow.follower_id == current_user.id,
                Follow.following_id == user.id,
                Follow.is_active == True
            )
        ).first() is not None
        
        is_follower = db.query(Follow).filter(
            and_(
                Follow.follower_id == user.id,
                Follow.following_id == current_user.id,
                Follow.is_active == True
            )
        ).first() is not None
    
    return FollowStats(
        followers_count=followers_count,
        following_count=following_count,
        is_following=is_following,
        is_follower=is_follower
    )

@router.get("/suggestions", response_model=List[FollowResponse])
def get_follow_suggestions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    following_ids = db.query(Follow.following_id).filter(
        Follow.follower_id == current_user.id,
        Follow.is_active == True
    ).subquery()
    
    suggestions = db.query(User).filter(
        User.id != current_user.id,
        User.id.notin_(following_ids),
        User.is_active == True
    ).order_by(User.created_at.desc()).limit(limit).all()
    
    result = []
    for user in suggestions:
        result.append(FollowResponse(
            id=user.id,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            followed_at=datetime.now()
        ))
    
    return result
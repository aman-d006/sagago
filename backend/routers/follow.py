from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user
from core.notifications import NotificationService

router = APIRouter(prefix="/users", tags=["follows"])
logger = logging.getLogger(__name__)

@router.post("/{username}/follow", response_model=dict)
def follow_user(
    username: str,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Follow/unfollow: {current_user.username} -> {username}")
    
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    
    try:
        if settings.USE_TURSO:
            user_to_follow = helpers.get_user_by_username(username)
            if not user_to_follow:
                raise HTTPException(status_code=404, detail="User not found")
            
            result = helpers.toggle_follow(current_user.id, user_to_follow["id"])
            
            # Create notification if following (don't fail if notification fails)
            if result["following"]:
                try:
                    NotificationService.create_follow_notification(
                        db=None,
                        followed_user_id=user_to_follow["id"],
                        follower_id=current_user.id
                    )
                except Exception as e:
                    logger.error(f"Failed to create follow notification: {e}")
            
            return {
                "message": f"{'Following' if result['following'] else 'Unfollowed'} {username}",
                "is_following": result["following"],
                "followers_count": result.get("followers_count", 0)
            }
        
        else:
            from sqlalchemy.orm import Session
            from sqlalchemy import and_
            from models.user import User
            from models.follow import Follow
            
            db = next(get_db())
            
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
                    try:
                        NotificationService.create_follow_notification(
                            db=db,
                            followed_user_id=user_to_follow.id,
                            follower_id=current_user.id
                        )
                    except Exception as e:
                        logger.error(f"Failed to create follow notification: {e}")
            else:
                new_follow = Follow(
                    follower_id=current_user.id,
                    following_id=user_to_follow.id,
                    is_active=True
                )
                db.add(new_follow)
                message = f"Following {username}"
                is_following = True
                try:
                    NotificationService.create_follow_notification(
                        db=db,
                        followed_user_id=user_to_follow.id,
                        follower_id=current_user.id
                    )
                except Exception as e:
                    logger.error(f"Failed to create follow notification: {e}")
            
            db.commit()
            
            followers_count = db.query(Follow).filter(
                Follow.following_id == user_to_follow.id,
                Follow.is_active == True
            ).count()
            
            return {
                "message": message,
                "is_following": is_following,
                "followers_count": followers_count
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in follow_user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{username}/followers", response_model=List[dict])
def get_followers(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting followers for {username}")
    
    try:
        if settings.USE_TURSO:
            user = helpers.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            followers = helpers.get_followers(user["id"], limit=limit)
            
            # Apply pagination
            paginated = followers[skip:skip+limit]
            
            result = []
            for follower_data in paginated:
                is_following = helpers.is_following(current_user.id, follower_data["id"])
                
                result.append({
                    "id": follower_data["id"],
                    "user_id": follower_data["id"],
                    "username": follower_data["username"],
                    "full_name": follower_data["full_name"],
                    "avatar_url": follower_data["avatar_url"],
                    "bio": follower_data.get("bio", ""),
                    "followed_at": follower_data.get("followed_at", datetime.now().isoformat()),
                    "is_following": is_following
                })
            
            return result
        
        else:
            from sqlalchemy.orm import Session
            from sqlalchemy import desc
            from models.user import User
            from models.follow import Follow
            
            db = next(get_db())
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            followers = db.query(Follow).filter(
                Follow.following_id == user.id,
                Follow.is_active == True
            ).order_by(desc(Follow.created_at)).offset(skip).limit(limit).all()
            
            result = []
            for follow in followers:
                follower = follow.follower
                is_following = False
                if current_user:
                    is_following = db.query(Follow).filter(
                        Follow.follower_id == current_user.id,
                        Follow.following_id == follower.id,
                        Follow.is_active == True
                    ).first() is not None
                
                result.append({
                    "id": follower.id,
                    "user_id": follower.id,
                    "username": follower.username,
                    "full_name": follower.full_name,
                    "avatar_url": follower.avatar_url,
                    "bio": follower.bio,
                    "followed_at": follow.created_at.isoformat() if follow.created_at else None,
                    "is_following": is_following
                })
            
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_followers: {e}")
        return []

@router.get("/{username}/following", response_model=List[dict])
def get_following(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting users followed by {username}")
    
    try:
        if settings.USE_TURSO:
            user = helpers.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            following = helpers.get_following(user["id"], limit=limit)
            
            # Apply pagination
            paginated = following[skip:skip+limit]
            
            result = []
            for followed_data in paginated:
                is_following = helpers.is_following(current_user.id, followed_data["id"])
                
                result.append({
                    "id": followed_data["id"],
                    "user_id": followed_data["id"],
                    "username": followed_data["username"],
                    "full_name": followed_data["full_name"],
                    "avatar_url": followed_data["avatar_url"],
                    "bio": followed_data.get("bio", ""),
                    "followed_at": followed_data.get("followed_at", datetime.now().isoformat()),
                    "is_following": is_following
                })
            
            return result
        
        else:
            from sqlalchemy.orm import Session
            from sqlalchemy import desc
            from models.user import User
            from models.follow import Follow
            
            db = next(get_db())
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            following = db.query(Follow).filter(
                Follow.follower_id == user.id,
                Follow.is_active == True
            ).order_by(desc(Follow.created_at)).offset(skip).limit(limit).all()
            
            result = []
            for follow in following:
                followed_user = follow.following
                is_following = False
                if current_user:
                    is_following = db.query(Follow).filter(
                        Follow.follower_id == current_user.id,
                        Follow.following_id == followed_user.id,
                        Follow.is_active == True
                    ).first() is not None
                
                result.append({
                    "id": followed_user.id,
                    "user_id": followed_user.id,
                    "username": followed_user.username,
                    "full_name": followed_user.full_name,
                    "avatar_url": followed_user.avatar_url,
                    "bio": followed_user.bio,
                    "followed_at": follow.created_at.isoformat() if follow.created_at else None,
                    "is_following": is_following
                })
            
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_following: {e}")
        return []

@router.get("/{username}/stats", response_model=dict)
def get_follow_stats(
    username: str,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting follow stats for {username}")
    
    try:
        if settings.USE_TURSO:
            user = helpers.get_user_by_username(username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            followers_count = helpers.get_followers_count(user["id"])
            following_count = helpers.get_following_count(user["id"])
            
            is_following = helpers.is_following(current_user.id, user["id"])
            is_follower = helpers.is_following(user["id"], current_user.id)
            
            return {
                "followers_count": followers_count,
                "following_count": following_count,
                "is_following": is_following,
                "is_follower": is_follower
            }
        
        else:
            from sqlalchemy.orm import Session
            from sqlalchemy import and_
            from models.user import User
            from models.follow import Follow
            
            db = next(get_db())
            
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
            
            return {
                "followers_count": followers_count,
                "following_count": following_count,
                "is_following": is_following,
                "is_follower": is_follower
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_follow_stats: {e}")
        return {
            "followers_count": 0,
            "following_count": 0,
            "is_following": False,
            "is_follower": False
        }

@router.get("/suggestions", response_model=List[dict])
def get_follow_suggestions(
    limit: int = Query(5, ge=1, le=50),
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting follow suggestions for {current_user.username}")
    
    try:
        if settings.USE_TURSO:
            suggestions = helpers.get_follow_suggestions(current_user.id, limit)
            
            result = []
            for user in suggestions:
                full_user = helpers.get_user_by_id(user["id"])
                
                result.append({
                    "id": user["id"],
                    "user_id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "avatar_url": user["avatar_url"],
                    "bio": full_user.get("bio", "") if full_user else "",
                    "followed_at": datetime.now().isoformat(),
                    "is_following": False
                })
            
            return result
        
        else:
            from sqlalchemy.orm import Session
            from models.user import User
            from models.follow import Follow
            
            db = next(get_db())
            
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
                result.append({
                    "id": user.id,
                    "user_id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "followed_at": datetime.now().isoformat(),
                    "is_following": False
                })
            
            return result
    except Exception as e:
        logger.error(f"Error in get_follow_suggestions: {e}")
        return []  
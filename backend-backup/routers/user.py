from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional
from db.database import get_db
from models.user import User
from models.story import Story, StoryNode
from models.follow import Follow
from schemas.user import UserResponse, UserProfileResponse, UserStoryResponse
from core.auth import get_current_active_user
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/search", response_model=List[UserResponse])
def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Searching users with query: {q}")
    
    search = f"%{q}%"
    users = db.query(User).filter(
        or_(
            User.username.ilike(search),
            User.full_name.ilike(search)
        ),
        User.is_active == True
    ).limit(limit).all()
    
    result = []
    for user in users:
        followers_count = db.query(Follow).filter(
            Follow.following_id == user.id,
            Follow.is_active == True
        ).count()
        
        following_count = db.query(Follow).filter(
            Follow.follower_id == user.id,
            Follow.is_active == True
        ).count()
        
        stories_count = db.query(Story).filter(
            Story.user_id == user.id,
            Story.is_published == True
        ).count()
        
        is_following = False
        if current_user:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user.id,
                Follow.following_id == user.id,
                Follow.is_active == True
            ).first() is not None
        
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "created_at": user.created_at,
            "followers_count": followers_count,
            "following_count": following_count,
            "stories_count": stories_count,
            "is_following": is_following
        })
    
    return result

@router.get("/suggestions", response_model=List[UserResponse])
def get_follow_suggestions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Fetching follow suggestions for user {current_user.username}")
    
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
        followers_count = db.query(Follow).filter(
            Follow.following_id == user.id,
            Follow.is_active == True
        ).count()
        
        following_count = db.query(Follow).filter(
            Follow.follower_id == user.id,
            Follow.is_active == True
        ).count()
        
        stories_count = db.query(Story).filter(
            Story.user_id == user.id,
            Story.is_published == True
        ).count()
        
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "created_at": user.created_at,
            "followers_count": followers_count,
            "following_count": following_count,
            "stories_count": stories_count,
            "is_following": False
        })
    
    return result

@router.get("/{username}", response_model=UserProfileResponse)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Fetching user with username: {username}")
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"User not found: {username}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User found: {user.id}, {user.username}")
        
        followers_count = db.query(Follow).filter(
            Follow.following_id == user.id,
            Follow.is_active == True
        ).count()
        
        following_count = db.query(Follow).filter(
            Follow.follower_id == user.id,
            Follow.is_active == True
        ).count()
        
        stories_count = db.query(Story).filter(
            Story.user_id == user.id,
            Story.is_published == True
        ).count()
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "created_at": user.created_at,
            "followers_count": followers_count,
            "following_count": following_count,
            "stories_count": stories_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{username}/stories", response_model=List[UserStoryResponse])
def get_user_stories(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
        has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
        story_type = story.story_type

        if has_nodes and story_type != 'interactive':
            story_type = 'interactive'
            story.story_type = 'interactive'
        elif not has_nodes and story_type != 'written':
            story_type = 'written'
            story.story_type = 'written'
        
        result.append({
            "id": story.id,
            "title": story.title,
            "excerpt": story.excerpt,
            "cover_image": story.cover_image,
            "created_at": story.created_at,
            "like_count": len(story.likes),
            "comment_count": len(story.comments),
            "view_count": len(story.views),
            "story_type": story_type
        })
    
    db.commit()  
    return result

@router.get("/{username}/followers")
def get_user_followers(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
            "username": follower.username,
            "full_name": follower.full_name,
            "avatar_url": follower.avatar_url,
            "bio": follower.bio,
            "followed_at": follow.created_at,
            "is_following": is_following
        })
    
    return result

@router.get("/{username}/following")
def get_user_following(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = db.query(Follow).filter(
        Follow.follower_id == user.id,
        Follow.is_active == True
    ).order_by(desc(Follow.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for follow in following:
        followed = follow.following
        is_following = False
        if current_user:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user.id,
                Follow.following_id == followed.id,
                Follow.is_active == True
            ).first() is not None
        
        result.append({
            "id": followed.id,
            "username": followed.username,
            "full_name": followed.full_name,
            "avatar_url": followed.avatar_url,
            "bio": followed.bio,
            "followed_at": follow.created_at,
            "is_following": is_following
        })
    
    return result

@router.get("/{username}/stats")
def get_user_stats(
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
            Follow.follower_id == current_user.id,
            Follow.following_id == user.id,
            Follow.is_active == True
        ).first() is not None
        
        is_follower = db.query(Follow).filter(
            Follow.follower_id == user.id,
            Follow.following_id == current_user.id,
            Follow.is_active == True
        ).first() is not None
    
    return {
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
        "is_follower": is_follower
    }

@router.post("/{username}/follow")
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
        Follow.follower_id == current_user.id,
        Follow.following_id == user_to_follow.id
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
    else:
        new_follow = Follow(
            follower_id=current_user.id,
            following_id=user_to_follow.id,
            is_active=True
        )
        db.add(new_follow)
        message = f"Following {username}"
        is_following = True
    
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

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    allowed_fields = ["full_name", "bio", "email", "avatar_url"]
    
    for key, value in user_update.items():
        if key in allowed_fields and value is not None:
            setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/count")
def get_user_count(db: Session = Depends(get_db)):
    count = db.query(User).count()
    return {"total": count}

@router.get("/debug/{username}/stories")
def debug_user_stories(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stories = db.query(Story).filter(
        Story.user_id == user.id,
        Story.is_published == True
    ).all()
    
    result = []
    for story in stories:
        result.append({
            "id": story.id,
            "title": story.title,
            "story_type": story.story_type,
            "has_nodes": len(story.nodes) > 0 if hasattr(story, 'nodes') else False
        })
    
    return result

@router.get("/id/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.id == user_id).first()
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
    
    stories_count = db.query(Story).filter(
        Story.user_id == user.id,
        Story.is_published == True
    ).count()
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "created_at": user.created_at,
        "followers_count": followers_count,
        "following_count": following_count,
        "stories_count": stories_count
    }
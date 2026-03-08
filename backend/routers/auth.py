from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import Annotated, Optional
import logging
import re

from db.database import get_db, settings
from db import helpers
from core.auth import get_password_hash, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

def validate_password(password: str) -> Optional[str]:
    """Validate password strength and return error message if invalid"""
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"
    return None

def validate_email(email: str) -> Optional[str]:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return "Invalid email format"
    return None

def validate_username(username: str) -> Optional[str]:
    """Validate username"""
    if len(username) < 3:
        return "Username must be at least 3 characters long"
    if len(username) > 30:
        return "Username must be less than 30 characters"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "Username can only contain letters, numbers, and underscores"
    return None

@router.post("/register", response_model=dict)
def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None)
):
    logger.info(f"Registration attempt for username: {username}, email: {email}")
    
    # Validate inputs
    username_error = validate_username(username)
    if username_error:
        raise HTTPException(status_code=400, detail={
            "field": "username",
            "message": username_error
        })
    
    email_error = validate_email(email)
    if email_error:
        raise HTTPException(status_code=400, detail={
            "field": "email",
            "message": email_error
        })
    
    password_error = validate_password(password)
    if password_error:
        raise HTTPException(status_code=400, detail={
            "field": "password",
            "message": password_error
        })
    
    try:
        if settings.USE_TURSO:
            # Check if user exists
            existing = helpers.get_user_by_username(username)
            if existing:
                raise HTTPException(status_code=400, detail={
                    "field": "username",
                    "message": "Username already registered"
                })
            
            existing_email = helpers.get_user_by_email(email)
            if existing_email:
                raise HTTPException(status_code=400, detail={
                    "field": "email",
                    "message": "Email already registered"
                })
            
            # Create user
            hashed_password = get_password_hash(password)
            user_data = {
                "username": username,
                "email": email,
                "full_name": full_name or username,
                "password_hash": hashed_password,
                "bio": "",
                "avatar_url": "",
                "is_active": True
            }
            
            user = helpers.create_user(user_data)
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create user")
            
            logger.info(f"User registered successfully: {username}")
            return user
        
        else:
            from sqlalchemy.orm import Session
            from models.user import User
            
            db = next(get_db())
            
            db_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if db_user:
                field = "username" if db_user.username == username else "email"
                raise HTTPException(status_code=400, detail={
                    "field": field,
                    "message": f"{field.capitalize()} already registered"
                })
            
            hashed_password = get_password_hash(password)
            db_user = User(
                email=email,
                username=username,
                full_name=full_name,
                hashed_password=hashed_password
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User registered successfully in SQLite: {username}")
            return db_user
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={
            "field": "general",
            "message": "Internal server error during registration"
        })

@router.post("/login", response_model=dict)
def login(
    user_data: Optional[dict] = None,
    username: Annotated[Optional[str], Form()] = None,
    password: Annotated[Optional[str], Form()] = None
):
    if user_data:
        input_username = user_data.get("username")
        input_password = user_data.get("password")
    elif username and password:
        input_username = username
        input_password = password
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "field": "general",
                "message": "Username and password are required"
            }
        )
    
    if not input_username or not input_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "field": "general",
                "message": "Username and password are required"
            }
        )
    
    logger.info(f"Login attempt for: {input_username}")
    
    try:
        if settings.USE_TURSO:
            user = helpers.get_user_by_username(input_username)
            if not user:
                user = helpers.get_user_by_email(input_username)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "field": "username",
                        "message": "User not found"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not verify_password(input_password, user.get("password_hash", "")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "field": "password",
                        "message": "Incorrect password"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "field": "general",
                        "message": "User account is inactive"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token = create_access_token(data={"sub": user["username"]})
            logger.info(f"Login successful: {input_username}")
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        
        else:
            from sqlalchemy.orm import Session
            from models.user import User
            
            db = next(get_db())
            
            user = db.query(User).filter(
                (User.username == input_username) | (User.email == input_username)
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "field": "username",
                        "message": "User not found"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not verify_password(input_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "field": "password",
                        "message": "Incorrect password"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token = create_access_token(data={"sub": user.username})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "created_at": user.created_at
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "field": "general",
                "message": "Login failed due to server error"
            }
        )

@router.get("/me", response_model=dict)
def read_users_me(current_user = Depends(get_current_active_user)):
    if settings.USE_TURSO:
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "bio": current_user.bio,
            "avatar_url": current_user.avatar_url,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at
        }
    else:
        return current_user
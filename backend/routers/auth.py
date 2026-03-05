from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import Annotated, Optional
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_password_hash, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=dict)
def register(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None)
):
    logger.info(f"📝 Registering new user: {username}")
    
    try:
        if settings.USE_TURSO:
            # Check if user exists
            existing = helpers.get_user_by_username(username)
            if existing:
                raise HTTPException(status_code=400, detail="Username already registered")
            
            existing_email = helpers.get_user_by_email(email)
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already registered")
            
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
            
            return user
        else:
            pass
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @router.post("/register", response_model=dict)
# def register(
#     email: str = Form(...),
#     username: str = Form(...),
#     password: str = Form(...),
#     full_name: Optional[str] = Form(None)
# ):
#     logger.info(f"📝 Registering new user: {username}")
    
#     if settings.USE_TURSO:
#         existing = helpers.get_user_by_username(username)
#         if existing:
#             raise HTTPException(status_code=400, detail="Username already registered")
        
#         existing_email = helpers.get_user_by_email(email)
#         if existing_email:
#             raise HTTPException(status_code=400, detail="Email already registered")
        
#         hashed_password = get_password_hash(password)
#         user_data = {
#             "username": username,
#             "email": email,
#             "full_name": full_name or username,
#             "password_hash": hashed_password,
#             "bio": "",
#             "avatar_url": "",
#             "is_active": True
#         }
        
#         user = helpers.create_user(user_data)
#         if not user:
#             raise HTTPException(status_code=500, detail="Failed to create user")
        
#         logger.info(f"✅ User registered in Turso: {username}")
#         return user
    
#     else:
#         from sqlalchemy.orm import Session
#         from models.user import User
        
#         db = next(get_db())
        
#         db_user = db.query(User).filter(
#             (User.username == username) | (User.email == email)
#         ).first()
#         if db_user:
#             raise HTTPException(status_code=400, detail="Username or email already registered")
        
#         hashed_password = get_password_hash(password)
#         db_user = User(
#             email=email,
#             username=username,
#             full_name=full_name,
#             hashed_password=hashed_password
#         )
#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
        
#         return db_user

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
            detail="Invalid login format. Provide username and password either as JSON or form data."
        )
    
    logger.info(f"🔑 Login attempt for: {input_username}")
    
    if settings.USE_TURSO:
        user = helpers.get_user_by_username(input_username)
        if not user:
            user = helpers.get_user_by_email(input_username)
        
        if not user or not verify_password(input_password, user.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user["username"]})
        logger.info(f"✅ Login successful: {input_username}")
        return {"access_token": access_token, "token_type": "bearer", "user": user}
    
    else:
        from sqlalchemy.orm import Session
        from models.user import User
        
        db = next(get_db())
        
        user = db.query(User).filter(
            (User.username == input_username) | (User.email == input_username)
        ).first()
        
        if not user or not verify_password(input_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=dict)
def read_users_me(current_user = Depends(get_current_active_user)):
    if settings.USE_TURSO:
        return current_user
    else:
        return current_user
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db, settings as db_settings
from db import helpers
from models.user import User
from core.config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserObject:
    """Simple class to make dict users work like SQLAlchemy objects"""
    def __init__(self, user_dict):
        self.id = user_dict.get('id')
        self.username = user_dict.get('username')
        self.email = user_dict.get('email')
        self.full_name = user_dict.get('full_name')
        self.bio = user_dict.get('bio')
        self.avatar_url = user_dict.get('avatar_url')
        self.is_active = user_dict.get('is_active', True)
        self.created_at = user_dict.get('created_at')
    
    def __getattr__(self, name):
        return None
    
    def get(self, key, default=None):
        """Dict-like get method for backward compatibility"""
        return getattr(self, key, default)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        logger.warning("No token provided")
        return None
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("No username in token payload")
            raise credentials_exception
        
        logger.info(f"Token decoded successfully for user: {username}")
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception
  
    if db_settings.USE_TURSO:
        user_dict = helpers.get_user_by_username(username)
        if user_dict is None:
            logger.warning(f"User not found in Turso: {username}")
            raise credentials_exception
        
        user = UserObject(user_dict)
        logger.info(f"User found in Turso: {user.username}")
        return user
    else:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User not found in SQLite: {username}")
            raise credentials_exception
        logger.info(f"User found in SQLite: {user.username}")
        return user

async def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user but return None if no token or invalid token"""
    if token is None:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    if db_settings.USE_TURSO:
        user_dict = helpers.get_user_by_username(username)
        if user_dict is None:
            return None
        return UserObject(user_dict)
    else:
        return db.query(User).filter(User.username == username).first()

async def get_current_active_user(current_user = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user
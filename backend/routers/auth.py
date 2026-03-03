from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from schemas.auth import UserCreate, UserResponse, Token, UserLogin
from core.auth import get_password_hash, verify_password, create_access_token, get_current_active_user
from typing import Annotated, Optional

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(

    user_data: Optional[UserLogin] = None,

    username: Annotated[Optional[str], Form()] = None,
    password: Annotated[Optional[str], Form()] = None,
    db: Session = Depends(get_db)
):
    
    if user_data:
        input_username = user_data.username
        input_password = user_data.password

    elif username and password:
        input_username = username
        input_password = password
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid login format. Provide username and password either as JSON or form data."
        )
    

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

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
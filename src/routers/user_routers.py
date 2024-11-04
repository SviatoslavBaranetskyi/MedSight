from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas.user_schemas import UserCreate, UserResponse, UserLogin, UserPasswordUpdate
from src.services.user_service import create_user, authenticate_user, get_user
from src.utils.auth_utils import create_access_token, get_current_user, get_password_hash

router = APIRouter(prefix="/auth", tags=["Authorization management"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    create_user(user_data, db)
    return {"message": "User registered successfully"}


@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.username})
    return {"message": "Login successful", "access_token": access_token, "token_type": "Bearer"}


@router.get("/profile", response_model=UserResponse)
def read_profile(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post("/profile", response_model=UserResponse)
def update_password(new_password: UserPasswordUpdate, current_user: UserResponse = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    db_user = get_user(db, current_user.username)
    db_user.hashed_password = get_password_hash(new_password.new_password)
    db.commit()
    return db_user

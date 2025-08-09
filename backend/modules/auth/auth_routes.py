from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.models.database import User
from backend.models.engine import db_session
from backend.modules.auth import auth_methods
from backend.modules.auth.auth_schema import LoginResponse, LoginUser, RegisterResponse, RegisterUser

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user: RegisterUser, db: Session = Depends(db_session)):
    try:
        user.password = auth_methods.hash_password(user.password)
        new_user = User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User {new_user.email} registered successfully")
        return new_user
    except IntegrityError:
        logger.error(f"Email {user.email} already registered")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        logger.error(f"Error registering user {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/login", response_model=LoginResponse)
async def login(user: LoginUser, db: Session = Depends(db_session)):
    statement = select(User).where(User.email == user.email)
    result = db.exec(statement)
    db_user = result.first()

    if not db_user:
        logger.error(f"User {user.email} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    if not auth_methods.verify_password(user.password, db_user.password):
        logger.error(f"User {user.email} password not valid")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth_methods.create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

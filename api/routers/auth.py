"""
CE365 Agent - Auth Router
Authentication & User Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from api.models import get_db, User
from api.schemas import UserCreate, UserLogin, UserResponse, Token
from api.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user

    Community Edition: Nur 1 User erlaubt
    """
    from api.config import settings

    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check user limit (Edition)
    if settings.max_users == 1:
        result = await db.execute(select(User))
        user_count = len(result.scalars().all())

        if user_count >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User limit reached for {settings.edition} edition"
            )

    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        company=user_data.company,
        is_admin=False  # First user wird später automatisch Admin
    )

    # First user wird Admin
    result = await db.execute(select(User))
    user_count = len(result.scalars().all())
    if user_count == 0:
        user.is_admin = True

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create token
    access_token = create_access_token(user.id)

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create token
    access_token = create_access_token(user.id)

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout():
    """
    Logout user

    JWT ist stateless, daher nur Client-Side Token löschen
    """
    return {"message": "Logged out successfully"}

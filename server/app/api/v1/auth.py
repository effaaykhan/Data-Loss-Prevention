"""
Authentication API Endpoints
User login, registration, token refresh
"""

from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
    decode_token,
    get_current_user,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.cache import get_cache
from app.services.user_service import UserService
from app.services.blacklist_service import TokenBlacklistService
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user
    """
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters "
                   "and contain uppercase, lowercase, digit, and special character",
        )

    # Create user service
    user_service = UserService(db)

    try:
        # Create user in database
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            organization=user_data.organization,
            role="VIEWER",  # Default role for new users
        )

        logger.info("User registered", email=user.email, user_id=str(user.id))

        return {
            "message": "User registered successfully",
            "email": user.email,
            "user_id": str(user.id),
        }

    except ValueError as e:
        # User already exists or other validation error
        logger.warning("Registration failed", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    User login with email and password
    Returns access and refresh tokens
    """
    # Create user service
    user_service = UserService(db)

    # Authenticate user
    user = await user_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )

    if not user:
        logger.warning("Login failed - invalid credentials", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
        }
    )

    logger.info("User logged in", email=user.email, user_id=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        payload = decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Create new tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
            }
        )

        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "email": user.email,
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    User logout
    """
    token = request.headers["authorization"].split(" ")[1]
    cache = get_cache()
    blacklist_service = TokenBlacklistService(cache)
    payload = decode_token(token)
    expires_in = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    await blacklist_service.add_to_blacklist(token, expires_in)
    logger.info("User logged out", email=current_user.email)
    return {"message": "Logged out successfully"}

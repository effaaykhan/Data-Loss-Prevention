"""
Security and Authentication
JWT tokens, password hashing, OAuth2
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.cache import get_cache
from app.services.blacklist_service import TokenBlacklistService
from app.models.user import User
# UserService imported lazily to avoid circular imports

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate password hash
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("Token decode failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token
    """
    # Lazy import to avoid circular dependency
    from app.services.user_service import UserService

    try:
        cache = get_cache()
        blacklist_service = TokenBlacklistService(cache)
        if await blacklist_service.is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
    except RuntimeError:
        # Redis not initialized, skip blacklist check (development mode)
        logger.warning("Redis not initialized, skipping token blacklist check")

    payload = decode_token(token)

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def optional_auth(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication for endpoints that can work with or without auth
    (e.g., agent endpoints that don't require authentication)

    Returns user dict if authenticated, None otherwise
    """
    # Lazy import to avoid circular dependency
    from app.services.user_service import UserService

    if not token:
        return None

    try:
        # Check blacklist
        try:
            cache = get_cache()
            blacklist_service = TokenBlacklistService(cache)
            if await blacklist_service.is_blacklisted(token):
                return None
        except RuntimeError:
            # Redis not initialized, skip blacklist check
            pass

        # Decode token
        payload = decode_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            return None

        # Get user
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)

        if user is None:
            return None

        # Return user as dict
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }

    except Exception as e:
        # If any error occurs, just return None (no auth)
        logger.debug("Optional auth failed, continuing without auth", error=str(e))
        return None


def require_role(required_role: str):
    """
    Dependency factory to check user role
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role

        # Role hierarchy: ADMIN > ANALYST > VIEWER
        role_hierarchy = {"ADMIN": 3, "ANALYST": 2, "VIEWER": 1}
        
        # Convert role to string if it's an enum
        user_role_str = str(user_role) if hasattr(user_role, 'value') else user_role
        required_role_str = required_role.upper() if isinstance(required_role, str) else str(required_role)

        user_level = role_hierarchy.get(user_role_str, 0)
        required_level = role_hierarchy.get(required_role_str, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    return has_upper and has_lower and has_digit and has_special

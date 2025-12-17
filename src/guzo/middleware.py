"""Shared middleware and dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from src.guzo.auth.core import User, UserRole
from src.guzo.auth.service import AuthService


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_token_from_cookie_or_header(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[str]:
    """Get token from Authorization header or cookie."""
    if token:
        return token
    if access_token:
        return access_token
    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_cookie_or_header),
) -> Optional[User]:
    """Get current user from token (returns None if not authenticated)."""
    if not token:
        return None
    
    token_data = AuthService.decode_token(token)
    if not token_data or not token_data.user_id:
        return None
    
    user = await AuthService.get_user_by_id(token_data.user_id)
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Get current user (raises 401 if not authenticated)."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


async def get_current_rider(
    user: User = Depends(get_current_user_required),
) -> User:
    """Get current user and verify they are a rider."""
    if user.role not in [UserRole.RIDER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Rider access required.",
        )
    return user


async def get_current_driver(
    user: User = Depends(get_current_user_required),
) -> User:
    """Get current user and verify they are a driver."""
    if user.role not in [UserRole.DRIVER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Driver access required.",
        )
    return user


async def get_current_admin(
    user: User = Depends(get_current_user_required),
) -> User:
    """Get current user and verify they are an admin."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin access required.",
        )
    return user


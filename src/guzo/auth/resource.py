"""Auth domain resource - API routes for authentication."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.guzo.auth.core import User, UserCreate, UserResponse, Token
from src.guzo.auth.service import AuthService
from src.guzo.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        user = await AuthService.create_user(user_data)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_online=user.is_online,
            rating=user.rating,
            language=user.language,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/token", response_model=Token)
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login."""
    user = await AuthService.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_online=user.is_online,
        rating=user.rating,
        language=user.language,
        created_at=user.created_at,
    )

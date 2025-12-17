"""Auth domain resource - API routes for authentication."""

from fastapi import APIRouter, HTTPException, status, Response, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from src.guzo.auth.core import User, UserRole, UserCreate, UserResponse, Token
from src.guzo.auth.service import AuthService
from src.guzo.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user (JSON API)."""
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


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    """Login with email and password (form submission)."""
    user = await AuthService.authenticate_user(email, password)
    if not user:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                '<div class="alert alert-error">Invalid email or password</div>',
                status_code=400,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    
    # Determine redirect based on role
    redirect_url = "/customer"
    if user.role == UserRole.DRIVER:
        redirect_url = "/driver"
    elif user.role == UserRole.ADMIN:
        redirect_url = "/admin"
    
    if request.headers.get("HX-Request"):
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = redirect_url
    else:
        response = RedirectResponse(url=redirect_url, status_code=303)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return response


@router.post("/signup")
async def signup(
    request: Request,
    response: Response,
    email: str = Form(...),
    phone: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(default="rider"),
):
    """Register a new user (form submission)."""
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.RIDER
    
    user_data = UserCreate(
        email=email,
        phone=phone,
        full_name=full_name,
        password=password,
        role=user_role,
    )
    
    try:
        user = await AuthService.create_user(user_data)
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    
    redirect_url = "/customer"
    if user.role == UserRole.DRIVER:
        redirect_url = "/driver"
    elif user.role == UserRole.ADMIN:
        redirect_url = "/admin"
    
    if request.headers.get("HX-Request"):
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = redirect_url
    else:
        response = RedirectResponse(url=redirect_url, status_code=303)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    if request.headers.get("HX-Request"):
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = "/"
    else:
        response = RedirectResponse(url="/", status_code=303)
    
    response.delete_cookie(key="access_token")
    return response


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


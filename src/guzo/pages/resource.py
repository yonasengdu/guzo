"""Pages resource - public and static pages."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user
from src.guzo.trips.service import TripService

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("/", response_class=HTMLResponse)
async def landing_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Landing page - redirects authenticated users to their dashboard."""
    # Redirect authenticated users to their role-specific dashboard
    if user:
        if user.role == UserRole.DRIVER:
            return RedirectResponse(url="/driver", status_code=303)
        elif user.role == UserRole.ADMIN:
            return RedirectResponse(url="/admin", status_code=303)
        return RedirectResponse(url="/customer", status_code=303)
    
    # Show landing page for unauthenticated users
    trips = await TripService.get_upcoming_trips(limit=6)
    
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "user": user,
            "trips": trips,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Login page."""
    if user:
        if user.role == UserRole.DRIVER:
            return RedirectResponse(url="/driver", status_code=303)
        elif user.role == UserRole.ADMIN:
            return RedirectResponse(url="/admin", status_code=303)
        return RedirectResponse(url="/customer", status_code=303)
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "user": None},
    )


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Signup page."""
    if user:
        if user.role == UserRole.DRIVER:
            return RedirectResponse(url="/driver", status_code=303)
        elif user.role == UserRole.ADMIN:
            return RedirectResponse(url="/admin", status_code=303)
        return RedirectResponse(url="/customer", status_code=303)
    
    return templates.TemplateResponse(
        "auth/signup.html",
        {"request": request, "user": None},
    )


@router.get("/offline", response_class=HTMLResponse)
async def offline_page(request: Request):
    """Offline fallback page for PWA."""
    return templates.TemplateResponse(
        "offline.html",
        {"request": request},
    )


"""Favorites resource - API routes for favorites."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.guzo.auth.core import User
from src.guzo.middleware import get_current_user
from src.guzo.favorites.core import FavoriteRouteCreate, FavoriteDriverCreate
from src.guzo.favorites.service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["Favorites"])
templates = Jinja2Templates(directory="src/guzo/templates")


# ============== Routes ==============

@router.get("/routes", response_class=HTMLResponse)
async def get_favorite_routes(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Get user's favorite routes."""
    routes = await FavoriteService.get_user_routes(str(user.id))
    
    return templates.TemplateResponse(
        "partials/favorite_routes.html",
        {
            "request": request,
            "routes": routes,
            "user": user,
        },
    )


@router.post("/routes", response_class=HTMLResponse)
async def add_favorite_route(
    request: Request,
    user: User = Depends(get_current_user),
    origin: str = Form(...),
    destination: str = Form(...),
):
    """Add a route to favorites."""
    data = FavoriteRouteCreate(origin=origin, destination=destination)
    route = await FavoriteService.add_favorite_route(str(user.id), data)
    
    if route:
        return templates.TemplateResponse(
            "partials/favorite_route_item.html",
            {
                "request": request,
                "route": route,
            },
        )
    
    return HTMLResponse('<span class="text-apple-gray-500">Already saved</span>')


@router.delete("/routes/{route_id}", response_class=HTMLResponse)
async def remove_favorite_route(
    request: Request,
    route_id: str,
    user: User = Depends(get_current_user),
):
    """Remove a route from favorites."""
    success = await FavoriteService.remove_favorite_route(str(user.id), route_id)
    
    if success:
        return HTMLResponse('')
    
    return templates.TemplateResponse(
        "partials/error.html",
        {
            "request": request,
            "message": "Could not remove route",
        },
        status_code=400,
    )


# ============== Drivers ==============

@router.get("/drivers", response_class=HTMLResponse)
async def get_favorite_drivers(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Get user's favorite drivers."""
    drivers = await FavoriteService.get_user_favorite_drivers(str(user.id))
    
    return templates.TemplateResponse(
        "partials/favorite_drivers.html",
        {
            "request": request,
            "drivers": drivers,
            "user": user,
        },
    )


@router.post("/drivers", response_class=HTMLResponse)
async def add_favorite_driver(
    request: Request,
    user: User = Depends(get_current_user),
    driver_id: str = Form(...),
    note: Optional[str] = Form(None),
):
    """Add a driver to favorites."""
    data = FavoriteDriverCreate(driver_id=driver_id, note=note)
    favorite = await FavoriteService.add_favorite_driver(str(user.id), data)
    
    if favorite:
        return HTMLResponse(
            '<button class="text-red-500 hover:text-red-600" '
            f'hx-delete="/favorites/drivers/{driver_id}" '
            'hx-swap="outerHTML">'
            '♥ Favorited</button>'
        )
    
    return HTMLResponse('<span class="text-apple-gray-500">Already favorited</span>')


@router.delete("/drivers/{driver_id}", response_class=HTMLResponse)
async def remove_favorite_driver(
    request: Request,
    driver_id: str,
    user: User = Depends(get_current_user),
):
    """Remove a driver from favorites."""
    success = await FavoriteService.remove_favorite_driver(str(user.id), driver_id)
    
    if success:
        return HTMLResponse(
            '<button class="text-apple-gray-400 hover:text-red-500" '
            f'hx-post="/favorites/drivers" '
            f'hx-vals=\'{{"driver_id": "{driver_id}"}}\' '
            'hx-swap="outerHTML">'
            '♡ Add to favorites</button>'
        )
    
    return templates.TemplateResponse(
        "partials/error.html",
        {
            "request": request,
            "message": "Could not remove driver",
        },
        status_code=400,
    )


@router.post("/drivers/{driver_id}/toggle", response_class=HTMLResponse)
async def toggle_favorite_driver(
    request: Request,
    driver_id: str,
    user: User = Depends(get_current_user),
):
    """Toggle favorite status for a driver."""
    is_fav, was_added = await FavoriteService.toggle_favorite_driver(
        str(user.id), driver_id
    )
    
    if is_fav:
        return HTMLResponse(
            f'<button class="text-red-500 hover:text-red-600 transition-colors" '
            f'hx-post="/favorites/drivers/{driver_id}/toggle" '
            'hx-swap="outerHTML">'
            '<svg class="w-5 h-5 fill-current" viewBox="0 0 20 20">'
            '<path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"/>'
            '</svg></button>'
        )
    else:
        return HTMLResponse(
            f'<button class="text-apple-gray-400 hover:text-red-500 transition-colors" '
            f'hx-post="/favorites/drivers/{driver_id}/toggle" '
            'hx-swap="outerHTML">'
            '<svg class="w-5 h-5 stroke-current fill-none" viewBox="0 0 20 20">'
            '<path stroke-width="1.5" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"/>'
            '</svg></button>'
        )


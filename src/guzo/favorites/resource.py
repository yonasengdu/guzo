"""Favorites resource - API routes for favorites."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.guzo.auth.core import User
from src.guzo.middleware import get_current_user
from src.guzo.favorites.core import (
    FavoriteRouteCreate,
    FavoriteRouteResponse,
    FavoriteDriverCreate,
    FavoriteDriverResponse,
)
from src.guzo.favorites.service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["Favorites"])


# ============== Request/Response Models ==============

class ToggleFavoriteResponse(BaseModel):
    """Response for toggle favorite endpoint."""
    is_favorite: bool
    was_added: bool


class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"


# ============== Routes ==============

@router.get("/routes", response_model=list[FavoriteRouteResponse])
async def get_favorite_routes(user: User = Depends(get_current_user)):
    """Get user's favorite routes."""
    routes = await FavoriteService.get_user_routes(str(user.id))
    return [
        FavoriteRouteResponse(
            id=str(r.id),
            user_id=r.user_id,
            origin=r.origin,
            destination=r.destination,
            use_count=r.use_count,
            last_used=r.last_used,
            created_at=r.created_at,
        )
        for r in routes
    ]


@router.post("/routes", response_model=FavoriteRouteResponse)
async def add_favorite_route(
    data: FavoriteRouteCreate,
    user: User = Depends(get_current_user),
):
    """Add a route to favorites."""
    route = await FavoriteService.add_favorite_route(str(user.id), data)
    
    if not route:
        raise HTTPException(status_code=409, detail="Route already saved")
    
    return FavoriteRouteResponse(
        id=str(route.id),
        user_id=route.user_id,
        origin=route.origin,
        destination=route.destination,
        use_count=route.use_count,
        last_used=route.last_used,
        created_at=route.created_at,
    )


@router.delete("/routes/{route_id}", response_model=DeleteResponse)
async def remove_favorite_route(
    route_id: str,
    user: User = Depends(get_current_user),
):
    """Remove a route from favorites."""
    success = await FavoriteService.remove_favorite_route(str(user.id), route_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Could not remove route")
    
    return DeleteResponse()


# ============== Drivers ==============

@router.get("/drivers", response_model=list[FavoriteDriverResponse])
async def get_favorite_drivers(user: User = Depends(get_current_user)):
    """Get user's favorite drivers."""
    drivers = await FavoriteService.get_user_favorite_drivers(str(user.id))
    return [
        FavoriteDriverResponse(
            id=str(d.id),
            user_id=d.user_id,
            driver_id=d.driver_id,
            driver_name=getattr(d, 'driver_name', None),
            driver_rating=getattr(d, 'driver_rating', None),
            driver_phone=getattr(d, 'driver_phone', None),
            note=d.note,
            created_at=d.created_at,
        )
        for d in drivers
    ]


@router.post("/drivers", response_model=FavoriteDriverResponse)
async def add_favorite_driver(
    data: FavoriteDriverCreate,
    user: User = Depends(get_current_user),
):
    """Add a driver to favorites."""
    favorite = await FavoriteService.add_favorite_driver(str(user.id), data)
    
    if not favorite:
        raise HTTPException(status_code=409, detail="Driver already favorited")
    
    return FavoriteDriverResponse(
        id=str(favorite.id),
        user_id=favorite.user_id,
        driver_id=favorite.driver_id,
        note=favorite.note,
        created_at=favorite.created_at,
    )


@router.delete("/drivers/{driver_id}", response_model=DeleteResponse)
async def remove_favorite_driver(
    driver_id: str,
    user: User = Depends(get_current_user),
):
    """Remove a driver from favorites."""
    success = await FavoriteService.remove_favorite_driver(str(user.id), driver_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Could not remove driver")
    
    return DeleteResponse()


@router.patch("/drivers/{driver_id}/toggle", response_model=ToggleFavoriteResponse)
async def toggle_favorite_driver(
    driver_id: str,
    user: User = Depends(get_current_user),
):
    """Toggle favorite status for a driver."""
    is_fav, was_added = await FavoriteService.toggle_favorite_driver(
        str(user.id), driver_id
    )
    
    return ToggleFavoriteResponse(is_favorite=is_fav, was_added=was_added)

"""Favorites service - Business logic for favorites."""

from typing import Optional

from src.guzo.auth.core import User
from src.guzo.favorites.core import (
    FavoriteRoute,
    FavoriteDriver,
    FavoriteRouteCreate,
    FavoriteDriverCreate,
    FavoriteRouteResponse,
    FavoriteDriverResponse,
)
from src.guzo.favorites.repository import (
    FavoriteRouteRepository,
    FavoriteDriverRepository,
)


class FavoriteService:
    """Service for favorites business logic."""
    
    # ============== Routes ==============
    
    @staticmethod
    async def add_favorite_route(
        user_id: str,
        data: FavoriteRouteCreate,
    ) -> Optional[FavoriteRoute]:
        """Add a route to favorites."""
        # Check if already exists
        existing = await FavoriteRouteRepository.find_existing(
            user_id, data.origin, data.destination
        )
        if existing:
            return existing
        
        route = FavoriteRoute(
            user_id=user_id,
            origin=data.origin,
            destination=data.destination,
        )
        
        return await FavoriteRouteRepository.create(route)
    
    @staticmethod
    async def get_user_routes(user_id: str) -> list[FavoriteRouteResponse]:
        """Get all favorite routes for a user."""
        routes = await FavoriteRouteRepository.get_user_routes(user_id)
        
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
    
    @staticmethod
    async def remove_favorite_route(user_id: str, route_id: str) -> bool:
        """Remove a route from favorites."""
        route = await FavoriteRouteRepository.get_by_id(route_id)
        if route and route.user_id == user_id:
            return await FavoriteRouteRepository.delete(route_id)
        return False
    
    @staticmethod
    async def record_route_use(user_id: str, origin: str, destination: str) -> None:
        """Record that a route was used (for auto-favorites or tracking)."""
        route = await FavoriteRouteRepository.find_existing(user_id, origin, destination)
        if route:
            await FavoriteRouteRepository.increment_use(str(route.id))
    
    # ============== Drivers ==============
    
    @staticmethod
    async def add_favorite_driver(
        user_id: str,
        data: FavoriteDriverCreate,
    ) -> Optional[FavoriteDriver]:
        """Add a driver to favorites."""
        # Check if already exists
        existing = await FavoriteDriverRepository.find_existing(
            user_id, data.driver_id
        )
        if existing:
            return existing
        
        favorite = FavoriteDriver(
            user_id=user_id,
            driver_id=data.driver_id,
            note=data.note,
        )
        
        return await FavoriteDriverRepository.create(favorite)
    
    @staticmethod
    async def get_user_favorite_drivers(user_id: str) -> list[FavoriteDriverResponse]:
        """Get all favorite drivers for a user with driver info."""
        from beanie import PydanticObjectId
        
        favorites = await FavoriteDriverRepository.get_user_favorites(user_id)
        
        responses = []
        for fav in favorites:
            driver = await User.get(PydanticObjectId(fav.driver_id))
            
            responses.append(FavoriteDriverResponse(
                id=str(fav.id),
                user_id=fav.user_id,
                driver_id=fav.driver_id,
                driver_name=driver.full_name if driver else "Unknown",
                driver_rating=driver.rating if driver else None,
                driver_phone=driver.phone if driver else None,
                note=fav.note,
                created_at=fav.created_at,
            ))
        
        return responses
    
    @staticmethod
    async def remove_favorite_driver(user_id: str, driver_id: str) -> bool:
        """Remove a driver from favorites."""
        return await FavoriteDriverRepository.delete_by_user_and_driver(
            user_id, driver_id
        )
    
    @staticmethod
    async def is_favorite_driver(user_id: str, driver_id: str) -> bool:
        """Check if a driver is favorited by user."""
        return await FavoriteDriverRepository.is_favorite(user_id, driver_id)
    
    @staticmethod
    async def toggle_favorite_driver(
        user_id: str,
        driver_id: str,
    ) -> tuple[bool, bool]:
        """Toggle favorite status for a driver. Returns (is_now_favorite, was_added)."""
        is_fav = await FavoriteDriverRepository.is_favorite(user_id, driver_id)
        
        if is_fav:
            await FavoriteDriverRepository.delete_by_user_and_driver(user_id, driver_id)
            return False, False
        else:
            favorite = FavoriteDriver(
                user_id=user_id,
                driver_id=driver_id,
            )
            await FavoriteDriverRepository.create(favorite)
            return True, True


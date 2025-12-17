"""Favorites repository - Database operations for favorites."""

from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId

from src.guzo.favorites.core import FavoriteRoute, FavoriteDriver


class FavoriteRouteRepository:
    """Repository for favorite route database operations."""
    
    @staticmethod
    async def create(route: FavoriteRoute) -> FavoriteRoute:
        """Create a new favorite route."""
        await route.insert()
        return route
    
    @staticmethod
    async def get_by_id(route_id: str) -> Optional[FavoriteRoute]:
        """Get favorite route by ID."""
        return await FavoriteRoute.get(PydanticObjectId(route_id))
    
    @staticmethod
    async def get_user_routes(user_id: str) -> list[FavoriteRoute]:
        """Get all favorite routes for a user."""
        return await FavoriteRoute.find(
            FavoriteRoute.user_id == user_id
        ).sort(-FavoriteRoute.use_count).to_list()
    
    @staticmethod
    async def find_existing(
        user_id: str, origin: str, destination: str
    ) -> Optional[FavoriteRoute]:
        """Find if a route already exists for user."""
        return await FavoriteRoute.find_one(
            FavoriteRoute.user_id == user_id,
            FavoriteRoute.origin == origin,
            FavoriteRoute.destination == destination,
        )
    
    @staticmethod
    async def increment_use(route_id: str) -> Optional[FavoriteRoute]:
        """Increment use count and update last used."""
        route = await FavoriteRoute.get(PydanticObjectId(route_id))
        if route:
            route.use_count += 1
            route.last_used = datetime.utcnow()
            await route.save()
        return route
    
    @staticmethod
    async def delete(route_id: str) -> bool:
        """Delete a favorite route."""
        route = await FavoriteRoute.get(PydanticObjectId(route_id))
        if route:
            await route.delete()
            return True
        return False


class FavoriteDriverRepository:
    """Repository for favorite driver database operations."""
    
    @staticmethod
    async def create(favorite: FavoriteDriver) -> FavoriteDriver:
        """Create a new favorite driver."""
        await favorite.insert()
        return favorite
    
    @staticmethod
    async def get_by_id(favorite_id: str) -> Optional[FavoriteDriver]:
        """Get favorite driver by ID."""
        return await FavoriteDriver.get(PydanticObjectId(favorite_id))
    
    @staticmethod
    async def get_user_favorites(user_id: str) -> list[FavoriteDriver]:
        """Get all favorite drivers for a user."""
        return await FavoriteDriver.find(
            FavoriteDriver.user_id == user_id
        ).sort(-FavoriteDriver.created_at).to_list()
    
    @staticmethod
    async def find_existing(user_id: str, driver_id: str) -> Optional[FavoriteDriver]:
        """Find if a driver is already favorited by user."""
        return await FavoriteDriver.find_one(
            FavoriteDriver.user_id == user_id,
            FavoriteDriver.driver_id == driver_id,
        )
    
    @staticmethod
    async def is_favorite(user_id: str, driver_id: str) -> bool:
        """Check if a driver is favorited by user."""
        fav = await FavoriteDriverRepository.find_existing(user_id, driver_id)
        return fav is not None
    
    @staticmethod
    async def delete(favorite_id: str) -> bool:
        """Delete a favorite driver."""
        favorite = await FavoriteDriver.get(PydanticObjectId(favorite_id))
        if favorite:
            await favorite.delete()
            return True
        return False
    
    @staticmethod
    async def delete_by_user_and_driver(user_id: str, driver_id: str) -> bool:
        """Delete a favorite by user and driver IDs."""
        favorite = await FavoriteDriverRepository.find_existing(user_id, driver_id)
        if favorite:
            await favorite.delete()
            return True
        return False


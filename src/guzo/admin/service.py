"""Admin domain service - business logic for admin operations."""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from beanie import PydanticObjectId

from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import Booking, BookingStatus
from src.guzo.bookings.service import BookingService
from src.guzo.trips.service import TripService


@dataclass
class AdminStats:
    """Value object for dashboard statistics."""
    total_users: int
    total_trips: int
    total_bookings: int
    total_revenue: float
    users: List[User]
    trips: list
    bookings: List[Booking]


class AdminService:
    """Service for admin operations."""
    
    @staticmethod
    async def get_dashboard_stats(limit: int = 50) -> AdminStats:
        """Get all dashboard statistics in one call."""
        users = await User.find_all().to_list()
        trips = await TripService.get_upcoming_trips(limit=limit)
        bookings = await BookingService.get_all_bookings(limit=limit)
        
        total_revenue = sum(
            b.price or 0 
            for b in bookings 
            if b.status == BookingStatus.COMPLETED
        )
        
        return AdminStats(
            total_users=len(users),
            total_trips=len(trips),
            total_bookings=len(bookings),
            total_revenue=total_revenue,
            users=users,
            trips=trips,
            bookings=bookings,
        )
    
    @staticmethod
    async def get_users(role: Optional[UserRole] = None) -> tuple[List[User], dict]:
        """Get users with counts for UI tabs."""
        if role:
            users = await User.find(User.role == role).to_list()
        else:
            users = await User.find_all().to_list()
        
        counts = {
            "all": await User.count(),
            "drivers": await User.find(User.role == UserRole.DRIVER).count(),
            "riders": await User.find(User.role == UserRole.RIDER).count(),
        }
        
        return users, counts
    
    @staticmethod
    async def get_drivers() -> List[User]:
        """Get all drivers."""
        return await User.find(User.role == UserRole.DRIVER).to_list()
    
    @staticmethod
    async def activate_user(user_id: str, admin_user: User) -> User:
        """Activate a user account."""
        target_user = await User.get(PydanticObjectId(user_id))
        if not target_user:
            raise ValueError("User not found")
        
        target_user.is_active = True
        target_user.updated_at = datetime.utcnow()
        await target_user.save()
        return target_user
    
    @staticmethod
    async def deactivate_user(user_id: str, admin_user: User) -> User:
        """Deactivate a user account."""
        target_user = await User.get(PydanticObjectId(user_id))
        if not target_user:
            raise ValueError("User not found")
        
        # Business rule: can't deactivate yourself
        if str(target_user.id) == str(admin_user.id):
            raise ValueError("Cannot deactivate your own account")
        
        target_user.is_active = False
        target_user.updated_at = datetime.utcnow()
        await target_user.save()
        return target_user


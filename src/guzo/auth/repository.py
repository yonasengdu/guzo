"""Auth domain repository - database operations for users."""

from datetime import datetime
from typing import Optional, List
from src.guzo.auth.core import User, UserRole
from src.guzo.infrastructure.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User database operations."""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return await User.find_one(User.email == email)
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get a user by phone."""
        return await User.find_one(User.phone == phone)
    
    async def email_or_phone_exists(self, email: str, phone: str) -> bool:
        """Check if email or phone already exists."""
        existing = await User.find_one(
            {"$or": [{"email": email}, {"phone": phone}]}
        )
        return existing is not None
    
    async def get_by_role(self, role: UserRole, limit: int = 100) -> List[User]:
        """Get all users with a specific role."""
        return await User.find(User.role == role).limit(limit).to_list()
    
    async def get_online_drivers(self) -> List[User]:
        """Get all online drivers."""
        return await User.find(
            User.role == UserRole.DRIVER,
            User.is_online == True,
            User.is_active == True,
        ).to_list()
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await user.save()
    
    async def update_online_status(self, user_id: str, is_online: bool) -> Optional[User]:
        """Update driver's online status."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_online = is_online
            user.updated_at = datetime.utcnow()
            await user.save()
            return user
        return None


# Singleton instance
user_repository = UserRepository()


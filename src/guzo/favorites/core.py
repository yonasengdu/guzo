"""Favorites domain models and schemas."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Document Models ==============

class FavoriteRoute(Document):
    """Favorite route model for saved routes."""
    
    user_id: Indexed(str)
    origin: str
    destination: str
    
    # Metadata
    use_count: int = 0  # How many times this route was booked
    last_used: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "favorite_routes"
        
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "origin": "Addis Ababa",
                "destination": "Bahir Dar",
            }
        }


class FavoriteDriver(Document):
    """Favorite driver model for preferred drivers."""
    
    user_id: Indexed(str)
    driver_id: Indexed(str)
    
    # Optional note
    note: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "favorite_drivers"
        
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "driver_id": "507f1f77bcf86cd799439012",
            }
        }


# ============== Pydantic Schemas ==============

class FavoriteRouteCreate(BaseModel):
    """Schema for creating a favorite route."""
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)


class FavoriteRouteResponse(BaseModel):
    """Schema for favorite route response."""
    id: str
    user_id: str
    origin: str
    destination: str
    use_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteDriverCreate(BaseModel):
    """Schema for creating a favorite driver."""
    driver_id: str
    note: Optional[str] = Field(default=None, max_length=200)


class FavoriteDriverResponse(BaseModel):
    """Schema for favorite driver response."""
    id: str
    user_id: str
    driver_id: str
    driver_name: Optional[str] = None
    driver_rating: Optional[float] = None
    driver_phone: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


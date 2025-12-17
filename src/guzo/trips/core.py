"""Trips domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class TripStatus(str, Enum):
    """Status of a driver trip."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============== Document Models ==============

class DriverTrip(Document):
    """Driver trip model for scheduled routes."""
    
    driver_id: Indexed(str)  # Reference to User ID
    vehicle_id: Optional[str] = None  # Reference to Vehicle ID
    
    # Route info
    origin: Indexed(str)
    destination: Indexed(str)
    
    # Schedule
    departure_time: Indexed(datetime)
    estimated_arrival: Optional[datetime] = None
    
    # Capacity and booking
    available_seats: int = Field(ge=1)
    booked_seats: int = Field(default=0, ge=0)
    
    # Pricing (in ETB - Ethiopian Birr)
    price_per_seat: float = Field(gt=0)
    whole_car_price: float = Field(gt=0)
    
    # Status
    status: TripStatus = TripStatus.SCHEDULED
    
    # Additional info
    notes: Optional[str] = None
    waypoints: list[str] = Field(default_factory=list)  # Intermediate stops
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "driver_trips"
        
    @property
    def remaining_seats(self) -> int:
        """Get number of remaining seats."""
        return self.available_seats - self.booked_seats
    
    @property
    def is_full(self) -> bool:
        """Check if trip is fully booked."""
        return self.booked_seats >= self.available_seats
    
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "507f1f77bcf86cd799439011",
                "origin": "Addis Ababa",
                "destination": "Bahir Dar",
                "departure_time": "2024-01-15T08:00:00",
                "available_seats": 4,
                "price_per_seat": 800.00,
                "whole_car_price": 3000.00,
            }
        }


# ============== Pydantic Schemas ==============

class TripCreate(BaseModel):
    """Schema for creating a driver trip."""
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    departure_time: datetime
    available_seats: int = Field(ge=1, le=50)
    price_per_seat: float = Field(gt=0)
    whole_car_price: float = Field(gt=0)
    vehicle_id: Optional[str] = None
    notes: Optional[str] = None
    waypoints: list[str] = Field(default_factory=list)


class TripUpdate(BaseModel):
    """Schema for updating a trip."""
    departure_time: Optional[datetime] = None
    available_seats: Optional[int] = Field(default=None, ge=1, le=50)
    price_per_seat: Optional[float] = Field(default=None, gt=0)
    whole_car_price: Optional[float] = Field(default=None, gt=0)
    status: Optional[TripStatus] = None
    notes: Optional[str] = None


class TripResponse(BaseModel):
    """Schema for trip response."""
    id: str
    driver_id: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_rating: Optional[float] = None
    vehicle_id: Optional[str] = None
    origin: str
    destination: str
    departure_time: datetime
    available_seats: int
    booked_seats: int
    remaining_seats: int
    price_per_seat: float
    whole_car_price: float
    status: TripStatus
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TripSearch(BaseModel):
    """Schema for searching trips."""
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[datetime] = None
    min_seats: int = 1

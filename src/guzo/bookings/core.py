"""Bookings domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class BookingType(str, Enum):
    """Type of booking."""
    SEAT = "seat"  # Booking individual seats
    WHOLE_CAR = "whole_car"  # Booking entire vehicle
    CHARTER = "charter"  # Custom charter request


class BookingStatus(str, Enum):
    """Status of a booking."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============== Document Models ==============

class Booking(Document):
    """Booking model for ride reservations."""
    
    # Customer info (customer_id is null for phone bookings by admin)
    customer_id: Optional[Indexed(str)] = None
    customer_name: str
    customer_phone: str
    
    # Trip reference (null for charter requests)
    trip_id: Optional[Indexed(str)] = None
    
    # Booking details
    booking_type: BookingType = BookingType.SEAT
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    seats_booked: int = Field(default=1, ge=1)
    
    # Pricing
    price: Optional[float] = None
    
    # Status
    status: BookingStatus = BookingStatus.PENDING
    
    # Assignment
    assigned_driver_id: Optional[str] = None
    
    # Additional info
    notes: Optional[str] = None
    special_requests: Optional[str] = None
    
    # Reviews (references to Review IDs)
    customer_review_id: Optional[str] = None  # Review given by customer
    driver_review_id: Optional[str] = None  # Review given by driver
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "bookings"
        
    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "Tigist Haile",
                "customer_phone": "+251922345678",
                "pickup_location": "Addis Ababa",
                "dropoff_location": "Adama",
                "scheduled_time": "2024-01-15T08:00:00",
                "seats_booked": 2,
                "booking_type": "seat",
            }
        }


# ============== Pydantic Schemas ==============

class BookingCreate(BaseModel):
    """Schema for creating a booking."""
    trip_id: Optional[str] = None  # Null for charter requests
    customer_name: str = Field(min_length=2)
    customer_phone: str = Field(min_length=10)
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    seats_booked: int = Field(default=1, ge=1)
    booking_type: BookingType = BookingType.SEAT
    notes: Optional[str] = None
    special_requests: Optional[str] = None


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    status: Optional[BookingStatus] = None
    assigned_driver_id: Optional[str] = None
    price: Optional[float] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Schema for booking response."""
    id: str
    customer_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    trip_id: Optional[str] = None
    booking_type: BookingType
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    seats_booked: int
    price: Optional[float] = None
    status: BookingStatus
    assigned_driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_rating: Optional[float] = None
    notes: Optional[str] = None
    customer_review_id: Optional[str] = None
    driver_review_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

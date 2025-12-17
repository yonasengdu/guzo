"""Vehicles domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class VehicleType(str, Enum):
    """Types of vehicles available."""
    SEDAN = "sedan"
    SUV = "suv"
    MINIBUS = "minibus"
    BUS = "bus"
    VAN = "van"


# ============== Document Models ==============

class Vehicle(Document):
    """Vehicle model for driver's cars."""
    
    driver_id: Indexed(str)  # Reference to User ID
    
    # Vehicle details
    plate_number: Indexed(str, unique=True)
    make: str  # e.g., Toyota
    model: str  # e.g., Corolla
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: VehicleType = VehicleType.SEDAN
    
    # Capacity
    capacity: int = Field(ge=1, le=50)  # Number of passengers
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    # Images
    images: list[str] = Field(default_factory=list)
    
    # Registration documents
    registration_document: Optional[str] = None  # File path
    registration_expiry: Optional[datetime] = None
    insurance_document: Optional[str] = None  # File path
    insurance_expiry: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "vehicles"
        
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "507f1f77bcf86cd799439011",
                "plate_number": "AA-12345",
                "make": "Toyota",
                "model": "HiAce",
                "vehicle_type": "minibus",
                "capacity": 12,
            }
        }


# ============== Pydantic Schemas ==============

class VehicleCreate(BaseModel):
    """Schema for creating a vehicle."""
    plate_number: str = Field(min_length=4)
    make: str = Field(min_length=2)
    model: str = Field(min_length=1)
    year: Optional[int] = Field(default=None, ge=1990, le=2030)
    color: Optional[str] = None
    vehicle_type: VehicleType = VehicleType.SEDAN
    capacity: int = Field(ge=1, le=50)


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1990, le=2030)
    color: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    capacity: Optional[int] = Field(default=None, ge=1, le=50)
    is_active: Optional[bool] = None


class VehicleResponse(BaseModel):
    """Schema for vehicle response."""
    id: str
    driver_id: str
    plate_number: str
    make: str
    model: str
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: VehicleType
    capacity: int
    is_active: bool
    is_verified: bool
    images: list[str] = []
    registration_document: Optional[str] = None
    registration_expiry: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


"""Pricing domain models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


# ============== Enums ==============

class SurgeReason(str, Enum):
    """Reasons for surge pricing."""
    PEAK_HOURS = "peak_hours"
    HIGH_DEMAND = "high_demand"
    HOLIDAY = "holiday"
    WEATHER = "weather"
    SPECIAL_EVENT = "special_event"
    MANUAL = "manual"


# ============== Document Models ==============

class PricingRule(Document):
    """Pricing rule for a specific route."""
    
    origin: Indexed(str)
    destination: Indexed(str)
    
    # Pricing
    base_fare: float = Field(gt=0)  # Base fare in ETB
    per_km_rate: float = Field(gt=0)  # Rate per kilometer
    estimated_distance_km: float = Field(gt=0)  # Estimated route distance
    
    # Status
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "pricing_rules"
        
    @property
    def calculated_price(self) -> float:
        """Calculate base price without surge."""
        return self.base_fare + (self.per_km_rate * self.estimated_distance_km)
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin": "Addis Ababa",
                "destination": "Bahir Dar",
                "base_fare": 100.0,
                "per_km_rate": 5.0,
                "estimated_distance_km": 500.0,
            }
        }


class SurgeMultiplier(Document):
    """Surge pricing multiplier."""
    
    # Route (use "*" for all routes)
    route_key: Indexed(str)  # Format: "origin-destination" or "*"
    
    # Surge details
    multiplier: float = Field(ge=1.0, le=5.0)  # e.g., 1.5 for 50% surge
    reason: SurgeReason = SurgeReason.MANUAL
    description: Optional[str] = None
    
    # Time bounds
    start_time: datetime
    end_time: datetime
    
    # Status
    is_active: bool = True
    
    # Auto-apply settings for recurring surges
    is_recurring: bool = False
    recurring_days: list[int] = Field(default_factory=list)  # 0=Monday, 6=Sunday
    recurring_start_hour: Optional[int] = None  # 0-23
    recurring_end_hour: Optional[int] = None  # 0-23
    
    # Audit
    created_by: Optional[str] = None  # Admin user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "surge_multipliers"
        
    class Config:
        json_schema_extra = {
            "example": {
                "route_key": "Addis Ababa-Bahir Dar",
                "multiplier": 1.5,
                "reason": "peak_hours",
                "start_time": "2024-01-15T07:00:00",
                "end_time": "2024-01-15T09:00:00",
            }
        }


# ============== Pydantic Schemas ==============

class PricingRuleCreate(BaseModel):
    """Schema for creating a pricing rule."""
    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    base_fare: float = Field(gt=0)
    per_km_rate: float = Field(gt=0)
    estimated_distance_km: float = Field(gt=0)


class PricingRuleUpdate(BaseModel):
    """Schema for updating a pricing rule."""
    base_fare: Optional[float] = Field(default=None, gt=0)
    per_km_rate: Optional[float] = Field(default=None, gt=0)
    estimated_distance_km: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class PricingRuleResponse(BaseModel):
    """Schema for pricing rule response."""
    id: str
    origin: str
    destination: str
    base_fare: float
    per_km_rate: float
    estimated_distance_km: float
    calculated_price: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SurgeCreate(BaseModel):
    """Schema for creating a surge multiplier."""
    route_key: str = Field(min_length=1)  # "*" for all routes
    multiplier: float = Field(ge=1.0, le=5.0)
    reason: SurgeReason = SurgeReason.MANUAL
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_recurring: bool = False
    recurring_days: list[int] = Field(default_factory=list)
    recurring_start_hour: Optional[int] = Field(default=None, ge=0, le=23)
    recurring_end_hour: Optional[int] = Field(default=None, ge=0, le=23)


class SurgeUpdate(BaseModel):
    """Schema for updating a surge multiplier."""
    multiplier: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    reason: Optional[SurgeReason] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None


class SurgeResponse(BaseModel):
    """Schema for surge response."""
    id: str
    route_key: str
    multiplier: float
    reason: SurgeReason
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_active: bool
    is_recurring: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PriceCalculation(BaseModel):
    """Schema for price calculation result."""
    base_price: float
    surge_multiplier: float
    surge_reason: Optional[str] = None
    final_price: float
    is_surge_active: bool


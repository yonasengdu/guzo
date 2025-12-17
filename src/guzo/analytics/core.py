"""Analytics domain models and schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ============== Pydantic Schemas ==============

class DateRange(BaseModel):
    """Date range for analytics queries."""
    start_date: datetime
    end_date: datetime


class DriverEarnings(BaseModel):
    """Driver earnings summary."""
    driver_id: str
    driver_name: str
    period: str  # "today", "week", "month", "custom"
    
    # Revenue
    total_revenue: float
    total_trips: int
    total_bookings: int
    
    # Averages
    avg_revenue_per_trip: float
    avg_rating: float
    
    # Breakdown
    revenue_by_day: dict[str, float]
    top_routes: list[dict]
    
    # Comparison
    revenue_change_percent: Optional[float] = None


class PlatformStats(BaseModel):
    """Platform-wide statistics."""
    period: str
    
    # Users
    total_users: int
    total_drivers: int
    total_customers: int
    new_users: int
    active_users: int
    
    # Trips & Bookings
    total_trips: int
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    
    # Revenue
    total_revenue: float
    avg_booking_value: float
    
    # Performance
    booking_completion_rate: float
    avg_driver_rating: float
    
    # Trends
    revenue_by_day: dict[str, float]
    bookings_by_day: dict[str, int]
    users_by_day: dict[str, int]


class RoutePopularity(BaseModel):
    """Route popularity data."""
    origin: str
    destination: str
    total_bookings: int
    total_revenue: float
    avg_price: float


class DemandHeatmap(BaseModel):
    """Demand heatmap data."""
    routes: list[RoutePopularity]
    peak_hours: dict[int, int]  # hour -> booking count
    peak_days: dict[str, int]  # day name -> booking count


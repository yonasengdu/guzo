"""Analytics resource - API routes for analytics and reporting."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user, get_current_admin
from src.guzo.analytics.service import AnalyticsService
from src.guzo.analytics.core import (
    DriverEarnings,
    PlatformStats,
    DemandHeatmap,
    SurgeRecommendation,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============== Driver Endpoints ==============

@router.get("/driver/earnings", response_model=DriverEarnings)
async def get_driver_earnings(
    user: User = Depends(get_current_user),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get earnings analytics for current driver."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can view earnings")
    
    earnings = await AnalyticsService.get_driver_earnings(str(user.id), period)
    return earnings


# ============== Admin Endpoints ==============

@router.get("/platform", response_model=PlatformStats)
async def get_platform_stats(
    user: User = Depends(get_current_admin),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get platform-wide statistics (admin)."""
    stats = await AnalyticsService.get_platform_stats(period)
    return stats


@router.get("/demand", response_model=DemandHeatmap)
async def get_demand_heatmap(
    user: User = Depends(get_current_admin),
    days: int = Query(30, ge=1, le=90),
):
    """Get demand heatmap (admin)."""
    heatmap = await AnalyticsService.get_demand_heatmap(days)
    return heatmap


@router.get("/surge-recommendation", response_model=SurgeRecommendation)
async def get_surge_recommendation(
    origin: str,
    destination: str,
    user: User = Depends(get_current_admin),
):
    """Get surge pricing recommendation (admin)."""
    recommendation = await AnalyticsService.calculate_surge_recommendation(
        origin, destination
    )
    return SurgeRecommendation(**recommendation)


@router.get("/driver/{driver_id}/performance", response_model=DriverEarnings)
async def get_driver_performance(
    driver_id: str,
    user: User = Depends(get_current_admin),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get performance analytics for a specific driver (admin)."""
    earnings = await AnalyticsService.get_driver_earnings(driver_id, period)
    return earnings

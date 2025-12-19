"""Analytics resource - API routes for analytics and reporting."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.guzo.auth.core import User, UserRole
from src.guzo.middleware import get_current_user, get_current_admin
from src.guzo.analytics.core import DateRange
from src.guzo.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
templates = Jinja2Templates(directory="src/guzo/templates")


# ============== Driver Analytics ==============

@router.get("/driver/earnings", response_class=HTMLResponse)
async def get_driver_earnings(
    request: Request,
    user: User = Depends(get_current_user),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get earnings analytics for current driver."""
    if user.role != UserRole.DRIVER:
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "message": "Only drivers can view earnings",
            },
            status_code=403,
        )
    
    earnings = await AnalyticsService.get_driver_earnings(str(user.id), period)
    
    return templates.TemplateResponse(
        "partials/earnings_content.html",
        {
            "request": request,
            "earnings": earnings,
            "user": user,
            "period": period,
        },
    )


@router.get("/driver/earnings/chart", response_class=HTMLResponse)
async def get_driver_earnings_chart(
    request: Request,
    user: User = Depends(get_current_user),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get earnings chart data for current driver."""
    if user.role != UserRole.DRIVER:
        return HTMLResponse("Unauthorized", status_code=403)
    
    earnings = await AnalyticsService.get_driver_earnings(str(user.id), period)
    
    return templates.TemplateResponse(
        "partials/earnings_chart.html",
        {
            "request": request,
            "earnings": earnings,
            "period": period,
        },
    )


# ============== Admin Analytics ==============

@router.get("/platform", response_class=HTMLResponse)
async def get_platform_stats(
    request: Request,
    user: User = Depends(get_current_admin),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get platform-wide statistics (admin)."""
    stats = await AnalyticsService.get_platform_stats(period)
    
    return templates.TemplateResponse(
        "partials/platform_stats.html",
        {
            "request": request,
            "stats": stats,
            "user": user,
            "period": period,
        },
    )


@router.get("/platform/charts", response_class=HTMLResponse)
async def get_platform_charts(
    request: Request,
    user: User = Depends(get_current_admin),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get platform analytics charts (admin)."""
    stats = await AnalyticsService.get_platform_stats(period)
    
    return templates.TemplateResponse(
        "partials/platform_charts.html",
        {
            "request": request,
            "stats": stats,
            "period": period,
        },
    )


@router.get("/demand", response_class=HTMLResponse)
async def get_demand_heatmap(
    request: Request,
    user: User = Depends(get_current_admin),
    days: int = Query(30, ge=1, le=90),
):
    """Get demand heatmap (admin)."""
    heatmap = await AnalyticsService.get_demand_heatmap(days)
    
    return templates.TemplateResponse(
        "partials/demand_heatmap.html",
        {
            "request": request,
            "heatmap": heatmap,
            "days": days,
        },
    )


@router.get("/surge-recommendation", response_class=HTMLResponse)
async def get_surge_recommendation(
    request: Request,
    origin: str,
    destination: str,
    user: User = Depends(get_current_admin),
):
    """Get surge pricing recommendation (admin)."""
    recommendation = await AnalyticsService.calculate_surge_recommendation(
        origin, destination
    )
    
    return templates.TemplateResponse(
        "partials/surge_recommendation.html",
        {
            "request": request,
            "recommendation": recommendation,
            "origin": origin,
            "destination": destination,
        },
    )


# ============== Driver Performance (Admin) ==============

@router.get("/driver/{driver_id}/performance", response_class=HTMLResponse)
async def get_driver_performance(
    request: Request,
    driver_id: str,
    user: User = Depends(get_current_admin),
    period: str = Query("month", enum=["today", "week", "month"]),
):
    """Get performance analytics for a specific driver (admin)."""
    earnings = await AnalyticsService.get_driver_earnings(driver_id, period)
    
    return templates.TemplateResponse(
        "partials/driver_performance.html",
        {
            "request": request,
            "earnings": earnings,
            "period": period,
        },
    )


"""Pricing resource - API routes for pricing management."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.guzo.auth.core import User
from src.guzo.middleware import get_current_admin
from src.guzo.pricing.core import (
    PricingRuleCreate,
    PricingRuleUpdate,
    SurgeCreate,
    SurgeUpdate,
    SurgeReason,
)
from src.guzo.pricing.service import PricingService

router = APIRouter(prefix="/pricing", tags=["Pricing"])
templates = Jinja2Templates(directory="src/guzo/templates")


# ============== Public Pricing Calculation ==============

@router.get("/calculate", response_class=HTMLResponse)
async def calculate_route_price(
    request: Request,
    origin: str,
    destination: str,
):
    """Calculate price for a route (public)."""
    calc = await PricingService.calculate_price(origin, destination)
    
    return templates.TemplateResponse(
        "partials/price_calculation.html",
        {
            "request": request,
            "calculation": calc,
            "origin": origin,
            "destination": destination,
        },
    )


# ============== Admin: Pricing Rules ==============

@router.get("/rules", response_class=HTMLResponse)
async def get_pricing_rules(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Get all pricing rules (admin)."""
    rules = await PricingService.get_all_pricing_rules()
    
    return templates.TemplateResponse(
        "partials/pricing_rules.html",
        {
            "request": request,
            "rules": rules,
            "user": user,
        },
    )


@router.post("/rules", response_class=HTMLResponse)
async def create_pricing_rule(
    request: Request,
    user: User = Depends(get_current_admin),
    origin: str = Form(...),
    destination: str = Form(...),
    base_fare: float = Form(...),
    per_km_rate: float = Form(...),
    estimated_distance_km: float = Form(...),
):
    """Create a new pricing rule (admin)."""
    data = PricingRuleCreate(
        origin=origin,
        destination=destination,
        base_fare=base_fare,
        per_km_rate=per_km_rate,
        estimated_distance_km=estimated_distance_km,
    )
    
    rule = await PricingService.create_pricing_rule(data)
    
    return templates.TemplateResponse(
        "partials/pricing_rule_row.html",
        {
            "request": request,
            "rule": rule,
        },
    )


@router.put("/rules/{rule_id}", response_class=HTMLResponse)
async def update_pricing_rule(
    request: Request,
    rule_id: str,
    user: User = Depends(get_current_admin),
    base_fare: Optional[float] = Form(None),
    per_km_rate: Optional[float] = Form(None),
    estimated_distance_km: Optional[float] = Form(None),
    is_active: Optional[bool] = Form(None),
):
    """Update a pricing rule (admin)."""
    data = PricingRuleUpdate(
        base_fare=base_fare,
        per_km_rate=per_km_rate,
        estimated_distance_km=estimated_distance_km,
        is_active=is_active,
    )
    
    rule = await PricingService.update_pricing_rule(rule_id, data)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return HTMLResponse('<span class="text-green-600">Updated</span>')


@router.delete("/rules/{rule_id}", response_class=HTMLResponse)
async def delete_pricing_rule(
    request: Request,
    rule_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a pricing rule (admin)."""
    success = await PricingService.delete_pricing_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return HTMLResponse('')


# ============== Admin: Surge Multipliers ==============

@router.get("/surges", response_class=HTMLResponse)
async def get_surge_multipliers(
    request: Request,
    user: User = Depends(get_current_admin),
    active_only: bool = False,
):
    """Get all surge multipliers (admin)."""
    surges = await PricingService.get_all_surges(active_only)
    
    return templates.TemplateResponse(
        "partials/surge_list.html",
        {
            "request": request,
            "surges": surges,
            "user": user,
        },
    )


@router.post("/surges", response_class=HTMLResponse)
async def create_surge(
    request: Request,
    user: User = Depends(get_current_admin),
    route_key: str = Form(...),
    multiplier: float = Form(...),
    reason: str = Form("manual"),
    description: Optional[str] = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
):
    """Create a new surge multiplier (admin)."""
    data = SurgeCreate(
        route_key=route_key,
        multiplier=multiplier,
        reason=SurgeReason(reason),
        description=description,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
    )
    
    surge = await PricingService.create_surge(data, str(user.id))
    
    return templates.TemplateResponse(
        "partials/surge_row.html",
        {
            "request": request,
            "surge": surge,
        },
    )


@router.post("/surges/{surge_id}/deactivate", response_class=HTMLResponse)
async def deactivate_surge(
    request: Request,
    surge_id: str,
    user: User = Depends(get_current_admin),
):
    """Deactivate a surge multiplier (admin)."""
    surge = await PricingService.deactivate_surge(surge_id)
    
    if not surge:
        raise HTTPException(status_code=404, detail="Surge not found")
    
    return HTMLResponse('<span class="badge-apple badge-warning">Inactive</span>')


@router.delete("/surges/{surge_id}", response_class=HTMLResponse)
async def delete_surge(
    request: Request,
    surge_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a surge multiplier (admin)."""
    success = await PricingService.delete_surge(surge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Surge not found")
    
    return HTMLResponse('')


# ============== Admin: Demand Analysis ==============

@router.get("/demand", response_class=HTMLResponse)
async def get_demand_stats(
    request: Request,
    origin: str,
    destination: str,
    days: int = 7,
    user: User = Depends(get_current_admin),
):
    """Get demand statistics for a route (admin)."""
    stats = await PricingService.get_demand_stats(origin, destination, days)
    
    return templates.TemplateResponse(
        "partials/demand_stats.html",
        {
            "request": request,
            "stats": stats,
            "origin": origin,
            "destination": destination,
        },
    )


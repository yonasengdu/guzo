"""Pricing resource - API routes for pricing management."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.guzo.auth.core import User
from src.guzo.middleware import get_current_admin
from src.guzo.pricing.core import (
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRuleResponse,
    SurgeCreate,
    SurgeResponse,
    PriceCalculation,
    DemandStats,
)
from src.guzo.pricing.service import PricingService

router = APIRouter(prefix="/pricing", tags=["Pricing"])


class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"


# ============== Public Pricing Calculation ==============

@router.get("/calculate", response_model=PriceCalculation)
async def calculate_route_price(
    origin: str,
    destination: str,
):
    """Calculate price for a route (public)."""
    calc = await PricingService.calculate_price(origin, destination)
    return calc


# ============== Admin: Pricing Rules ==============

@router.get("/rules", response_model=list[PricingRuleResponse])
async def get_pricing_rules(user: User = Depends(get_current_admin)):
    """Get all pricing rules (admin)."""
    rules = await PricingService.get_all_pricing_rules()
    return [
        PricingRuleResponse(
            id=str(r.id),
            origin=r.origin,
            destination=r.destination,
            base_fare=r.base_fare,
            per_km_rate=r.per_km_rate,
            estimated_distance_km=r.estimated_distance_km,
            calculated_price=r.calculated_price,
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post("/rules", response_model=PricingRuleResponse)
async def create_pricing_rule(
    data: PricingRuleCreate,
    user: User = Depends(get_current_admin),
):
    """Create a new pricing rule (admin)."""
    rule = await PricingService.create_pricing_rule(data)
    return PricingRuleResponse(
        id=str(rule.id),
        origin=rule.origin,
        destination=rule.destination,
        base_fare=rule.base_fare,
        per_km_rate=rule.per_km_rate,
        estimated_distance_km=rule.estimated_distance_km,
        calculated_price=rule.calculated_price,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.patch("/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: str,
    data: PricingRuleUpdate,
    user: User = Depends(get_current_admin),
):
    """Update a pricing rule (admin)."""
    rule = await PricingService.update_pricing_rule(rule_id, data)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return PricingRuleResponse(
        id=str(rule.id),
        origin=rule.origin,
        destination=rule.destination,
        base_fare=rule.base_fare,
        per_km_rate=rule.per_km_rate,
        estimated_distance_km=rule.estimated_distance_km,
        calculated_price=rule.calculated_price,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.delete("/rules/{rule_id}", response_model=DeleteResponse)
async def delete_pricing_rule(
    rule_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a pricing rule (admin)."""
    success = await PricingService.delete_pricing_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return DeleteResponse()


# ============== Admin: Surge Multipliers ==============

@router.get("/surges", response_model=list[SurgeResponse])
async def get_surge_multipliers(
    user: User = Depends(get_current_admin),
    active_only: bool = False,
):
    """Get all surge multipliers (admin)."""
    surges = await PricingService.get_all_surges(active_only)
    return [
        SurgeResponse(
            id=str(s.id),
            route_key=s.route_key,
            multiplier=s.multiplier,
            reason=s.reason,
            description=s.description,
            start_time=s.start_time,
            end_time=s.end_time,
            is_active=s.is_active,
            is_recurring=s.is_recurring,
            created_at=s.created_at,
        )
        for s in surges
    ]


@router.post("/surges", response_model=SurgeResponse)
async def create_surge(
    data: SurgeCreate,
    user: User = Depends(get_current_admin),
):
    """Create a new surge multiplier (admin)."""
    surge = await PricingService.create_surge(data, str(user.id))
    return SurgeResponse(
        id=str(surge.id),
        route_key=surge.route_key,
        multiplier=surge.multiplier,
        reason=surge.reason,
        description=surge.description,
        start_time=surge.start_time,
        end_time=surge.end_time,
        is_active=surge.is_active,
        is_recurring=surge.is_recurring,
        created_at=surge.created_at,
    )


@router.post("/surges/{surge_id}/deactivate", response_model=SurgeResponse)
async def deactivate_surge(
    surge_id: str,
    user: User = Depends(get_current_admin),
):
    """Deactivate a surge multiplier (admin)."""
    surge = await PricingService.deactivate_surge(surge_id)
    
    if not surge:
        raise HTTPException(status_code=404, detail="Surge not found")
    
    return SurgeResponse(
        id=str(surge.id),
        route_key=surge.route_key,
        multiplier=surge.multiplier,
        reason=surge.reason,
        description=surge.description,
        start_time=surge.start_time,
        end_time=surge.end_time,
        is_active=surge.is_active,
        is_recurring=surge.is_recurring,
        created_at=surge.created_at,
    )


@router.delete("/surges/{surge_id}", response_model=DeleteResponse)
async def delete_surge(
    surge_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a surge multiplier (admin)."""
    success = await PricingService.delete_surge(surge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Surge not found")
    
    return DeleteResponse()


# ============== Admin: Demand Analysis ==============

@router.get("/demand", response_model=DemandStats)
async def get_demand_stats(
    origin: str,
    destination: str,
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_current_admin),
):
    """Get demand statistics for a route (admin)."""
    stats = await PricingService.get_demand_stats(origin, destination, days)
    return stats

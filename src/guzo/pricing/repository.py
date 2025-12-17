"""Pricing repository - Database operations for pricing."""

from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId

from src.guzo.pricing.core import PricingRule, SurgeMultiplier


class PricingRuleRepository:
    """Repository for pricing rule database operations."""
    
    @staticmethod
    async def create(rule: PricingRule) -> PricingRule:
        """Create a new pricing rule."""
        await rule.insert()
        return rule
    
    @staticmethod
    async def get_by_id(rule_id: str) -> Optional[PricingRule]:
        """Get pricing rule by ID."""
        return await PricingRule.get(PydanticObjectId(rule_id))
    
    @staticmethod
    async def get_by_route(origin: str, destination: str) -> Optional[PricingRule]:
        """Get pricing rule for a specific route."""
        return await PricingRule.find_one(
            PricingRule.origin == origin,
            PricingRule.destination == destination,
            PricingRule.is_active == True,
        )
    
    @staticmethod
    async def get_all_active() -> list[PricingRule]:
        """Get all active pricing rules."""
        return await PricingRule.find(
            PricingRule.is_active == True
        ).sort(PricingRule.origin).to_list()
    
    @staticmethod
    async def get_all() -> list[PricingRule]:
        """Get all pricing rules."""
        return await PricingRule.find_all().sort(PricingRule.origin).to_list()
    
    @staticmethod
    async def update(rule_id: str, data: dict) -> Optional[PricingRule]:
        """Update a pricing rule."""
        rule = await PricingRule.get(PydanticObjectId(rule_id))
        if rule:
            data["updated_at"] = datetime.utcnow()
            for key, value in data.items():
                if value is not None:
                    setattr(rule, key, value)
            await rule.save()
        return rule
    
    @staticmethod
    async def delete(rule_id: str) -> bool:
        """Delete a pricing rule."""
        rule = await PricingRule.get(PydanticObjectId(rule_id))
        if rule:
            await rule.delete()
            return True
        return False


class SurgeRepository:
    """Repository for surge multiplier database operations."""
    
    @staticmethod
    async def create(surge: SurgeMultiplier) -> SurgeMultiplier:
        """Create a new surge multiplier."""
        await surge.insert()
        return surge
    
    @staticmethod
    async def get_by_id(surge_id: str) -> Optional[SurgeMultiplier]:
        """Get surge by ID."""
        return await SurgeMultiplier.get(PydanticObjectId(surge_id))
    
    @staticmethod
    async def get_active_for_route(route_key: str, at_time: datetime = None) -> list[SurgeMultiplier]:
        """Get active surge multipliers for a route."""
        if at_time is None:
            at_time = datetime.utcnow()
        
        # Get surges for specific route or global (*)
        surges = await SurgeMultiplier.find(
            SurgeMultiplier.is_active == True,
            SurgeMultiplier.start_time <= at_time,
            SurgeMultiplier.end_time >= at_time,
        ).to_list()
        
        # Filter by route_key
        return [s for s in surges if s.route_key in (route_key, "*")]
    
    @staticmethod
    async def get_all_active() -> list[SurgeMultiplier]:
        """Get all active surge multipliers."""
        now = datetime.utcnow()
        return await SurgeMultiplier.find(
            SurgeMultiplier.is_active == True,
            SurgeMultiplier.end_time >= now,
        ).sort(-SurgeMultiplier.created_at).to_list()
    
    @staticmethod
    async def get_all() -> list[SurgeMultiplier]:
        """Get all surge multipliers."""
        return await SurgeMultiplier.find_all().sort(-SurgeMultiplier.created_at).to_list()
    
    @staticmethod
    async def update(surge_id: str, data: dict) -> Optional[SurgeMultiplier]:
        """Update a surge multiplier."""
        surge = await SurgeMultiplier.get(PydanticObjectId(surge_id))
        if surge:
            for key, value in data.items():
                if value is not None:
                    setattr(surge, key, value)
            await surge.save()
        return surge
    
    @staticmethod
    async def deactivate(surge_id: str) -> Optional[SurgeMultiplier]:
        """Deactivate a surge multiplier."""
        surge = await SurgeMultiplier.get(PydanticObjectId(surge_id))
        if surge:
            surge.is_active = False
            await surge.save()
        return surge
    
    @staticmethod
    async def delete(surge_id: str) -> bool:
        """Delete a surge multiplier."""
        surge = await SurgeMultiplier.get(PydanticObjectId(surge_id))
        if surge:
            await surge.delete()
            return True
        return False


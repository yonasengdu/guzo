"""Pricing service - Business logic for dynamic pricing."""

from datetime import datetime
from typing import Optional

from src.guzo.pricing.core import (
    PricingRule,
    SurgeMultiplier,
    SurgeReason,
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRuleResponse,
    SurgeCreate,
    SurgeUpdate,
    SurgeResponse,
    PriceCalculation,
)
from src.guzo.pricing.repository import PricingRuleRepository, SurgeRepository


class PricingService:
    """Service for pricing business logic."""
    
    # Default pricing when no rule exists
    DEFAULT_BASE_FARE = 50.0  # ETB
    DEFAULT_PER_KM_RATE = 3.0  # ETB per km
    DEFAULT_DISTANCE = 100.0  # km (used when no estimate)
    
    # Peak hours configuration
    PEAK_MORNING_START = 7
    PEAK_MORNING_END = 9
    PEAK_EVENING_START = 17
    PEAK_EVENING_END = 19
    PEAK_MULTIPLIER = 1.2
    
    @staticmethod
    async def calculate_price(
        origin: str,
        destination: str,
        at_time: datetime = None,
    ) -> PriceCalculation:
        """Calculate the price for a route including any surge."""
        if at_time is None:
            at_time = datetime.utcnow()
        
        # Get base pricing rule
        rule = await PricingRuleRepository.get_by_route(origin, destination)
        
        if rule:
            base_price = rule.calculated_price
        else:
            # Use default pricing
            base_price = (
                PricingService.DEFAULT_BASE_FARE +
                (PricingService.DEFAULT_PER_KM_RATE * PricingService.DEFAULT_DISTANCE)
            )
        
        # Check for active surge
        route_key = f"{origin}-{destination}"
        surges = await SurgeRepository.get_active_for_route(route_key, at_time)
        
        # Also check for time-based peak hour surge
        peak_surge = PricingService._check_peak_hours(at_time)
        
        # Use the highest multiplier
        max_multiplier = 1.0
        surge_reason = None
        
        for surge in surges:
            if surge.multiplier > max_multiplier:
                max_multiplier = surge.multiplier
                surge_reason = surge.reason.value
        
        # Apply peak hour surge if higher
        if peak_surge > max_multiplier:
            max_multiplier = peak_surge
            surge_reason = "peak_hours"
        
        final_price = round(base_price * max_multiplier, 2)
        
        return PriceCalculation(
            base_price=round(base_price, 2),
            surge_multiplier=max_multiplier,
            surge_reason=surge_reason,
            final_price=final_price,
            is_surge_active=max_multiplier > 1.0,
        )
    
    @staticmethod
    def _check_peak_hours(at_time: datetime) -> float:
        """Check if given time is during peak hours."""
        hour = at_time.hour
        
        # Morning peak
        if PricingService.PEAK_MORNING_START <= hour < PricingService.PEAK_MORNING_END:
            return PricingService.PEAK_MULTIPLIER
        
        # Evening peak
        if PricingService.PEAK_EVENING_START <= hour < PricingService.PEAK_EVENING_END:
            return PricingService.PEAK_MULTIPLIER
        
        return 1.0
    
    @staticmethod
    async def get_suggested_price(
        origin: str,
        destination: str,
        seats: int = 1,
    ) -> dict:
        """Get suggested pricing for a new trip."""
        calc = await PricingService.calculate_price(origin, destination)
        
        return {
            "price_per_seat": round(calc.final_price / 4, 2),  # Assume 4 seats
            "whole_car_price": calc.final_price,
            "is_surge": calc.is_surge_active,
            "surge_info": calc.surge_reason,
        }
    
    # ============== Pricing Rules ==============
    
    @staticmethod
    async def create_pricing_rule(data: PricingRuleCreate) -> PricingRule:
        """Create a new pricing rule."""
        rule = PricingRule(
            origin=data.origin,
            destination=data.destination,
            base_fare=data.base_fare,
            per_km_rate=data.per_km_rate,
            estimated_distance_km=data.estimated_distance_km,
        )
        return await PricingRuleRepository.create(rule)
    
    @staticmethod
    async def get_all_pricing_rules() -> list[PricingRuleResponse]:
        """Get all pricing rules."""
        rules = await PricingRuleRepository.get_all()
        
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
    
    @staticmethod
    async def update_pricing_rule(
        rule_id: str,
        data: PricingRuleUpdate,
    ) -> Optional[PricingRule]:
        """Update a pricing rule."""
        update_data = data.model_dump(exclude_unset=True)
        return await PricingRuleRepository.update(rule_id, update_data)
    
    @staticmethod
    async def delete_pricing_rule(rule_id: str) -> bool:
        """Delete a pricing rule."""
        return await PricingRuleRepository.delete(rule_id)
    
    # ============== Surge Multipliers ==============
    
    @staticmethod
    async def create_surge(data: SurgeCreate, admin_id: str = None) -> SurgeMultiplier:
        """Create a new surge multiplier."""
        surge = SurgeMultiplier(
            route_key=data.route_key,
            multiplier=data.multiplier,
            reason=data.reason,
            description=data.description,
            start_time=data.start_time,
            end_time=data.end_time,
            is_recurring=data.is_recurring,
            recurring_days=data.recurring_days,
            recurring_start_hour=data.recurring_start_hour,
            recurring_end_hour=data.recurring_end_hour,
            created_by=admin_id,
        )
        return await SurgeRepository.create(surge)
    
    @staticmethod
    async def get_all_surges(active_only: bool = False) -> list[SurgeResponse]:
        """Get all surge multipliers."""
        if active_only:
            surges = await SurgeRepository.get_all_active()
        else:
            surges = await SurgeRepository.get_all()
        
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
    
    @staticmethod
    async def update_surge(surge_id: str, data: SurgeUpdate) -> Optional[SurgeMultiplier]:
        """Update a surge multiplier."""
        update_data = data.model_dump(exclude_unset=True)
        return await SurgeRepository.update(surge_id, update_data)
    
    @staticmethod
    async def deactivate_surge(surge_id: str) -> Optional[SurgeMultiplier]:
        """Deactivate a surge multiplier."""
        return await SurgeRepository.deactivate(surge_id)
    
    @staticmethod
    async def delete_surge(surge_id: str) -> bool:
        """Delete a surge multiplier."""
        return await SurgeRepository.delete(surge_id)
    
    # ============== Demand Analysis ==============
    
    @staticmethod
    async def get_demand_stats(origin: str, destination: str, days: int = 7) -> dict:
        """Get demand statistics for a route."""
        from src.guzo.bookings.core import Booking
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        bookings = await Booking.find(
            Booking.pickup_location == origin,
            Booking.dropoff_location == destination,
            Booking.created_at >= start_date,
        ).to_list()
        
        # Calculate stats
        total_bookings = len(bookings)
        
        # Group by day
        bookings_by_day = {}
        for b in bookings:
            day = b.created_at.date().isoformat()
            bookings_by_day[day] = bookings_by_day.get(day, 0) + 1
        
        avg_daily = total_bookings / days if days > 0 else 0
        
        return {
            "total_bookings": total_bookings,
            "avg_daily_bookings": round(avg_daily, 1),
            "bookings_by_day": bookings_by_day,
            "suggested_surge": 1.3 if avg_daily > 10 else 1.0,  # Simple suggestion
        }


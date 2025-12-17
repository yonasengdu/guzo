"""Analytics service - Business logic for analytics and reporting."""

from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import Booking, BookingStatus
from src.guzo.trips.core import DriverTrip, TripStatus
from src.guzo.analytics.core import (
    DateRange,
    DriverEarnings,
    PlatformStats,
    RoutePopularity,
    DemandHeatmap,
)


class AnalyticsService:
    """Service for analytics and reporting."""
    
    # ============== Driver Analytics ==============
    
    @staticmethod
    async def get_driver_earnings(
        driver_id: str,
        period: str = "month",
        custom_range: DateRange = None,
    ) -> DriverEarnings:
        """Get earnings analytics for a driver."""
        from beanie import PydanticObjectId
        
        # Calculate date range
        now = datetime.utcnow()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif period == "custom" and custom_range:
            start_date = custom_range.start_date
            end_date = custom_range.end_date
        else:
            start_date = now - timedelta(days=30)
            end_date = now
        
        # Get driver info
        driver = await User.get(PydanticObjectId(driver_id))
        driver_name = driver.full_name if driver else "Unknown"
        
        # Get completed bookings for driver
        bookings = await Booking.find(
            Booking.assigned_driver_id == driver_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.completed_at >= start_date,
            Booking.completed_at <= end_date,
        ).to_list()
        
        # Get trips
        trips = await DriverTrip.find(
            DriverTrip.driver_id == driver_id,
            DriverTrip.status == TripStatus.COMPLETED,
            DriverTrip.departure_time >= start_date,
            DriverTrip.departure_time <= end_date,
        ).to_list()
        
        # Calculate revenue
        total_revenue = sum(b.price or 0 for b in bookings)
        total_trips = len(trips)
        total_bookings = len(bookings)
        
        # Calculate averages
        avg_revenue_per_trip = total_revenue / total_trips if total_trips > 0 else 0
        
        # Revenue by day
        revenue_by_day = defaultdict(float)
        for b in bookings:
            if b.completed_at:
                day = b.completed_at.strftime("%Y-%m-%d")
                revenue_by_day[day] += b.price or 0
        
        # Top routes
        route_revenue = defaultdict(lambda: {"count": 0, "revenue": 0})
        for b in bookings:
            route_key = f"{b.pickup_location} → {b.dropoff_location}"
            route_revenue[route_key]["count"] += 1
            route_revenue[route_key]["revenue"] += b.price or 0
        
        top_routes = sorted(
            [
                {"route": k, "count": v["count"], "revenue": v["revenue"]}
                for k, v in route_revenue.items()
            ],
            key=lambda x: x["revenue"],
            reverse=True,
        )[:5]
        
        # Calculate change from previous period
        prev_start = start_date - (end_date - start_date)
        prev_bookings = await Booking.find(
            Booking.assigned_driver_id == driver_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.completed_at >= prev_start,
            Booking.completed_at < start_date,
        ).to_list()
        
        prev_revenue = sum(b.price or 0 for b in prev_bookings)
        if prev_revenue > 0:
            change_percent = ((total_revenue - prev_revenue) / prev_revenue) * 100
        else:
            change_percent = 100 if total_revenue > 0 else 0
        
        return DriverEarnings(
            driver_id=driver_id,
            driver_name=driver_name,
            period=period,
            total_revenue=round(total_revenue, 2),
            total_trips=total_trips,
            total_bookings=total_bookings,
            avg_revenue_per_trip=round(avg_revenue_per_trip, 2),
            avg_rating=driver.rating if driver else 5.0,
            revenue_by_day=dict(revenue_by_day),
            top_routes=top_routes,
            revenue_change_percent=round(change_percent, 1),
        )
    
    # ============== Platform Analytics ==============
    
    @staticmethod
    async def get_platform_stats(
        period: str = "month",
        custom_range: DateRange = None,
    ) -> PlatformStats:
        """Get platform-wide statistics."""
        # Calculate date range
        now = datetime.utcnow()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif period == "custom" and custom_range:
            start_date = custom_range.start_date
            end_date = custom_range.end_date
        else:
            start_date = now - timedelta(days=30)
            end_date = now
        
        # User stats
        all_users = await User.find_all().to_list()
        total_users = len(all_users)
        total_drivers = len([u for u in all_users if u.role == UserRole.DRIVER])
        total_customers = len([u for u in all_users if u.role == UserRole.RIDER])
        new_users = len([u for u in all_users if u.created_at >= start_date])
        active_users = len([u for u in all_users if u.last_login and u.last_login >= start_date])
        
        # Trip stats
        trips = await DriverTrip.find(
            DriverTrip.created_at >= start_date,
            DriverTrip.created_at <= end_date,
        ).to_list()
        total_trips = len(trips)
        
        # Booking stats
        bookings = await Booking.find(
            Booking.created_at >= start_date,
            Booking.created_at <= end_date,
        ).to_list()
        total_bookings = len(bookings)
        completed_bookings = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
        cancelled_bookings = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
        
        # Revenue
        total_revenue = sum(b.price or 0 for b in bookings if b.status == BookingStatus.COMPLETED)
        avg_booking_value = total_revenue / completed_bookings if completed_bookings > 0 else 0
        
        # Performance
        booking_completion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        drivers = [u for u in all_users if u.role == UserRole.DRIVER]
        avg_driver_rating = sum(d.rating for d in drivers) / len(drivers) if drivers else 5.0
        
        # Trends - revenue by day
        revenue_by_day = defaultdict(float)
        for b in bookings:
            if b.status == BookingStatus.COMPLETED:
                day = b.created_at.strftime("%Y-%m-%d")
                revenue_by_day[day] += b.price or 0
        
        # Bookings by day
        bookings_by_day = defaultdict(int)
        for b in bookings:
            day = b.created_at.strftime("%Y-%m-%d")
            bookings_by_day[day] += 1
        
        # Users by day
        users_by_day = defaultdict(int)
        for u in all_users:
            if u.created_at >= start_date:
                day = u.created_at.strftime("%Y-%m-%d")
                users_by_day[day] += 1
        
        return PlatformStats(
            period=period,
            total_users=total_users,
            total_drivers=total_drivers,
            total_customers=total_customers,
            new_users=new_users,
            active_users=active_users,
            total_trips=total_trips,
            total_bookings=total_bookings,
            completed_bookings=completed_bookings,
            cancelled_bookings=cancelled_bookings,
            total_revenue=round(total_revenue, 2),
            avg_booking_value=round(avg_booking_value, 2),
            booking_completion_rate=round(booking_completion_rate, 1),
            avg_driver_rating=round(avg_driver_rating, 2),
            revenue_by_day=dict(revenue_by_day),
            bookings_by_day=dict(bookings_by_day),
            users_by_day=dict(users_by_day),
        )
    
    # ============== Demand Analysis ==============
    
    @staticmethod
    async def get_demand_heatmap(
        days: int = 30,
    ) -> DemandHeatmap:
        """Get demand heatmap data."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        bookings = await Booking.find(
            Booking.created_at >= start_date,
        ).to_list()
        
        # Route popularity
        route_stats = defaultdict(lambda: {"count": 0, "revenue": 0})
        for b in bookings:
            route_key = (b.pickup_location, b.dropoff_location)
            route_stats[route_key]["count"] += 1
            route_stats[route_key]["revenue"] += b.price or 0
        
        routes = [
            RoutePopularity(
                origin=k[0],
                destination=k[1],
                total_bookings=v["count"],
                total_revenue=round(v["revenue"], 2),
                avg_price=round(v["revenue"] / v["count"], 2) if v["count"] > 0 else 0,
            )
            for k, v in route_stats.items()
        ]
        routes.sort(key=lambda x: x.total_bookings, reverse=True)
        
        # Peak hours
        peak_hours = defaultdict(int)
        for b in bookings:
            hour = b.scheduled_time.hour
            peak_hours[hour] += 1
        
        # Peak days
        peak_days = defaultdict(int)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for b in bookings:
            day_idx = b.scheduled_time.weekday()
            peak_days[day_names[day_idx]] += 1
        
        return DemandHeatmap(
            routes=routes[:20],  # Top 20 routes
            peak_hours=dict(peak_hours),
            peak_days=dict(peak_days),
        )
    
    @staticmethod
    async def calculate_surge_recommendation(
        origin: str,
        destination: str,
    ) -> dict:
        """Calculate surge pricing recommendation based on demand."""
        now = datetime.utcnow()
        hour = now.hour
        
        # Get recent bookings for this route
        start_date = now - timedelta(hours=24)
        bookings = await Booking.find(
            Booking.pickup_location == origin,
            Booking.dropoff_location == destination,
            Booking.created_at >= start_date,
        ).to_list()
        
        recent_count = len(bookings)
        
        # Simple recommendation logic
        if recent_count > 20:
            multiplier = 1.5
            reason = "high_demand"
        elif recent_count > 10:
            multiplier = 1.3
            reason = "moderate_demand"
        elif 7 <= hour <= 9 or 17 <= hour <= 19:
            multiplier = 1.2
            reason = "peak_hours"
        else:
            multiplier = 1.0
            reason = "normal"
        
        return {
            "recommended_multiplier": multiplier,
            "reason": reason,
            "recent_bookings": recent_count,
            "current_hour": hour,
        }


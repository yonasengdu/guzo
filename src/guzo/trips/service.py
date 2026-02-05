"""Trips domain service - business logic for trips."""

from datetime import datetime
from typing import Optional, List
from src.guzo.trips.core import DriverTrip, TripCreate, TripUpdate, TripResponse, TripSearch
from src.guzo.trips.repository import trip_repository
from src.guzo.auth.core import User


class TripService:
    """Service for managing driver trips."""
    
    @staticmethod
    async def create_trip(driver_id: str, trip_data: TripCreate) -> DriverTrip:
        """Create a new trip with full validation.
        
        Validates:
        - Driver exists and is active
        - departure_time is in the future
        - whole_car_price >= price_per_seat * available_seats (business logic consistency)
        """
        from beanie import PydanticObjectId
        from src.guzo.auth.core import UserRole
        
        # Validate driver exists and is active
        try:
            driver_oid = PydanticObjectId(driver_id)
        except Exception:
            raise ValueError("Invalid driver ID format")
        
        driver = await User.get(driver_oid)
        if not driver:
            raise ValueError("Driver not found")
        
        if driver.role != UserRole.DRIVER:
            raise ValueError("User is not a driver")
        
        if not driver.is_active:
            raise ValueError("Driver account is not active")
        
        # Validate departure_time is in the future
        if trip_data.departure_time <= datetime.utcnow():
            raise ValueError("Departure time must be in the future")
        
        # Validate pricing consistency
        # whole_car_price should be at least as much as booking all seats individually
        min_whole_car_price = trip_data.price_per_seat * trip_data.available_seats
        if trip_data.whole_car_price < min_whole_car_price:
            raise ValueError(
                f"Whole car price ({trip_data.whole_car_price}) must be at least "
                f"price_per_seat * available_seats ({min_whole_car_price})"
            )
        
        trip = DriverTrip(
            driver_id=driver_id,
            vehicle_id=trip_data.vehicle_id,
            origin=trip_data.origin,
            destination=trip_data.destination,
            departure_time=trip_data.departure_time,
            available_seats=trip_data.available_seats,
            price_per_seat=trip_data.price_per_seat,
            whole_car_price=trip_data.whole_car_price,
            notes=trip_data.notes,
            waypoints=trip_data.waypoints,
        )
        await trip_repository.create(trip)
        return trip
    
    @staticmethod
    async def get_trip(trip_id: str) -> Optional[DriverTrip]:
        """Get a trip by ID."""
        return await trip_repository.get_by_id(trip_id)
    
    @staticmethod
    async def update_trip(trip_id: str, trip_data: TripUpdate) -> Optional[DriverTrip]:
        """Update a trip."""
        update_data = trip_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            return await trip_repository.update(trip_id, update_data)
        return await trip_repository.get_by_id(trip_id)
    
    @staticmethod
    async def delete_trip(trip_id: str) -> bool:
        """Delete a trip."""
        return await trip_repository.delete(trip_id)
    
    @staticmethod
    async def search_trips(search: TripSearch) -> List[DriverTrip]:
        """Search for available trips."""
        return await trip_repository.search(
            origin=search.origin,
            destination=search.destination,
            date=search.date,
            min_seats=search.min_seats,
        )
    
    @staticmethod
    async def get_driver_trips(
        driver_id: str, 
        include_past: bool = False,
        upcoming_only: bool = False,
    ) -> List[DriverTrip]:
        """Get all trips for a driver."""
        return await trip_repository.get_by_driver(driver_id, include_past)
    
    @staticmethod
    async def get_upcoming_trips(limit: int = 20) -> List[DriverTrip]:
        """Get upcoming trips for the landing page."""
        return await trip_repository.get_upcoming(limit)
    
    @staticmethod
    async def get_trip_with_driver(trip_id: str) -> Optional[TripResponse]:
        """Get trip with driver details."""
        trip = await trip_repository.get_by_id(trip_id)
        if not trip:
            return None
        
        driver = await User.get(trip.driver_id)
        
        return TripResponse(
            id=str(trip.id),
            driver_id=trip.driver_id,
            driver_name=driver.full_name if driver else None,
            driver_phone=driver.phone if driver else None,
            driver_rating=driver.rating if driver else None,
            vehicle_id=trip.vehicle_id,
            origin=trip.origin,
            destination=trip.destination,
            departure_time=trip.departure_time,
            available_seats=trip.available_seats,
            booked_seats=trip.booked_seats,
            remaining_seats=trip.remaining_seats,
            price_per_seat=trip.price_per_seat,
            whole_car_price=trip.whole_car_price,
            status=trip.status,
            notes=trip.notes,
            created_at=trip.created_at,
        )
    
    @staticmethod
    async def book_seats(trip_id: str, seats: int) -> bool:
        """Book seats on a trip."""
        return await trip_repository.book_seats(trip_id, seats)
    
    @staticmethod
    async def release_seats(trip_id: str, seats: int) -> bool:
        """Release booked seats on a trip."""
        return await trip_repository.release_seats(trip_id, seats)
    
    @staticmethod
    async def get_suggested_pricing(origin: str, destination: str) -> dict:
        """Get suggested pricing for a route based on dynamic pricing rules."""
        from src.guzo.pricing.service import PricingService
        
        return await PricingService.get_suggested_price(origin, destination)


"""Trips domain repository - database operations for trips."""

from datetime import datetime, timedelta
from typing import Optional, List
from src.guzo.trips.core import DriverTrip, TripStatus
from src.guzo.infrastructure.repository import BaseRepository


class TripRepository(BaseRepository[DriverTrip]):
    """Repository for Trip database operations."""
    
    def __init__(self):
        super().__init__(DriverTrip)
    
    async def get_by_driver(
        self, driver_id: str, include_past: bool = False
    ) -> List[DriverTrip]:
        """Get all trips for a driver."""
        query = {"driver_id": driver_id}
        if not include_past:
            query["departure_time"] = {"$gte": datetime.utcnow()}
        
        return await DriverTrip.find(query).sort("-departure_time").to_list()
    
    async def get_upcoming(self, limit: int = 20) -> List[DriverTrip]:
        """Get upcoming scheduled trips with available seats."""
        return await DriverTrip.find(
            {
                "status": TripStatus.SCHEDULED,
                "departure_time": {"$gte": datetime.utcnow()},
                "$expr": {"$gt": ["$available_seats", "$booked_seats"]},
            }
        ).sort("departure_time").limit(limit).to_list()
    
    async def search(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        date: Optional[datetime] = None,
        min_seats: int = 1,
    ) -> List[DriverTrip]:
        """Search for available trips."""
        query = {"status": TripStatus.SCHEDULED}
        
        if origin:
            query["origin"] = {"$regex": origin, "$options": "i"}
        if destination:
            query["destination"] = {"$regex": destination, "$options": "i"}
        if date:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query["departure_time"] = {"$gte": start_of_day, "$lt": end_of_day}
        
        # Only get trips with available seats
        query["$expr"] = {"$gt": ["$available_seats", "$booked_seats"]}
        
        trips = await DriverTrip.find(query).sort("departure_time").to_list()
        return [t for t in trips if t.remaining_seats >= min_seats]
    
    async def book_seats(self, trip_id: str, seats: int) -> bool:
        """Book seats on a trip."""
        trip = await self.get_by_id(trip_id)
        if not trip or trip.remaining_seats < seats:
            return False
        
        trip.booked_seats += seats
        trip.updated_at = datetime.utcnow()
        await trip.save()
        return True
    
    async def release_seats(self, trip_id: str, seats: int) -> bool:
        """Release booked seats on a trip."""
        trip = await self.get_by_id(trip_id)
        if not trip:
            return False
        
        trip.booked_seats = max(0, trip.booked_seats - seats)
        trip.updated_at = datetime.utcnow()
        await trip.save()
        return True
    
    async def update_status(self, trip_id: str, status: TripStatus) -> Optional[DriverTrip]:
        """Update trip status."""
        trip = await self.get_by_id(trip_id)
        if trip:
            trip.status = status
            trip.updated_at = datetime.utcnow()
            await trip.save()
            return trip
        return None


# Singleton instance
trip_repository = TripRepository()


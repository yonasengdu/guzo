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
        """
        Atomically book seats on a trip.
        Uses MongoDB's findAndModify to prevent race conditions.
        """
        from beanie import PydanticObjectId
        
        try:
            trip_oid = PydanticObjectId(trip_id)
        except Exception:
            return False
        
        # Atomic update: only succeeds if there are enough available seats
        # $expr compares available_seats - booked_seats >= seats
        result = await DriverTrip.find_one(
            {
                "_id": trip_oid,
                "status": TripStatus.SCHEDULED,
                "$expr": {"$gte": [{"$subtract": ["$available_seats", "$booked_seats"]}, seats]},
            }
        ).update(
            {
                "$inc": {"booked_seats": seats},
                "$set": {"updated_at": datetime.utcnow()},
            }
        )
        
        return result is not None and result.modified_count > 0
    
    async def release_seats(self, trip_id: str, seats: int) -> bool:
        """
        Atomically release booked seats on a trip.
        Ensures booked_seats doesn't go below 0.
        """
        from beanie import PydanticObjectId
        
        try:
            trip_oid = PydanticObjectId(trip_id)
        except Exception:
            return False
        
        # First check if trip exists and has enough booked seats
        trip = await DriverTrip.find_one({"_id": trip_oid})
        if not trip:
            return False
        
        # Calculate the actual seats to release (don't go below 0)
        actual_release = min(seats, trip.booked_seats)
        
        # Atomic decrement
        result = await DriverTrip.find_one(
            {
                "_id": trip_oid,
                "booked_seats": {"$gte": actual_release},
            }
        ).update(
            {
                "$inc": {"booked_seats": -actual_release},
                "$set": {"updated_at": datetime.utcnow()},
            }
        )
        
        return result is not None and result.modified_count > 0
    
    # Valid status transitions for trips
    VALID_STATUS_TRANSITIONS = {
        TripStatus.SCHEDULED: {TripStatus.IN_PROGRESS, TripStatus.CANCELLED},
        TripStatus.IN_PROGRESS: {TripStatus.COMPLETED, TripStatus.CANCELLED},
        TripStatus.COMPLETED: set(),  # Terminal state
        TripStatus.CANCELLED: set(),  # Terminal state
    }
    
    @classmethod
    def is_valid_status_transition(cls, current: TripStatus, new: TripStatus) -> bool:
        """Check if a status transition is valid."""
        return new in cls.VALID_STATUS_TRANSITIONS.get(current, set())
    
    async def update_status(
        self, trip_id: str, status: TripStatus, force: bool = False
    ) -> Optional[DriverTrip]:
        """
        Update trip status with transition validation.
        
        Args:
            trip_id: The trip ID to update
            status: The new status
            force: If True, skip transition validation (admin override)
        """
        trip = await self.get_by_id(trip_id)
        if not trip:
            return None
        
        # Validate status transition
        if not force and not self.is_valid_status_transition(trip.status, status):
            raise ValueError(
                f"Invalid status transition: {trip.status.value} -> {status.value}. "
                f"Valid transitions from {trip.status.value}: "
                f"{[s.value for s in self.VALID_STATUS_TRANSITIONS.get(trip.status, set())]}"
            )
        
        trip.status = status
        trip.updated_at = datetime.utcnow()
        await trip.save()
        return trip


# Singleton instance
trip_repository = TripRepository()


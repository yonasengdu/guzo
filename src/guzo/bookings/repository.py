"""Bookings domain repository - database operations for bookings."""

from datetime import datetime
from typing import Optional, List
from src.guzo.bookings.core import Booking, BookingType, BookingStatus
from src.guzo.infrastructure.repository import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Repository for Booking database operations."""
    
    def __init__(self):
        super().__init__(Booking)
    
    async def get_by_customer(self, customer_id: str) -> List[Booking]:
        """Get all bookings for a customer."""
        return await Booking.find(
            Booking.customer_id == customer_id
        ).sort("-created_at").to_list()
    
    async def get_by_driver(self, driver_id: str) -> List[Booking]:
        """Get all bookings assigned to a driver."""
        return await Booking.find(
            Booking.assigned_driver_id == driver_id
        ).sort("-created_at").to_list()
    
    async def get_by_trip(self, trip_id: str) -> List[Booking]:
        """Get all bookings for a trip."""
        return await Booking.find(
            Booking.trip_id == trip_id
        ).sort("-created_at").to_list()
    
    async def get_pending_charters(self) -> List[Booking]:
        """Get all pending charter requests."""
        return await Booking.find(
            {
                "booking_type": BookingType.CHARTER,
                "status": BookingStatus.PENDING,
                "trip_id": None,
            }
        ).sort("-created_at").to_list()
    
    async def get_by_status(
        self, status: BookingStatus, limit: int = 100
    ) -> List[Booking]:
        """Get all bookings with a specific status."""
        return await Booking.find(
            Booking.status == status
        ).sort("-created_at").limit(limit).to_list()
    
    # Valid status transitions for bookings
    VALID_STATUS_TRANSITIONS = {
        BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
        BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
        BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
        BookingStatus.COMPLETED: set(),  # Terminal state
        BookingStatus.CANCELLED: set(),  # Terminal state
    }
    
    @classmethod
    def is_valid_status_transition(cls, current: BookingStatus, new: BookingStatus) -> bool:
        """Check if a status transition is valid."""
        return new in cls.VALID_STATUS_TRANSITIONS.get(current, set())
    
    async def update_status(
        self, booking_id: str, status: BookingStatus, force: bool = False
    ) -> Optional[Booking]:
        """
        Update booking status with transition validation.
        
        Args:
            booking_id: The booking ID to update
            status: The new status
            force: If True, skip transition validation (admin override)
        """
        booking = await self.get_by_id(booking_id)
        if not booking:
            return None
        
        # Validate status transition
        if not force and not self.is_valid_status_transition(booking.status, status):
            raise ValueError(
                f"Invalid status transition: {booking.status.value} -> {status.value}. "
                f"Valid transitions from {booking.status.value}: "
                f"{[s.value for s in self.VALID_STATUS_TRANSITIONS.get(booking.status, set())]}"
            )
        
        booking.status = status
        booking.updated_at = datetime.utcnow()
        
        if status == BookingStatus.CONFIRMED:
            booking.confirmed_at = datetime.utcnow()
        elif status == BookingStatus.COMPLETED:
            booking.completed_at = datetime.utcnow()
        
        await booking.save()
        return booking
    
    async def assign_driver(
        self,
        booking_id: str,
        driver_id: str,
        trip_id: Optional[str] = None,
        price: Optional[float] = None,
    ) -> Optional[Booking]:
        """
        Assign a driver to a booking.
        
        Note: This method only updates the driver assignment fields.
        Status changes should be handled by the service layer.
        """
        booking = await self.get_by_id(booking_id)
        if not booking:
            return None
        
        booking.assigned_driver_id = driver_id
        booking.updated_at = datetime.utcnow()
        
        if trip_id:
            booking.trip_id = trip_id
        if price:
            booking.price = price
        
        await booking.save()
        return booking


# Singleton instance
booking_repository = BookingRepository()


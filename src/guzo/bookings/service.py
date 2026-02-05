"""Bookings domain service - business logic for bookings."""

from datetime import datetime
from typing import Optional, List
from src.guzo.bookings.core import (
    Booking, BookingType, BookingStatus, 
    BookingCreate, BookingUpdate, BookingResponse
)
from src.guzo.bookings.repository import booking_repository
from src.guzo.auth.core import User


# Valid status transitions for bookings
VALID_STATUS_TRANSITIONS = {
    BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
    BookingStatus.CONFIRMED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED],
    BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED, BookingStatus.CANCELLED],
    BookingStatus.COMPLETED: [],  # Terminal state
    BookingStatus.CANCELLED: [],  # Terminal state
}


class BookingService:
    """Service for managing bookings."""
    
    @staticmethod
    async def create_booking(
        booking_data: BookingCreate,
        customer_id: Optional[str] = None
    ) -> Booking:
        """Create a new booking with full validation.
        
        Validates:
        - Trip exists and is SCHEDULED (if trip_id provided)
        - scheduled_time is in the future
        - seats_booked doesn't exceed trip capacity
        - Customer isn't already on this trip
        """
        from src.guzo.trips.core import DriverTrip, TripStatus
        from src.guzo.trips.service import TripService
        from beanie import PydanticObjectId
        
        # Validate scheduled_time is in the future
        if booking_data.scheduled_time <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        
        # Calculate price and validate trip if booking a trip
        price = None
        if booking_data.trip_id:
            try:
                trip_oid = PydanticObjectId(booking_data.trip_id)
            except Exception:
                raise ValueError("Invalid trip ID format")
            
            trip = await DriverTrip.get(trip_oid)
            
            # Validate trip exists
            if not trip:
                raise ValueError("Trip not found")
            
            # Validate trip status is SCHEDULED
            if trip.status != TripStatus.SCHEDULED:
                raise ValueError(f"Trip is not available for booking (status: {trip.status})")
            
            # Validate trip departure is in the future
            if trip.departure_time <= datetime.utcnow():
                raise ValueError("Trip has already departed")
            
            # Validate seats don't exceed capacity
            if booking_data.seats_booked > trip.available_seats:
                raise ValueError(f"Requested seats ({booking_data.seats_booked}) exceed trip capacity ({trip.available_seats})")
            
            # Check if customer already has a booking on this trip
            if customer_id:
                existing_booking = await Booking.find_one(
                    Booking.trip_id == booking_data.trip_id,
                    Booking.customer_id == customer_id,
                    Booking.status.nin_([BookingStatus.CANCELLED])  # Exclude cancelled bookings
                )
                if existing_booking:
                    raise ValueError("You already have a booking on this trip")
            
            # Calculate price
            if booking_data.booking_type == BookingType.WHOLE_CAR:
                price = trip.whole_car_price
            else:
                price = trip.price_per_seat * booking_data.seats_booked
            
            # Book the seats (atomic operation handles race conditions)
            success = await TripService.book_seats(
                booking_data.trip_id, 
                booking_data.seats_booked
            )
            if not success:
                raise ValueError("Not enough seats available")
        
        booking = Booking(
            customer_id=customer_id,
            customer_name=booking_data.customer_name,
            customer_phone=booking_data.customer_phone,
            trip_id=booking_data.trip_id,
            booking_type=booking_data.booking_type,
            pickup_location=booking_data.pickup_location,
            dropoff_location=booking_data.dropoff_location,
            scheduled_time=booking_data.scheduled_time,
            seats_booked=booking_data.seats_booked,
            price=price,
            notes=booking_data.notes,
            special_requests=booking_data.special_requests,
        )
        await booking_repository.create(booking)
        return booking
    
    @staticmethod
    async def get_booking(booking_id: str) -> Optional[Booking]:
        """Get a booking by ID."""
        return await booking_repository.get_by_id(booking_id)
    
    @staticmethod
    async def update_booking(
        booking_id: str,
        booking_data: BookingUpdate
    ) -> Optional[Booking]:
        """Update a booking with status transition validation.
        
        Valid status transitions:
        - PENDING -> CONFIRMED, CANCELLED
        - CONFIRMED -> IN_PROGRESS, CANCELLED  
        - IN_PROGRESS -> COMPLETED, CANCELLED
        - COMPLETED -> (terminal state)
        - CANCELLED -> (terminal state)
        """
        update_data = booking_data.model_dump(exclude_unset=True)
        if not update_data:
            return await booking_repository.get_by_id(booking_id)
        
        # If status is being changed, validate the transition
        if "status" in update_data:
            new_status = update_data["status"]
            
            # Get current booking to check current status
            current_booking = await booking_repository.get_by_id(booking_id)
            if not current_booking:
                return None
            
            current_status = current_booking.status
            
            # Validate status transition
            valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in valid_transitions:
                raise ValueError(
                    f"Invalid status transition: {current_status} -> {new_status}. "
                    f"Valid transitions from {current_status}: {valid_transitions}"
                )
            
            # Set timestamps based on new status
            if new_status == BookingStatus.CONFIRMED:
                update_data["confirmed_at"] = datetime.utcnow()
            elif new_status == BookingStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
        
        update_data["updated_at"] = datetime.utcnow()
        return await booking_repository.update(booking_id, update_data)
    
    @staticmethod
    async def cancel_booking(booking_id: str) -> bool:
        """
        Cancel a booking and release seats.
        Uses atomic update to prevent double-cancellation race condition.
        """
        from src.guzo.trips.service import TripService
        from beanie import PydanticObjectId
        
        try:
            booking_oid = PydanticObjectId(booking_id)
        except Exception:
            return False
        
        # Atomically update status only if not already cancelled/completed
        # This prevents releasing seats multiple times
        result = await Booking.find_one(
            {
                "_id": booking_oid,
                "status": {"$nin": [BookingStatus.CANCELLED, BookingStatus.COMPLETED]},
            }
        ).update(
            {
                "$set": {
                    "status": BookingStatus.CANCELLED,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        if result is None or result.modified_count == 0:
            return False
        
        # Get the booking to release seats
        booking = await booking_repository.get_by_id(booking_id)
        if booking and booking.trip_id:
            await TripService.release_seats(booking.trip_id, booking.seats_booked)
        
        return True
    
    @staticmethod
    async def get_customer_bookings(customer_id: str) -> List[Booking]:
        """Get all bookings for a customer."""
        return await booking_repository.get_by_customer(customer_id)
    
    @staticmethod
    async def get_driver_bookings(driver_id: str) -> List[Booking]:
        """Get all bookings assigned to a driver."""
        return await booking_repository.get_by_driver(driver_id)
    
    @staticmethod
    async def get_trip_bookings(trip_id: str) -> List[Booking]:
        """Get all bookings for a trip."""
        return await booking_repository.get_by_trip(trip_id)
    
    @staticmethod
    async def get_pending_requests() -> List[Booking]:
        """Get all pending charter/custom requests."""
        return await booking_repository.get_pending_charters()
    
    @staticmethod
    async def assign_driver(
        booking_id: str,
        driver_id: str,
        trip_id: Optional[str] = None,
        price: Optional[float] = None,
        auto_confirm: bool = True
    ) -> Optional[Booking]:
        """
        Assign a driver to a booking.
        
        Args:
            booking_id: The booking to assign
            driver_id: The driver to assign
            trip_id: Optional trip ID to link
            price: Optional price to set
            auto_confirm: If True, automatically confirms the booking (default)
        """
        # First, assign the driver
        booking = await booking_repository.assign_driver(
            booking_id, driver_id, trip_id, price
        )
        
        if not booking:
            return None
        
        # Then, handle status change (business logic in service layer)
        if auto_confirm and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_at = datetime.utcnow()
            booking.updated_at = datetime.utcnow()
            await booking.save()
        
        return booking
    
    @staticmethod
    async def get_booking_with_details(booking_id: str) -> Optional[BookingResponse]:
        """Get booking with driver details."""
        booking = await booking_repository.get_by_id(booking_id)
        if not booking:
            return None
        
        driver_name = None
        driver_phone = None
        if booking.assigned_driver_id:
            driver = await User.get(booking.assigned_driver_id)
            if driver:
                driver_name = driver.full_name
                driver_phone = driver.phone
        
        return BookingResponse(
            id=str(booking.id),
            customer_id=booking.customer_id,
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            trip_id=booking.trip_id,
            booking_type=booking.booking_type,
            pickup_location=booking.pickup_location,
            dropoff_location=booking.dropoff_location,
            scheduled_time=booking.scheduled_time,
            seats_booked=booking.seats_booked,
            price=booking.price,
            status=booking.status,
            assigned_driver_id=booking.assigned_driver_id,
            driver_name=driver_name,
            driver_phone=driver_phone,
            notes=booking.notes,
            created_at=booking.created_at,
        )
    
    @staticmethod
    async def get_all_bookings(
        status: Optional[BookingStatus] = None,
        limit: int = 100
    ) -> List[Booking]:
        """Get all bookings (for admin)."""
        if status:
            return await booking_repository.get_by_status(status, limit)
        return await booking_repository.get_all(limit)


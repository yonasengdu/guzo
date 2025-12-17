"""Bookings domain service - business logic for bookings."""

from datetime import datetime
from typing import Optional, List
from src.guzo.bookings.core import (
    Booking, BookingType, BookingStatus, 
    BookingCreate, BookingUpdate, BookingResponse
)
from src.guzo.bookings.repository import booking_repository
from src.guzo.auth.core import User


class BookingService:
    """Service for managing bookings."""
    
    @staticmethod
    async def create_booking(
        booking_data: BookingCreate,
        customer_id: Optional[str] = None
    ) -> Booking:
        """Create a new booking."""
        from src.guzo.trips.core import DriverTrip
        from src.guzo.trips.service import TripService
        
        # Calculate price if booking a trip
        price = None
        if booking_data.trip_id:
            trip = await DriverTrip.get(booking_data.trip_id)
            if trip:
                if booking_data.booking_type == BookingType.WHOLE_CAR:
                    price = trip.whole_car_price
                else:
                    price = trip.price_per_seat * booking_data.seats_booked
                
                # Book the seats
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
        """Update a booking."""
        update_data = booking_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            if "status" in update_data:
                if update_data["status"] == BookingStatus.CONFIRMED:
                    update_data["confirmed_at"] = datetime.utcnow()
                elif update_data["status"] == BookingStatus.COMPLETED:
                    update_data["completed_at"] = datetime.utcnow()
            
            return await booking_repository.update(booking_id, update_data)
        return await booking_repository.get_by_id(booking_id)
    
    @staticmethod
    async def cancel_booking(booking_id: str) -> bool:
        """Cancel a booking and release seats."""
        from src.guzo.trips.service import TripService
        
        booking = await booking_repository.get_by_id(booking_id)
        if not booking:
            return False
        
        # Release seats if this was a trip booking
        if booking.trip_id:
            await TripService.release_seats(booking.trip_id, booking.seats_booked)
        
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow()
        await booking.save()
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
        price: Optional[float] = None
    ) -> Optional[Booking]:
        """Assign a driver to a booking."""
        return await booking_repository.assign_driver(
            booking_id, driver_id, trip_id, price
        )
    
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


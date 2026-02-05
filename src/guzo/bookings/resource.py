"""Bookings domain resource - API routes for bookings (customer functionality)."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import BookingType, BookingStatus, BookingCreate, BookingResponse
from src.guzo.bookings.service import BookingService
from src.guzo.trips.core import TripSearch, TripResponse
from src.guzo.trips.service import TripService
from src.guzo.middleware import get_current_user, get_current_user_required

router = APIRouter(prefix="/customer", tags=["Customer"])


# ============== Request/Response Models ==============

class BookingCreateRequest(BaseModel):
    """Request model for creating a booking."""
    trip_id: Optional[str] = None
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    seats_booked: int = 1
    booking_type: BookingType = BookingType.SEAT
    notes: Optional[str] = None


class CharterRequest(BaseModel):
    """Request model for charter booking."""
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    notes: Optional[str] = None


class RebookResponse(BaseModel):
    """Response model for rebook endpoint."""
    pickup_location: str
    dropoff_location: str
    seats_booked: int


# ============== Endpoints ==============

@router.get("/bookings", response_model=list[BookingResponse])
async def get_my_bookings(
    user: User = Depends(get_current_user_required),
    status: Optional[BookingStatus] = None,
):
    """Get current user's bookings."""
    bookings = await BookingService.get_customer_bookings(str(user.id), status=status)
    return [
        BookingResponse(
            id=str(b.id),
            customer_id=b.customer_id,
            customer_name=b.customer_name,
            customer_phone=b.customer_phone,
            trip_id=b.trip_id,
            booking_type=b.booking_type,
            pickup_location=b.pickup_location,
            dropoff_location=b.dropoff_location,
            scheduled_time=b.scheduled_time,
            seats_booked=b.seats_booked,
            price=b.price,
            status=b.status,
            assigned_driver_id=b.assigned_driver_id,
            notes=b.notes,
            customer_review_id=b.customer_review_id,
            driver_review_id=b.driver_review_id,
            created_at=b.created_at,
            completed_at=b.completed_at,
        )
        for b in bookings
    ]


@router.get("/trips/search", response_model=list[TripResponse])
async def search_trips(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[datetime] = None,
    seats: int = Query(1, ge=1),
):
    """Search available trips."""
    search = TripSearch(
        origin=origin,
        destination=destination,
        date=date,
        min_seats=seats,
    )
    trips = await TripService.search_trips(search)
    return [
        TripResponse(
            id=str(t.id),
            driver_id=t.driver_id,
            driver_name=getattr(t, 'driver_name', None),
            driver_phone=getattr(t, 'driver_phone', None),
            driver_rating=getattr(t, 'driver_rating', None),
            vehicle_id=t.vehicle_id,
            origin=t.origin,
            destination=t.destination,
            departure_time=t.departure_time,
            available_seats=t.available_seats,
            booked_seats=t.booked_seats,
            remaining_seats=t.available_seats - t.booked_seats,
            price_per_seat=t.price_per_seat,
            whole_car_price=t.whole_car_price,
            status=t.status,
            notes=t.notes,
            created_at=t.created_at,
        )
        for t in trips
    ]


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str):
    """Get trip details."""
    trip = await TripService.get_trip_with_driver(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return TripResponse(
        id=str(trip.id),
        driver_id=trip.driver_id,
        driver_name=getattr(trip, 'driver_name', None),
        driver_phone=getattr(trip, 'driver_phone', None),
        driver_rating=getattr(trip, 'driver_rating', None),
        vehicle_id=trip.vehicle_id,
        origin=trip.origin,
        destination=trip.destination,
        departure_time=trip.departure_time,
        available_seats=trip.available_seats,
        booked_seats=trip.booked_seats,
        remaining_seats=trip.available_seats - trip.booked_seats,
        price_per_seat=trip.price_per_seat,
        whole_car_price=trip.whole_car_price,
        status=trip.status,
        notes=trip.notes,
        created_at=trip.created_at,
    )


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking_request: BookingCreateRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a new booking."""
    booking_data = BookingCreate(
        trip_id=booking_request.trip_id,
        customer_name=user.full_name,
        customer_phone=user.phone,
        pickup_location=booking_request.pickup_location,
        dropoff_location=booking_request.dropoff_location,
        scheduled_time=booking_request.scheduled_time,
        seats_booked=booking_request.seats_booked,
        booking_type=booking_request.booking_type,
        notes=booking_request.notes,
    )
    
    try:
        booking = await BookingService.create_booking(
            booking_data,
            customer_id=str(user.id),
        )
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
            notes=booking.notes,
            created_at=booking.created_at,
            completed_at=booking.completed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/charter", response_model=BookingResponse)
async def create_charter(
    charter_request: CharterRequest,
    user: User = Depends(get_current_user_required),
):
    """Request a charter (custom trip)."""
    booking_data = BookingCreate(
        trip_id=None,
        customer_name=user.full_name,
        customer_phone=user.phone,
        pickup_location=charter_request.pickup_location,
        dropoff_location=charter_request.dropoff_location,
        scheduled_time=charter_request.scheduled_time,
        seats_booked=1,
        booking_type=BookingType.CHARTER,
        notes=charter_request.notes,
    )
    
    try:
        booking = await BookingService.create_booking(
            booking_data,
            customer_id=str(user.id),
        )
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
            notes=booking.notes,
            created_at=booking.created_at,
            completed_at=booking.completed_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Cancel a booking (state change)."""
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = await BookingService.cancel_booking(booking_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel booking")
    
    # Fetch updated booking
    updated_booking = await BookingService.get_booking(booking_id)
    return BookingResponse(
        id=str(updated_booking.id),
        customer_id=updated_booking.customer_id,
        customer_name=updated_booking.customer_name,
        customer_phone=updated_booking.customer_phone,
        trip_id=updated_booking.trip_id,
        booking_type=updated_booking.booking_type,
        pickup_location=updated_booking.pickup_location,
        dropoff_location=updated_booking.dropoff_location,
        scheduled_time=updated_booking.scheduled_time,
        seats_booked=updated_booking.seats_booked,
        price=updated_booking.price,
        status=updated_booking.status,
        assigned_driver_id=updated_booking.assigned_driver_id,
        notes=updated_booking.notes,
        created_at=updated_booking.created_at,
        completed_at=updated_booking.completed_at,
    )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get a specific booking."""
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
        notes=booking.notes,
        customer_review_id=booking.customer_review_id,
        driver_review_id=booking.driver_review_id,
        created_at=booking.created_at,
        completed_at=booking.completed_at,
    )


@router.get("/bookings/{booking_id}/rebook", response_model=RebookResponse)
async def get_rebook_info(
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get booking info for rebooking."""
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != str(user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return RebookResponse(
        pickup_location=booking.pickup_location,
        dropoff_location=booking.dropoff_location,
        seats_booked=booking.seats_booked,
    )

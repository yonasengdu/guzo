"""Trips domain resource - API routes for trips (driver functionality)."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.guzo.auth.core import User, UserRole
from src.guzo.auth.service import AuthService
from src.guzo.trips.core import TripStatus, TripCreate, TripUpdate, TripResponse
from src.guzo.trips.service import TripService
from src.guzo.bookings.core import BookingResponse, BookingStatus
from src.guzo.middleware import get_current_driver
from src.guzo.analytics.core import DriverEarnings

router = APIRouter(prefix="/driver", tags=["Driver"])


# ============== Request/Response Models ==============

class OnlineStatusResponse(BaseModel):
    """Response for online status toggle."""
    is_online: bool


class AcceptRequestPayload(BaseModel):
    """Payload for accepting a charter request."""
    trip_id: Optional[str] = None
    price: Optional[float] = None


class ScheduleDay(BaseModel):
    """Schedule for a single day."""
    enabled: bool
    start: str = "08:00"
    end: str = "18:00"


class ScheduleUpdate(BaseModel):
    """Schedule update payload."""
    monday: Optional[ScheduleDay] = None
    tuesday: Optional[ScheduleDay] = None
    wednesday: Optional[ScheduleDay] = None
    thursday: Optional[ScheduleDay] = None
    friday: Optional[ScheduleDay] = None
    saturday: Optional[ScheduleDay] = None
    sunday: Optional[ScheduleDay] = None


class PricingSuggestion(BaseModel):
    """Pricing suggestion response."""
    price_per_seat: float
    whole_car_price: float
    is_surge: bool
    surge_info: Optional[str] = None


class DriverDashboardResponse(BaseModel):
    """Response for driver dashboard data."""
    trips: list[TripResponse]
    bookings: list[BookingResponse]


class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: Optional[str] = None


# ============== Endpoints ==============

@router.get("/dashboard", response_model=DriverDashboardResponse)
async def get_driver_dashboard(user: User = Depends(get_current_driver)):
    """Get driver dashboard data."""
    from src.guzo.bookings.service import BookingService
    
    trips = await TripService.get_driver_trips(str(user.id))
    bookings = await BookingService.get_driver_bookings(str(user.id))
    pending_requests = await BookingService.get_pending_requests()
    
    return DriverDashboardResponse(
        trips=[
            TripResponse(
                id=str(t.id),
                driver_id=t.driver_id,
                driver_name=getattr(t, 'driver_name', None),
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
        ],
        bookings=[
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
                created_at=b.created_at,
                completed_at=b.completed_at,
            )
            for b in bookings
        ],
        pending_requests=[
            BookingResponse(
                id=str(r.id),
                customer_id=r.customer_id,
                customer_name=r.customer_name,
                customer_phone=r.customer_phone,
                trip_id=r.trip_id,
                booking_type=r.booking_type,
                pickup_location=r.pickup_location,
                dropoff_location=r.dropoff_location,
                scheduled_time=r.scheduled_time,
                seats_booked=r.seats_booked,
                price=r.price,
                status=r.status,
                assigned_driver_id=r.assigned_driver_id,
                notes=r.notes,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in pending_requests
        ],
    )


@router.patch("/status", response_model=OnlineStatusResponse)
async def toggle_online_status(user: User = Depends(get_current_driver)):
    """Toggle driver online/offline status (state change)."""
    updated_user = await AuthService.toggle_online_status(user)
    return OnlineStatusResponse(is_online=updated_user.is_online)


@router.get("/trips", response_model=list[TripResponse])
async def get_driver_trips(
    user: User = Depends(get_current_driver),
    upcoming_only: bool = False,
):
    """Get driver's trips."""
    trips = await TripService.get_driver_trips(str(user.id), upcoming_only=upcoming_only)
    return [
        TripResponse(
            id=str(t.id),
            driver_id=t.driver_id,
            driver_name=getattr(t, 'driver_name', None),
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


@router.post("/trips", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    user: User = Depends(get_current_driver),
):
    """Create a new trip."""
    try:
        trip = await TripService.create_trip(str(user.id), trip_data)
        return TripResponse(
            id=str(trip.id),
            driver_id=trip.driver_id,
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    update_data: TripUpdate,
    user: User = Depends(get_current_driver),
):
    """Update a trip."""
    trip = await TripService.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated_trip = await TripService.update_trip(trip_id, update_data)
    return TripResponse(
        id=str(updated_trip.id),
        driver_id=updated_trip.driver_id,
        vehicle_id=updated_trip.vehicle_id,
        origin=updated_trip.origin,
        destination=updated_trip.destination,
        departure_time=updated_trip.departure_time,
        available_seats=updated_trip.available_seats,
        booked_seats=updated_trip.booked_seats,
        remaining_seats=updated_trip.available_seats - updated_trip.booked_seats,
        price_per_seat=updated_trip.price_per_seat,
        whole_car_price=updated_trip.whole_car_price,
        status=updated_trip.status,
        notes=updated_trip.notes,
        created_at=updated_trip.created_at,
    )


@router.delete("/trips/{trip_id}", response_model=DeleteResponse)
async def delete_trip(
    trip_id: str,
    user: User = Depends(get_current_driver),
):
    """Delete a trip."""
    from src.guzo.bookings.service import BookingService
    
    trip = await TripService.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    bookings = await BookingService.get_trip_bookings(trip_id)
    if bookings:
        raise HTTPException(status_code=400, detail="Cannot delete trip with existing bookings")
    
    await TripService.delete_trip(trip_id)
    return DeleteResponse()


class BookingCompleteResponse(BaseModel):
    """Response for booking completion with token info."""
    booking: BookingResponse
    tokens_charged: int
    token_balance: int


@router.patch("/bookings/{booking_id}/complete", response_model=BookingCompleteResponse)
async def complete_booking(
    booking_id: str,
    user: User = Depends(get_current_driver),
):
    """
    Mark a booking as completed and charge platform fee in tokens.
    
    The driver's wallet will be debited based on the number of seats booked.
    """
    from src.guzo.bookings.service import BookingService
    from src.guzo.bookings.core import BookingUpdate
    from src.guzo.wallet.service import WalletService, InsufficientTokensError
    
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    driver_id = booking.assigned_driver_id or str(user.id)
    
    if driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if driver has enough tokens before completing
    balance_check = await WalletService.check_balance_for_trip(
        driver_id,
        booking.seats_booked
    )
    
    if not balance_check["can_accept"]:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Insufficient tokens: {balance_check.get('reason', 'Purchase more tokens to complete trips')}"
        )
    
    # Complete the booking
    updated = await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.COMPLETED),
    )
    
    # Charge platform fee
    tokens_charged = 0
    token_balance = balance_check["token_balance"]
    
    try:
        transaction = await WalletService.charge_trip_fee(
            driver_id=driver_id,
            trip_id=booking.trip_id or booking_id,  # Use booking ID if no trip
            booked_seats=booking.seats_booked,
        )
        if transaction:
            tokens_charged = abs(transaction.amount)
            token_balance = transaction.balance_after
    except InsufficientTokensError:
        # This shouldn't happen since we checked above, but handle gracefully
        pass
    except Exception:
        # Log but don't fail - booking is already completed
        pass
    
    booking_response = BookingResponse(
        id=str(updated.id),
        customer_id=updated.customer_id,
        customer_name=updated.customer_name,
        customer_phone=updated.customer_phone,
        trip_id=updated.trip_id,
        booking_type=updated.booking_type,
        pickup_location=updated.pickup_location,
        dropoff_location=updated.dropoff_location,
        scheduled_time=updated.scheduled_time,
        seats_booked=updated.seats_booked,
        price=updated.price,
        status=updated.status,
        assigned_driver_id=updated.assigned_driver_id,
        notes=updated.notes,
        created_at=updated.created_at,
        completed_at=updated.completed_at,
    )
    
    return BookingCompleteResponse(
        booking=booking_response,
        tokens_charged=tokens_charged,
        token_balance=token_balance,
    )


@router.post("/requests/{request_id}/accept", response_model=BookingResponse)
async def accept_request(
    request_id: str,
    payload: AcceptRequestPayload,
    user: User = Depends(get_current_driver),
):
    """Accept a charter request."""
    from src.guzo.bookings.service import BookingService
    
    booking = await BookingService.assign_driver(
        request_id,
        str(user.id),
        trip_id=payload.trip_id,
        price=payload.price,
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
    
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


@router.get("/earnings", response_model=DriverEarnings)
async def get_driver_earnings(
    user: User = Depends(get_current_driver),
    period: str = Query("week", enum=["today", "week", "month"]),
):
    """Get driver earnings."""
    from src.guzo.analytics.service import AnalyticsService
    
    earnings = await AnalyticsService.get_driver_earnings(str(user.id), period)
    return earnings


@router.get("/schedule", response_model=list[TripResponse])
async def get_driver_schedule(user: User = Depends(get_current_driver)):
    """Get driver's upcoming trips (schedule)."""
    trips = await TripService.get_driver_trips(str(user.id), upcoming_only=True)
    return [
        TripResponse(
            id=str(t.id),
            driver_id=t.driver_id,
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


@router.put("/schedule", response_model=StatusResponse)
async def update_schedule(
    schedule: ScheduleUpdate,
    user: User = Depends(get_current_driver),
):
    """Update driver schedule."""
    schedule_dict = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        day_schedule = getattr(schedule, day)
        if day_schedule:
            schedule_dict[day] = {
                "enabled": day_schedule.enabled,
                "start": day_schedule.start,
                "end": day_schedule.end,
            }
    
    await AuthService.update_schedule(user, schedule_dict)
    return StatusResponse(status="updated")


@router.get("/pricing-suggestion", response_model=PricingSuggestion)
async def get_pricing_suggestion(
    origin: str,
    destination: str,
    user: User = Depends(get_current_driver),
):
    """Get pricing suggestion for a route."""
    suggestion = await TripService.get_suggested_pricing(origin, destination)
    return PricingSuggestion(
        price_per_seat=suggestion["price_per_seat"],
        whole_car_price=suggestion["whole_car_price"],
        is_surge=suggestion.get("is_surge", False),
        surge_info=suggestion.get("surge_info"),
    )

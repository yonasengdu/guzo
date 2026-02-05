"""Admin resource - API routes for admin functionality."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.guzo.auth.core import User, UserRole, UserResponse
from src.guzo.bookings.core import BookingStatus, BookingType, BookingCreate, BookingResponse, BookingUpdate
from src.guzo.bookings.service import BookingService
from src.guzo.trips.core import TripUpdate, TripResponse
from src.guzo.trips.service import TripService
from src.guzo.middleware import get_current_admin
from src.guzo.admin.service import AdminService
from src.guzo.analytics.core import PlatformStats
from src.guzo.verification.core import VerificationResponse, VerificationStats

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== Request/Response Models ==============

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_users: int
    total_trips: int
    total_bookings: int
    total_revenue: float


class DashboardResponse(BaseModel):
    """Response for admin dashboard."""
    stats: DashboardStats
    users: list[UserResponse]
    trips: list[TripResponse]
    bookings: list[BookingResponse]


class UsersResponse(BaseModel):
    """Response for users list."""
    users: list[UserResponse]
    counts: dict


class PhoneBookingCreate(BaseModel):
    """Request for creating a phone booking."""
    customer_name: str
    customer_phone: str
    pickup_location: str
    dropoff_location: str
    scheduled_time: datetime
    seats_booked: int = 1
    price: Optional[float] = None
    assigned_driver_id: Optional[str] = None
    notes: Optional[str] = None


class AssignDriverRequest(BaseModel):
    """Request for assigning a driver."""
    driver_id: str
    trip_id: Optional[str] = None
    price: Optional[float] = None


class UpdatePriceRequest(BaseModel):
    """Request for updating price."""
    price: float


class UpdateTripPriceRequest(BaseModel):
    """Request for updating trip price."""
    price_per_seat: Optional[float] = None
    whole_car_price: Optional[float] = None


class TripDetailResponse(BaseModel):
    """Detailed trip response with bookings."""
    trip: TripResponse
    bookings: list[BookingResponse]


class VerificationsResponse(BaseModel):
    """Response for verifications list endpoint."""
    verifications: list[VerificationResponse]
    stats: VerificationStats


class LocationsResponse(BaseModel):
    """Response for locations list endpoint."""
    locations: list[str]


class VerificationsResponse(BaseModel):
    """Response for verifications list."""
    verifications: list
    stats: dict


class LocationsResponse(BaseModel):
    """Response for locations list."""
    locations: list[str]


class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"


# ============== Helper Functions ==============

def _user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_online=user.is_online,
        rating=user.rating,
        language=user.language,
        created_at=user.created_at,
    )


def _booking_to_response(b) -> BookingResponse:
    """Convert Booking model to BookingResponse."""
    return BookingResponse(
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


def _trip_to_response(t) -> TripResponse:
    """Convert Trip model to TripResponse."""
    return TripResponse(
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


# ============== Endpoints ==============

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(user: User = Depends(get_current_admin)):
    """Get admin dashboard data."""
    stats = await AdminService.get_dashboard_stats()
    
    return DashboardResponse(
        stats=DashboardStats(
            total_users=stats.total_users,
            total_trips=stats.total_trips,
            total_bookings=stats.total_bookings,
            total_revenue=stats.total_revenue,
        ),
        users=[_user_to_response(u) for u in stats.users[:10]],
        trips=[_trip_to_response(t) for t in stats.trips[:10]],
        bookings=[_booking_to_response(b) for b in stats.bookings[:10]],
    )


@router.get("/users", response_model=UsersResponse)
async def get_users(
    user: User = Depends(get_current_admin),
    role: Optional[UserRole] = None,
):
    """Get all users with optional role filter."""
    users, counts = await AdminService.get_users(role=role)
    return UsersResponse(
        users=[_user_to_response(u) for u in users],
        counts=counts,
    )


@router.get("/drivers", response_model=list[UserResponse])
async def get_drivers(user: User = Depends(get_current_admin)):
    """Get all drivers."""
    drivers = await AdminService.get_drivers()
    return [_user_to_response(d) for d in drivers]


@router.get("/trips", response_model=list[TripResponse])
async def get_all_trips(
    user: User = Depends(get_current_admin),
    limit: int = Query(100, le=500),
):
    """Get all trips."""
    trips = await TripService.get_upcoming_trips(limit=limit)
    return [_trip_to_response(t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripDetailResponse)
async def get_trip_detail(
    trip_id: str,
    user: User = Depends(get_current_admin),
):
    """Get trip details with bookings."""
    trip = await TripService.get_trip_with_driver(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    bookings = await BookingService.get_trip_bookings(trip_id)
    
    return TripDetailResponse(
        trip=_trip_to_response(trip),
        bookings=[_booking_to_response(b) for b in bookings],
    )


@router.delete("/trips/{trip_id}", response_model=DeleteResponse)
async def delete_trip(
    trip_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a trip."""
    success = await TripService.delete_trip(trip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trip not found")
    return DeleteResponse()


@router.get("/bookings", response_model=list[BookingResponse])
async def get_all_bookings(
    user: User = Depends(get_current_admin),
    status: Optional[BookingStatus] = None,
):
    """Get all bookings with optional status filter."""
    bookings = await BookingService.get_all_bookings(status=status)
    return [_booking_to_response(b) for b in bookings]


@router.get("/requests", response_model=list[BookingResponse])
async def get_pending_requests(user: User = Depends(get_current_admin)):
    """Get pending charter requests."""
    pending_requests = await BookingService.get_pending_requests()
    return [_booking_to_response(r) for r in pending_requests]


@router.post("/bookings", response_model=BookingResponse)
async def create_phone_booking(
    booking_data: PhoneBookingCreate,
    user: User = Depends(get_current_admin),
):
    """Create a booking from phone call (admin)."""
    try:
        create_data = BookingCreate(
            trip_id=None,
            customer_name=booking_data.customer_name,
            customer_phone=booking_data.customer_phone,
            pickup_location=booking_data.pickup_location,
            dropoff_location=booking_data.dropoff_location,
            scheduled_time=booking_data.scheduled_time,
            seats_booked=booking_data.seats_booked,
            booking_type=BookingType.CHARTER,
            notes=booking_data.notes,
        )
        
        booking = await BookingService.create_booking(create_data)
        
        if booking_data.assigned_driver_id:
            booking = await BookingService.assign_driver(
                str(booking.id),
                booking_data.assigned_driver_id,
                price=booking_data.price,
            )
        elif booking_data.price:
            booking = await BookingService.update_booking(
                str(booking.id),
                BookingUpdate(price=booking_data.price),
            )
        
        return _booking_to_response(booking)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/assign", response_model=BookingResponse)
async def assign_request(
    request_id: str,
    assign_data: AssignDriverRequest,
    user: User = Depends(get_current_admin),
):
    """Assign a driver to a charter request."""
    booking = await BookingService.assign_driver(
        request_id,
        assign_data.driver_id,
        trip_id=assign_data.trip_id,
        price=assign_data.price,
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return _booking_to_response(booking)


@router.patch("/bookings/{booking_id}/price", response_model=BookingResponse)
async def update_booking_price(
    booking_id: str,
    price_data: UpdatePriceRequest,
    user: User = Depends(get_current_admin),
):
    """Update booking price."""
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(price=price_data.price),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return _booking_to_response(booking)


@router.patch("/trips/{trip_id}/price", response_model=TripResponse)
async def update_trip_price(
    trip_id: str,
    price_data: UpdateTripPriceRequest,
    user: User = Depends(get_current_admin),
):
    """Update trip pricing."""
    update_data = TripUpdate(
        price_per_seat=price_data.price_per_seat,
        whole_car_price=price_data.whole_car_price,
    )
    
    trip = await TripService.update_trip(trip_id, update_data)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return _trip_to_response(trip)


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    user: User = Depends(get_current_admin),
):
    """Activate a user account (state change)."""
    try:
        updated_user = await AdminService.activate_user(user_id, user)
        return _user_to_response(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    user: User = Depends(get_current_admin),
):
    """Deactivate a user account (state change)."""
    try:
        updated_user = await AdminService.deactivate_user(user_id, user)
        return _user_to_response(updated_user)
    except ValueError as e:
        if "your own account" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: str,
    user: User = Depends(get_current_admin),
):
    """Confirm a pending booking (state change)."""
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.CONFIRMED),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return _booking_to_response(booking)


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    user: User = Depends(get_current_admin),
):
    """Cancel a booking (state change)."""
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.CANCELLED),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return _booking_to_response(booking)


@router.get("/analytics", response_model=PlatformStats)
async def get_analytics(
    user: User = Depends(get_current_admin),
    period: str = Query("week", enum=["today", "week", "month"]),
):
    """Get platform analytics."""
    from src.guzo.analytics.service import AnalyticsService
    
    stats = await AnalyticsService.get_platform_stats(period)
    return stats


@router.get("/verifications", response_model=VerificationsResponse)
async def get_verifications(user: User = Depends(get_current_admin)):
    """Get pending driver verifications."""
    from src.guzo.verification.service import VerificationService
    
    verifications = await VerificationService.get_pending_verifications()
    stats = await VerificationService.get_verification_stats()
    
    return VerificationsResponse(
        verifications=verifications,
        stats=stats,
    )


@router.get("/locations", response_model=LocationsResponse)
async def get_locations(user: User = Depends(get_current_admin)):
    """Get available locations for pricing rules."""
    from src.guzo.core import LOCATIONS
    return LocationsResponse(locations=LOCATIONS)

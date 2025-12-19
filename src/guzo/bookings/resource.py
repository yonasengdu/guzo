"""Bookings domain resource - API routes for bookings (customer functionality)."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import BookingType, BookingCreate
from src.guzo.bookings.service import BookingService
from src.guzo.trips.core import TripSearch
from src.guzo.trips.service import TripService
from src.guzo.middleware import get_current_user, get_current_user_required

router = APIRouter(prefix="/customer", tags=["Customer"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    user: User = Depends(get_current_user_required),
):
    """Customer dashboard page."""
    if user.role == UserRole.DRIVER:
        return RedirectResponse(url="/driver", status_code=303)
    elif user.role == UserRole.ADMIN:
        return RedirectResponse(url="/admin", status_code=303)
    
    bookings = await BookingService.get_customer_bookings(str(user.id))
    
    return templates.TemplateResponse(
        "customer/dashboard.html",
        {
            "request": request,
            "user": user,
            "bookings": bookings,
            "active_tab": "dashboard",
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_trips_page(
    request: Request,
    user: User = Depends(get_current_user),
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    seats: int = 1,
):
    """Search trips page."""
    search_date = None
    if date:
        try:
            search_date = datetime.fromisoformat(date)
        except ValueError:
            pass
    
    search = TripSearch(
        origin=origin,
        destination=destination,
        date=search_date,
        min_seats=seats,
    )
    trips = await TripService.search_trips(search)
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/trip_list.html",
            {
                "request": request,
                "trips": trips,
                "user": user,
            },
        )
    
    return templates.TemplateResponse(
        "customer/search.html",
        {
            "request": request,
            "user": user,
            "trips": trips,
            "search": {
                "origin": origin or "",
                "destination": destination or "",
                "date": date or "",
                "seats": seats,
            },
            "active_tab": "search",
        },
    )


@router.get("/trip/{trip_id}", response_class=HTMLResponse)
async def trip_details(
    request: Request,
    trip_id: str,
    user: User = Depends(get_current_user),
):
    """Trip details page."""
    trip = await TripService.get_trip_with_driver(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return templates.TemplateResponse(
        "customer/trip_detail.html",
        {
            "request": request,
            "user": user,
            "trip": trip,
        },
    )


@router.post("/book", response_class=HTMLResponse)
async def create_booking(
    request: Request,
    user: User = Depends(get_current_user_required),
    trip_id: Optional[str] = Form(None),
    pickup_location: str = Form(...),
    dropoff_location: str = Form(...),
    scheduled_time: str = Form(...),
    seats_booked: int = Form(1),
    booking_type: str = Form("seat"),
    notes: Optional[str] = Form(None),
):
    """Create a new booking."""
    try:
        booking_data = BookingCreate(
            trip_id=trip_id if trip_id else None,
            customer_name=user.full_name,
            customer_phone=user.phone,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            scheduled_time=datetime.fromisoformat(scheduled_time),
            seats_booked=seats_booked,
            booking_type=BookingType(booking_type),
            notes=notes,
        )
        
        booking = await BookingService.create_booking(
            booking_data,
            customer_id=str(user.id),
        )
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/booking_success.html",
                {
                    "request": request,
                    "booking": booking,
                },
            )
        
        return RedirectResponse(url="/customer", status_code=303)
        
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/book/charter", response_class=HTMLResponse)
async def request_charter(
    request: Request,
    user: User = Depends(get_current_user_required),
    pickup_location: str = Form(...),
    dropoff_location: str = Form(...),
    scheduled_time: str = Form(...),
    notes: Optional[str] = Form(None),
):
    """Request a charter (custom trip)."""
    try:
        booking_data = BookingCreate(
            trip_id=None,
            customer_name=user.full_name,
            customer_phone=user.phone,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            scheduled_time=datetime.fromisoformat(scheduled_time),
            seats_booked=1,
            booking_type=BookingType.CHARTER,
            notes=notes,
        )
        
        booking = await BookingService.create_booking(
            booking_data,
            customer_id=str(user.id),
        )
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/booking_success.html",
                {
                    "request": request,
                    "booking": booking,
                    "message": "Your charter request has been submitted. We'll contact you soon!",
                },
            )
        
        return RedirectResponse(url="/customer", status_code=303)
        
    except Exception as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">Error: {str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/booking/{booking_id}/cancel")
async def cancel_booking(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Cancel a booking."""
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = await BookingService.cancel_booking(booking_id)
    
    if request.headers.get("HX-Request"):
        if success:
            return HTMLResponse('<div class="alert alert-success">Booking cancelled</div>')
        return HTMLResponse('<div class="alert alert-error">Failed to cancel booking</div>', status_code=400)
    
    return RedirectResponse(url="/customer", status_code=303)


@router.get("/bookings", response_class=HTMLResponse)
async def get_bookings_partial(
    request: Request,
    user: User = Depends(get_current_user_required),
):
    """Get customer bookings (HTMX partial)."""
    bookings = await BookingService.get_customer_bookings(str(user.id))
    
    return templates.TemplateResponse(
        "partials/customer_bookings.html",
        {
            "request": request,
            "bookings": bookings,
        },
    )


# ============== Phase 2: History, Favorites ==============

@router.get("/history", response_class=HTMLResponse)
async def customer_history_page(
    request: Request,
    user: User = Depends(get_current_user_required),
    status: Optional[str] = None,
):
    """Customer trip history page."""
    from src.guzo.bookings.core import BookingStatus
    
    # Get all bookings or filter by status
    if status == "completed":
        bookings = await BookingService.get_customer_bookings(
            str(user.id), status=BookingStatus.COMPLETED
        )
    elif status == "cancelled":
        bookings = await BookingService.get_customer_bookings(
            str(user.id), status=BookingStatus.CANCELLED
        )
    else:
        bookings = await BookingService.get_customer_bookings(str(user.id))
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/customer_history.html",
            {
                "request": request,
                "bookings": bookings,
                "user": user,
            },
        )
    
    return templates.TemplateResponse(
        "customer/history.html",
        {
            "request": request,
            "user": user,
            "bookings": bookings,
            "status_filter": status,
            "active_tab": "history",
        },
    )


@router.get("/favorites", response_class=HTMLResponse)
async def customer_favorites_page(
    request: Request,
    user: User = Depends(get_current_user_required),
):
    """Customer favorites page."""
    from src.guzo.core import LOCATIONS
    
    return templates.TemplateResponse(
        "customer/favorites.html",
        {
            "request": request,
            "user": user,
            "locations": LOCATIONS,
            "active_tab": "favorites",
        },
    )


@router.post("/rebook/{booking_id}", response_class=HTMLResponse)
async def rebook_trip(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_user_required),
):
    """Rebook a previous trip."""
    from src.guzo.bookings.core import BookingCreate, BookingType
    
    # Get the original booking
    original = await BookingService.get_booking(booking_id)
    if not original:
        return HTMLResponse(
            '<div class="p-3 bg-red-100 text-red-700 rounded-xl">Booking not found</div>',
            status_code=404,
        )
    
    if original.customer_id != str(user.id):
        return HTMLResponse(
            '<div class="p-3 bg-red-100 text-red-700 rounded-xl">Not authorized</div>',
            status_code=403,
        )
    
    # Redirect to search with pre-filled parameters
    return HTMLResponse(
        f'''<script>
            window.location.href = '/customer/search?origin={original.pickup_location}&destination={original.dropoff_location}&seats={original.seats_booked}';
        </script>
        <div class="p-3 bg-blue-100 text-blue-700 rounded-xl">Redirecting to search...</div>'''
    )


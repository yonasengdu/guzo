"""Admin resource - API routes for admin functionality."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.guzo.auth.core import User, UserRole
from src.guzo.bookings.core import BookingStatus, BookingType, BookingCreate
from src.guzo.bookings.service import BookingService
from src.guzo.trips.core import TripUpdate
from src.guzo.trips.service import TripService
from src.guzo.middleware import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Admin dashboard page."""
    # Get all users
    users = await User.find_all().to_list()
    trips = await TripService.get_upcoming_trips(limit=50)
    bookings = await BookingService.get_all_bookings(limit=50)
    
    # Calculate stats
    total_revenue = sum(b.price or 0 for b in bookings if b.status.value == 'completed')
    stats = {
        "total_users": len(users),
        "total_trips": len(trips),
        "total_bookings": len(bookings),
        "total_revenue": total_revenue,
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "trips": trips,
            "bookings": bookings,
            "stats": stats,
            "active_tab": "dashboard",
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    user: User = Depends(get_current_admin),
    role: Optional[str] = None,
):
    """Admin users management page."""
    if role:
        users = await User.find(User.role == UserRole(role)).to_list()
    else:
        users = await User.find_all().to_list()
    
    # Get counts for tabs
    all_count = await User.count()
    driver_count = await User.find(User.role == UserRole.DRIVER).count()
    rider_count = await User.find(User.role == UserRole.RIDER).count()
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "role_filter": role,
            "counts": {
                "all": all_count,
                "drivers": driver_count,
                "riders": rider_count,
            },
            "active_tab": "users",
        },
    )


@router.get("/drivers", response_class=HTMLResponse)
async def get_drivers(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Get all drivers (HTMX partial)."""
    drivers = await User.find(User.role == UserRole.DRIVER).to_list()
    
    return templates.TemplateResponse(
        "partials/admin_drivers.html",
        {
            "request": request,
            "drivers": drivers,
        },
    )


@router.get("/trips", response_class=HTMLResponse)
async def get_all_trips(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Get all trips page or HTMX partial."""
    trips = await TripService.get_upcoming_trips(limit=100)
    
    # Return partial for HTMX requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/admin_trips.html",
            {
                "request": request,
                "trips": trips,
            },
        )
    
    return templates.TemplateResponse(
        "admin/trips.html",
        {
            "request": request,
            "user": user,
            "trips": trips,
            "active_tab": "trips",
        },
    )


@router.get("/bookings", response_class=HTMLResponse)
async def get_all_bookings(
    request: Request,
    user: User = Depends(get_current_admin),
    status: Optional[str] = None,
):
    """Get all bookings (HTMX partial)."""
    booking_status = BookingStatus(status) if status else None
    bookings = await BookingService.get_all_bookings(status=booking_status)
    
    return templates.TemplateResponse(
        "partials/admin_bookings.html",
        {
            "request": request,
            "bookings": bookings,
        },
    )


@router.get("/requests", response_class=HTMLResponse)
async def get_pending_requests(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Get pending charter requests (HTMX partial)."""
    requests = await BookingService.get_pending_requests()
    trips = await TripService.get_upcoming_trips(limit=50)
    drivers = await User.find(User.role == UserRole.DRIVER).to_list()
    
    return templates.TemplateResponse(
        "partials/admin_requests.html",
        {
            "request": request,
            "pending_requests": requests,
            "trips": trips,
            "drivers": drivers,
        },
    )


@router.post("/booking/create", response_class=HTMLResponse)
async def create_phone_booking(
    request: Request,
    user: User = Depends(get_current_admin),
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    pickup_location: str = Form(...),
    dropoff_location: str = Form(...),
    scheduled_time: str = Form(...),
    seats_booked: int = Form(1),
    price: Optional[float] = Form(None),
    assigned_driver_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    """Create a booking from phone call (admin)."""
    try:
        booking_data = BookingCreate(
            trip_id=None,
            customer_name=customer_name,
            customer_phone=customer_phone,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            scheduled_time=datetime.fromisoformat(scheduled_time),
            seats_booked=seats_booked,
            booking_type=BookingType.CHARTER,
            notes=notes,
        )
        
        booking = await BookingService.create_booking(booking_data)
        
        if assigned_driver_id:
            await BookingService.assign_driver(
                str(booking.id),
                assigned_driver_id,
                price=float(price) if price else None,
            )
        elif price:
            from src.guzo.bookings.core import BookingUpdate
            await BookingService.update_booking(
                str(booking.id),
                BookingUpdate(price=float(price)),
            )
        
        if request.headers.get("HX-Request"):
            return HTMLResponse('<div class="alert alert-success">Booking created successfully!</div>')
        
        return RedirectResponse(url="/admin", status_code=303)
        
    except Exception as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">Error: {str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/request/{request_id}/assign")
async def assign_request(
    request: Request,
    request_id: str,
    user: User = Depends(get_current_admin),
    driver_id: str = Form(...),
    trip_id: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
):
    """Assign a driver to a charter request."""
    booking = await BookingService.assign_driver(
        request_id,
        driver_id,
        trip_id=trip_id,
        price=float(price) if price else None,
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<div class="alert alert-success">Driver assigned successfully!</div>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/booking/{booking_id}/update-price")
async def update_booking_price(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_admin),
    price: float = Form(...),
):
    """Update booking price."""
    from src.guzo.bookings.core import BookingUpdate
    
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(price=float(price)),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse(f'<span class="font-bold">{price} ETB</span>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/trip/{trip_id}/update-price")
async def update_trip_price(
    request: Request,
    trip_id: str,
    user: User = Depends(get_current_admin),
    price_per_seat: Optional[float] = Form(None),
    whole_car_price: Optional[float] = Form(None),
):
    """Update trip pricing."""
    update_data = TripUpdate()
    if price_per_seat:
        update_data.price_per_seat = float(price_per_seat)
    if whole_car_price:
        update_data.whole_car_price = float(whole_car_price)
    
    trip = await TripService.update_trip(trip_id, update_data)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<div class="alert alert-success">Price updated!</div>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: str,
    user: User = Depends(get_current_admin),
):
    """Activate a user account."""
    from beanie import PydanticObjectId
    target_user = await User.get(PydanticObjectId(user_id))
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user.is_active = True
    await target_user.save()
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge-apple badge-success">Active</span>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: str,
    user: User = Depends(get_current_admin),
):
    """Deactivate a user account."""
    from beanie import PydanticObjectId
    target_user = await User.get(PydanticObjectId(user_id))
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating yourself
    if str(target_user.id) == str(user.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    target_user.is_active = False
    await target_user.save()
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge-apple badge-error">Inactive</span>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.delete("/trip/{trip_id}")
async def delete_trip(
    request: Request,
    trip_id: str,
    user: User = Depends(get_current_admin),
):
    """Delete a trip."""
    success = await TripService.delete_trip(trip_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/booking/{booking_id}/confirm")
async def confirm_booking(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_admin),
):
    """Confirm a pending booking."""
    from src.guzo.bookings.core import BookingUpdate
    
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.CONFIRMED),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge-apple badge-info">Confirmed</span>')
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/booking/{booking_id}/cancel")
async def cancel_booking_admin(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_admin),
):
    """Cancel a booking."""
    from src.guzo.bookings.core import BookingUpdate
    
    booking = await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.CANCELLED),
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge-apple badge-error">Cancelled</span>')
    
    return RedirectResponse(url="/admin", status_code=303)


# ============== Phase 2: Analytics, Verification, Pricing Pages ==============

@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics_page(
    request: Request,
    user: User = Depends(get_current_admin),
    period: str = "week",
):
    """Admin analytics dashboard page."""
    from src.guzo.analytics.service import AnalyticsService
    
    stats = await AnalyticsService.get_platform_stats(period)
    
    # Return partial for HTMX requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/analytics_content.html",
            {
                "request": request,
                "stats": stats,
                "period": period,
            },
        )
    
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "period": period,
            "active_tab": "analytics",
        },
    )


@router.get("/verification", response_class=HTMLResponse)
async def admin_verification_page(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Admin driver verification page."""
    from src.guzo.verification.service import VerificationService
    
    verifications = await VerificationService.get_pending_verifications()
    stats = await VerificationService.get_verification_stats()
    
    return templates.TemplateResponse(
        "admin/verification.html",
        {
            "request": request,
            "user": user,
            "verifications": verifications,
            "stats": stats,
            "active_tab": "verification",
        },
    )


@router.get("/pricing", response_class=HTMLResponse)
async def admin_pricing_page(
    request: Request,
    user: User = Depends(get_current_admin),
):
    """Admin pricing rules page."""
    from src.guzo.core import LOCATIONS
    
    return templates.TemplateResponse(
        "admin/pricing.html",
        {
            "request": request,
            "user": user,
            "locations": LOCATIONS,
            "active_tab": "pricing",
        },
    )


"""Trips domain resource - API routes for trips (driver functionality)."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.guzo.auth.core import User, UserRole
from src.guzo.auth.service import AuthService
from src.guzo.trips.core import TripStatus, TripCreate, TripUpdate
from src.guzo.trips.service import TripService
from src.guzo.middleware import get_current_driver

router = APIRouter(prefix="/driver", tags=["Driver"])
templates = Jinja2Templates(directory="src/guzo/templates")


@router.get("", response_class=HTMLResponse)
async def driver_dashboard(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Driver dashboard page."""
    from src.guzo.bookings.service import BookingService
    
    trips = await TripService.get_driver_trips(str(user.id))
    bookings = await BookingService.get_driver_bookings(str(user.id))
    pending_requests = await BookingService.get_pending_requests()
    
    return templates.TemplateResponse(
        "driver/dashboard.html",
        {
            "request": request,
            "user": user,
            "trips": trips,
            "bookings": bookings,
            "pending_requests": pending_requests,
            "active_tab": "dashboard",
        },
    )


@router.post("/toggle-status")
async def toggle_online_status(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Toggle driver online/offline status."""
    updated_user = await AuthService.toggle_online_status(user)
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/online_toggle.html",
            {
                "request": request,
                "is_online": updated_user.is_online,
            },
        )
    
    return RedirectResponse(url="/driver", status_code=303)


@router.get("/trips", response_class=HTMLResponse)
async def get_trips_partial(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Get driver trips (HTMX partial)."""
    trips = await TripService.get_driver_trips(str(user.id))
    
    return templates.TemplateResponse(
        "partials/driver_trips.html",
        {
            "request": request,
            "trips": trips,
        },
    )


@router.post("/trip/create", response_class=HTMLResponse)
async def create_trip(
    request: Request,
    user: User = Depends(get_current_driver),
    origin: str = Form(...),
    destination: str = Form(...),
    departure_time: str = Form(...),
    available_seats: int = Form(...),
    price_per_seat: float = Form(...),
    whole_car_price: float = Form(...),
    notes: Optional[str] = Form(None),
):
    """Create a new trip."""
    try:
        trip_data = TripCreate(
            origin=origin,
            destination=destination,
            departure_time=datetime.fromisoformat(departure_time),
            available_seats=available_seats,
            price_per_seat=float(price_per_seat),
            whole_car_price=float(whole_car_price),
            notes=notes,
        )
        
        trip = await TripService.create_trip(str(user.id), trip_data)
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/trip_card.html",
                {
                    "request": request,
                    "trip": trip,
                    "is_driver": True,
                },
            )
        
        return RedirectResponse(url="/driver", status_code=303)
        
    except Exception as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">Error: {str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trip/{trip_id}/update")
async def update_trip(
    request: Request,
    trip_id: str,
    user: User = Depends(get_current_driver),
    price_per_seat: Optional[float] = Form(None),
    whole_car_price: Optional[float] = Form(None),
    status: Optional[str] = Form(None),
):
    """Update a trip."""
    trip = await TripService.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = TripUpdate()
    if price_per_seat:
        update_data.price_per_seat = float(price_per_seat)
    if whole_car_price:
        update_data.whole_car_price = float(whole_car_price)
    if status:
        update_data.status = TripStatus(status)
    
    updated_trip = await TripService.update_trip(trip_id, update_data)
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/trip_card.html",
            {
                "request": request,
                "trip": updated_trip,
                "is_driver": True,
            },
        )
    
    return RedirectResponse(url="/driver", status_code=303)


@router.post("/trip/{trip_id}/delete")
async def delete_trip(
    request: Request,
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
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                '<div class="alert alert-error">Cannot delete trip with existing bookings</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail="Cannot delete trip with existing bookings")
    
    await TripService.delete_trip(trip_id)
    
    if request.headers.get("HX-Request"):
        return HTMLResponse("")
    
    return RedirectResponse(url="/driver", status_code=303)


@router.post("/booking/{booking_id}/complete")
async def complete_booking(
    request: Request,
    booking_id: str,
    user: User = Depends(get_current_driver),
):
    """Mark a booking as completed."""
    from src.guzo.bookings.service import BookingService
    from src.guzo.bookings.core import BookingStatus, BookingUpdate
    
    booking = await BookingService.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.assigned_driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await BookingService.update_booking(
        booking_id,
        BookingUpdate(status=BookingStatus.COMPLETED),
    )
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge badge-success">Completed</span>')
    
    return RedirectResponse(url="/driver", status_code=303)


@router.post("/request/{request_id}/accept")
async def accept_request(
    request: Request,
    request_id: str,
    user: User = Depends(get_current_driver),
    trip_id: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
):
    """Accept a charter request."""
    from src.guzo.bookings.service import BookingService
    
    booking = await BookingService.assign_driver(
        request_id,
        str(user.id),
        trip_id=trip_id,
        price=float(price) if price else None,
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<div class="alert alert-success">Request accepted!</div>')
    
    return RedirectResponse(url="/driver", status_code=303)


# ============== Phase 2: Schedule & Earnings ==============

@router.get("/earnings", response_class=HTMLResponse)
async def driver_earnings_page(
    request: Request,
    user: User = Depends(get_current_driver),
    period: str = "week",
):
    """Driver earnings page."""
    from src.guzo.analytics.service import AnalyticsService
    
    earnings = await AnalyticsService.get_driver_earnings(str(user.id), period)
    
    # Return partial for HTMX requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/earnings_content.html",
            {
                "request": request,
                "earnings": earnings,
                "period": period,
            },
        )
    
    return templates.TemplateResponse(
        "driver/earnings.html",
        {
            "request": request,
            "user": user,
            "earnings": earnings,
            "period": period,
            "active_tab": "earnings",
        },
    )


@router.get("/schedule", response_class=HTMLResponse)
async def driver_schedule_page(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Driver schedule management page."""
    trips = await TripService.get_driver_trips(str(user.id), upcoming_only=True)
    
    return templates.TemplateResponse(
        "driver/schedule.html",
        {
            "request": request,
            "user": user,
            "trips": trips,
            "active_tab": "schedule",
        },
    )


@router.post("/schedule")
async def update_schedule(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Update driver schedule."""
    form_data = await request.form()
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    schedule = {}
    
    for day in days:
        enabled = form_data.get(f"{day}_enabled") == "true"
        start = form_data.get(f"{day}_start", "08:00")
        end = form_data.get(f"{day}_end", "18:00")
        
        schedule[day] = {
            "enabled": enabled,
            "start": start,
            "end": end,
        }
    
    await AuthService.update_schedule(user, schedule)
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<div class="p-4 bg-green-100 text-green-700 rounded-xl">Schedule saved!</div>')
    
    return RedirectResponse(url="/driver/schedule", status_code=303)


@router.get("/trips/upcoming", response_class=HTMLResponse)
async def get_upcoming_trips(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Get upcoming trips for the driver."""
    trips = await TripService.get_driver_trips(str(user.id), upcoming_only=True)
    
    if not trips:
        return HTMLResponse('<p class="text-apple-gray-500 text-center py-4">No upcoming trips</p>')
    
    return templates.TemplateResponse(
        "partials/upcoming_trips.html",
        {
            "request": request,
            "trips": trips,
        },
    )


@router.get("/vehicles", response_class=HTMLResponse)
async def driver_vehicles_page(
    request: Request,
    user: User = Depends(get_current_driver),
):
    """Driver vehicles management page."""
    from src.guzo.vehicles.service import VehicleService
    
    vehicles = await VehicleService.get_driver_vehicles(str(user.id))
    
    return templates.TemplateResponse(
        "driver/vehicles.html",
        {
            "request": request,
            "user": user,
            "vehicles": vehicles,
            "active_tab": "vehicles",
        },
    )


@router.get("/pricing-suggestion", response_class=HTMLResponse)
async def get_pricing_suggestion(
    request: Request,
    user: User = Depends(get_current_driver),
    origin: str = None,
    destination: str = None,
):
    """Get pricing suggestion for a route."""
    if not origin or not destination:
        return HTMLResponse("")
    
    suggestion = await TripService.get_suggested_pricing(origin, destination)
    
    return HTMLResponse(f'''
        <div class="p-4 bg-apple-gray-50 rounded-xl space-y-2">
            <p class="text-sm text-apple-gray-600">Suggested Pricing:</p>
            <div class="flex justify-between">
                <span>Price per seat:</span>
                <span class="font-semibold">{suggestion["price_per_seat"]} ETB</span>
            </div>
            <div class="flex justify-between">
                <span>Whole car price:</span>
                <span class="font-semibold">{suggestion["whole_car_price"]} ETB</span>
            </div>
            {"<p class='text-xs text-orange-500 mt-2'>⚡ Surge pricing active: " + suggestion["surge_info"] + "</p>" if suggestion["is_surge"] else ""}
        </div>
    ''')

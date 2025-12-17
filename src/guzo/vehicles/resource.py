"""Vehicles domain resource - API routes for vehicles."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.guzo.auth.core import User, UserRole
from src.guzo.vehicles.core import VehicleType, VehicleCreate, VehicleUpdate, VehicleResponse
from src.guzo.vehicles.service import VehicleService
from src.guzo.middleware import get_current_driver, get_current_admin

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=list[VehicleResponse])
async def get_my_vehicles(user: User = Depends(get_current_driver)):
    """Get all vehicles for the current driver."""
    vehicles = await VehicleService.get_driver_vehicles(str(user.id))
    return [
        VehicleResponse(
            id=str(v.id),
            driver_id=v.driver_id,
            plate_number=v.plate_number,
            make=v.make,
            model=v.model,
            year=v.year,
            color=v.color,
            vehicle_type=v.vehicle_type,
            capacity=v.capacity,
            is_active=v.is_active,
            is_verified=v.is_verified,
            created_at=v.created_at,
        )
        for v in vehicles
    ]


@router.post("", response_model=VehicleResponse)
async def create_vehicle(
    request: Request,
    user: User = Depends(get_current_driver),
    plate_number: str = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    year: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    vehicle_type: str = Form("sedan"),
    capacity: int = Form(4),
):
    """Create a new vehicle."""
    try:
        vehicle_data = VehicleCreate(
            plate_number=plate_number,
            make=make,
            model=model,
            year=year,
            color=color,
            vehicle_type=VehicleType(vehicle_type),
            capacity=capacity,
        )
        
        vehicle = await VehicleService.create_vehicle(str(user.id), vehicle_data)
        
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-success">Vehicle {vehicle.plate_number} added successfully!</div>'
            )
        
        return VehicleResponse(
            id=str(vehicle.id),
            driver_id=vehicle.driver_id,
            plate_number=vehicle.plate_number,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            vehicle_type=vehicle.vehicle_type,
            capacity=vehicle.capacity,
            is_active=vehicle.is_active,
            is_verified=vehicle.is_verified,
            created_at=vehicle.created_at,
        )
        
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, user: User = Depends(get_current_driver)):
    """Get a specific vehicle."""
    vehicle = await VehicleService.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Only allow access to own vehicles (or admin)
    if vehicle.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return VehicleResponse(
        id=str(vehicle.id),
        driver_id=vehicle.driver_id,
        plate_number=vehicle.plate_number,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        vehicle_type=vehicle.vehicle_type,
        capacity=vehicle.capacity,
        is_active=vehicle.is_active,
        is_verified=vehicle.is_verified,
        created_at=vehicle.created_at,
    )


@router.post("/{vehicle_id}/verify")
async def verify_vehicle(
    request: Request,
    vehicle_id: str,
    user: User = Depends(get_current_admin),
):
    """Verify a vehicle (admin only)."""
    vehicle = await VehicleService.verify_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if request.headers.get("HX-Request"):
        return HTMLResponse('<span class="badge badge-success">Verified</span>')
    
    return {"status": "verified"}


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    user: User = Depends(get_current_driver),
):
    """Delete a vehicle."""
    vehicle = await VehicleService.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if vehicle.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await VehicleService.delete_vehicle(vehicle_id)
    return {"status": "deleted"}


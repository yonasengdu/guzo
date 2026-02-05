"""Vehicles domain resource - API routes for vehicles."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.guzo.auth.core import User, UserRole
from src.guzo.vehicles.core import VehicleCreate, VehicleResponse
from src.guzo.vehicles.service import VehicleService
from src.guzo.middleware import get_current_driver, get_current_admin

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"


# ============== Helper Function ==============

def _vehicle_to_response(v) -> VehicleResponse:
    """Convert Vehicle model to VehicleResponse."""
    return VehicleResponse(
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


# ============== Endpoints ==============

@router.get("", response_model=list[VehicleResponse])
async def get_my_vehicles(user: User = Depends(get_current_driver)):
    """Get all vehicles for the current driver."""
    vehicles = await VehicleService.get_driver_vehicles(str(user.id))
    return [_vehicle_to_response(v) for v in vehicles]


@router.post("", response_model=VehicleResponse)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    user: User = Depends(get_current_driver),
):
    """Create a new vehicle."""
    try:
        vehicle = await VehicleService.create_vehicle(str(user.id), vehicle_data)
        return _vehicle_to_response(vehicle)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    user: User = Depends(get_current_driver),
):
    """Get a specific vehicle."""
    vehicle = await VehicleService.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Only allow access to own vehicles (or admin)
    if vehicle.driver_id != str(user.id) and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return _vehicle_to_response(vehicle)


@router.patch("/{vehicle_id}/verify", response_model=VehicleResponse)
async def verify_vehicle(
    vehicle_id: str,
    user: User = Depends(get_current_admin),
):
    """Verify a vehicle (admin only). Uses PATCH as this is a state change."""
    vehicle = await VehicleService.verify_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return _vehicle_to_response(vehicle)


@router.delete("/{vehicle_id}", response_model=DeleteResponse)
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
    return DeleteResponse()

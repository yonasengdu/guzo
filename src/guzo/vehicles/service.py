"""Vehicles domain service - business logic for vehicles."""

from datetime import datetime
from typing import Optional, List
from src.guzo.vehicles.core import Vehicle, VehicleCreate, VehicleUpdate, VehicleResponse
from src.guzo.vehicles.repository import vehicle_repository


class VehicleService:
    """Service for managing vehicles."""
    
    @staticmethod
    async def create_vehicle(driver_id: str, vehicle_data: VehicleCreate) -> Vehicle:
        """Create a new vehicle."""
        # Check if plate number already exists
        if await vehicle_repository.plate_exists(vehicle_data.plate_number):
            raise ValueError("A vehicle with this plate number already exists")
        
        vehicle = Vehicle(
            driver_id=driver_id,
            plate_number=vehicle_data.plate_number,
            make=vehicle_data.make,
            model=vehicle_data.model,
            year=vehicle_data.year,
            color=vehicle_data.color,
            vehicle_type=vehicle_data.vehicle_type,
            capacity=vehicle_data.capacity,
        )
        await vehicle_repository.create(vehicle)
        return vehicle
    
    @staticmethod
    async def get_vehicle(vehicle_id: str) -> Optional[Vehicle]:
        """Get a vehicle by ID."""
        return await vehicle_repository.get_by_id(vehicle_id)
    
    @staticmethod
    async def update_vehicle(vehicle_id: str, vehicle_data: VehicleUpdate) -> Optional[Vehicle]:
        """Update a vehicle."""
        update_data = vehicle_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            return await vehicle_repository.update(vehicle_id, update_data)
        return await vehicle_repository.get_by_id(vehicle_id)
    
    @staticmethod
    async def delete_vehicle(vehicle_id: str) -> bool:
        """Delete a vehicle."""
        return await vehicle_repository.delete(vehicle_id)
    
    @staticmethod
    async def get_driver_vehicles(driver_id: str) -> List[Vehicle]:
        """Get all vehicles for a driver."""
        return await vehicle_repository.get_by_driver(driver_id)
    
    @staticmethod
    async def verify_vehicle(vehicle_id: str) -> Optional[Vehicle]:
        """Mark a vehicle as verified (admin action)."""
        return await vehicle_repository.verify(vehicle_id)
    
    @staticmethod
    async def get_vehicle_response(vehicle_id: str) -> Optional[VehicleResponse]:
        """Get vehicle response."""
        vehicle = await vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            return None
        
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


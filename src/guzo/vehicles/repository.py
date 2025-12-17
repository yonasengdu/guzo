"""Vehicles domain repository - database operations for vehicles."""

from datetime import datetime
from typing import Optional, List
from src.guzo.vehicles.core import Vehicle, VehicleType
from src.guzo.infrastructure.repository import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    """Repository for Vehicle database operations."""
    
    def __init__(self):
        super().__init__(Vehicle)
    
    async def get_by_driver(self, driver_id: str) -> List[Vehicle]:
        """Get all vehicles for a driver."""
        return await Vehicle.find(Vehicle.driver_id == driver_id).to_list()
    
    async def get_by_plate(self, plate_number: str) -> Optional[Vehicle]:
        """Get a vehicle by plate number."""
        return await Vehicle.find_one(Vehicle.plate_number == plate_number)
    
    async def get_active_by_driver(self, driver_id: str) -> List[Vehicle]:
        """Get all active vehicles for a driver."""
        return await Vehicle.find(
            Vehicle.driver_id == driver_id,
            Vehicle.is_active == True,
        ).to_list()
    
    async def get_by_type(self, vehicle_type: VehicleType) -> List[Vehicle]:
        """Get all vehicles of a specific type."""
        return await Vehicle.find(
            Vehicle.vehicle_type == vehicle_type,
            Vehicle.is_active == True,
        ).to_list()
    
    async def plate_exists(self, plate_number: str) -> bool:
        """Check if a plate number already exists."""
        existing = await Vehicle.find_one(Vehicle.plate_number == plate_number)
        return existing is not None
    
    async def verify(self, vehicle_id: str) -> Optional[Vehicle]:
        """Mark a vehicle as verified."""
        vehicle = await self.get_by_id(vehicle_id)
        if vehicle:
            vehicle.is_verified = True
            vehicle.updated_at = datetime.utcnow()
            await vehicle.save()
            return vehicle
        return None


# Singleton instance
vehicle_repository = VehicleRepository()


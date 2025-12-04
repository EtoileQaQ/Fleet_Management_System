"""
Telematics service for GPS position ingestion and vehicle tracking.

This service handles:
- Real-time GPS position ingestion
- Vehicle status updates (last_seen, current_position)
- Batch processing for multiple positions
- Data validation and error handling
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2.elements import WKTElement

from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.gps_position import GPSPosition
from app.schemas.telematics import GPSPositionCreate, IngestionStats


class TelematicsServiceError(Exception):
    """Exception raised for telematics service errors."""
    pass


class TelematicsService:
    """Service for handling telematics data ingestion."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def ingest_position(
        self,
        position: GPSPositionCreate,
        update_vehicle: bool = True
    ) -> GPSPosition:
        """
        Ingest a single GPS position.
        
        Args:
            position: GPS position data
            update_vehicle: Whether to update vehicle's current position
            
        Returns:
            Created GPSPosition object
        """
        # Validate vehicle exists
        vehicle = await self._get_vehicle(position.vehicle_id)
        if not vehicle:
            raise TelematicsServiceError(f"Vehicle {position.vehicle_id} not found")
        
        # Validate driver if provided
        if position.driver_id:
            driver = await self._get_driver(position.driver_id)
            if not driver:
                raise TelematicsServiceError(f"Driver {position.driver_id} not found")
        
        # Create GPS position record
        gps_position = GPSPosition(
            vehicle_id=position.vehicle_id,
            driver_id=position.driver_id,
            timestamp=position.timestamp,
            location=WKTElement(f"POINT({position.lon} {position.lat})", srid=4326),
            speed=position.speed,
            heading=position.heading,
            odometer=position.odometer,
            ignition_status=position.ignition or False
        )
        
        self.db.add(gps_position)
        
        # Update vehicle's current position
        if update_vehicle:
            await self._update_vehicle_position(vehicle, position)
        
        await self.db.flush()
        await self.db.refresh(gps_position)
        
        return gps_position
    
    async def ingest_batch(
        self,
        positions: list[GPSPositionCreate]
    ) -> IngestionStats:
        """
        Ingest a batch of GPS positions.
        
        Args:
            positions: List of GPS position data
            
        Returns:
            IngestionStats with processing results
        """
        stats = IngestionStats(
            total_received=len(positions),
            successfully_processed=0,
            failed=0,
            errors=[]
        )
        
        # Group positions by vehicle for efficient vehicle updates
        vehicle_latest: dict[int, GPSPositionCreate] = {}
        
        for position in positions:
            try:
                # Track latest position per vehicle
                current_latest = vehicle_latest.get(position.vehicle_id)
                if not current_latest or position.timestamp > current_latest.timestamp:
                    vehicle_latest[position.vehicle_id] = position
                
                # Create GPS position record
                await self.ingest_position(position, update_vehicle=False)
                stats.successfully_processed += 1
                
            except TelematicsServiceError as e:
                stats.failed += 1
                stats.errors.append(str(e))
            except Exception as e:
                stats.failed += 1
                stats.errors.append(f"Unexpected error: {str(e)}")
        
        # Update vehicle positions with latest data
        for vehicle_id, latest_position in vehicle_latest.items():
            try:
                vehicle = await self._get_vehicle(vehicle_id)
                if vehicle:
                    await self._update_vehicle_position(vehicle, latest_position)
            except Exception as e:
                stats.errors.append(f"Failed to update vehicle {vehicle_id}: {str(e)}")
        
        await self.db.flush()
        
        return stats
    
    async def _get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_driver(self, driver_id: int) -> Optional[Driver]:
        """Get driver by ID."""
        result = await self.db.execute(
            select(Driver).where(Driver.id == driver_id)
        )
        return result.scalar_one_or_none()
    
    async def _update_vehicle_position(
        self,
        vehicle: Vehicle,
        position: GPSPositionCreate
    ) -> None:
        """Update vehicle's current position and last_seen."""
        # Only update if this position is more recent
        if vehicle.last_seen and position.timestamp <= vehicle.last_seen:
            return
        
        vehicle.last_seen = position.timestamp
        vehicle.current_position = WKTElement(
            f"POINT({position.lon} {position.lat})", srid=4326
        )
        vehicle.current_speed = position.speed
        vehicle.current_heading = position.heading
        
        if position.odometer:
            vehicle.total_odometer = position.odometer
    
    async def get_vehicle_status(self, vehicle_id: int) -> Optional[dict]:
        """Get vehicle's current status including online indicator."""
        vehicle = await self._get_vehicle(vehicle_id)
        if not vehicle:
            return None
        
        return {
            "id": vehicle.id,
            "registration_plate": vehicle.registration_plate,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "status": vehicle.status.value,
            "is_online": vehicle.is_online,
            "last_seen": vehicle.last_seen,
            "current_speed": vehicle.current_speed,
            "current_heading": vehicle.current_heading,
        }
    
    async def get_all_vehicles_status(self) -> list[dict]:
        """Get status of all vehicles."""
        result = await self.db.execute(select(Vehicle))
        vehicles = result.scalars().all()
        
        return [
            {
                "id": v.id,
                "registration_plate": v.registration_plate,
                "brand": v.brand,
                "model": v.model,
                "status": v.status.value,
                "is_online": v.is_online,
                "last_seen": v.last_seen,
                "current_speed": v.current_speed,
            }
            for v in vehicles
        ]
    
    async def get_online_vehicles_count(self) -> dict:
        """Get count of online vs offline vehicles."""
        result = await self.db.execute(select(Vehicle))
        vehicles = result.scalars().all()
        
        online = sum(1 for v in vehicles if v.is_online)
        offline = len(vehicles) - online
        
        return {
            "total": len(vehicles),
            "online": online,
            "offline": offline,
        }



"""
Telematics API endpoints for real-time GPS data ingestion.

Handles:
- Single position ingestion
- Batch position ingestion
- Vehicle status queries
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import ValidationError

from app.schemas.telematics import (
    GPSPositionCreate,
    GPSPositionBatch,
    GPSPositionResponse,
    VehicleStatusResponse,
    IngestionStats
)
from app.services.telematics_service import TelematicsService, TelematicsServiceError
from app.api.deps import DbSession, WriteUser, ReadUser


router = APIRouter(prefix="/telematics", tags=["Telematics"])


@router.post("/position", response_model=GPSPositionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_position(
    position: GPSPositionCreate,
    db: DbSession = None,
    current_user: WriteUser = None
) -> GPSPositionResponse:
    """
    Ingest a single GPS position from a telematics device.
    
    This endpoint is designed to receive position updates from connected
    vehicle tracking devices (typically every 1-5 minutes).
    
    **Payload:**
    - vehicle_id: ID of the vehicle
    - driver_id: Optional driver ID (if known from RFID)
    - lat: Latitude (-90 to 90)
    - lon: Longitude (-180 to 180)
    - speed: Speed in km/h
    - heading: Direction (0-360 degrees)
    - odometer: Current odometer reading in km
    - ignition: Ignition status (true/false)
    - timestamp: Position timestamp in UTC
    """
    service = TelematicsService(db)
    
    try:
        gps_position = await service.ingest_position(position)
        
        return GPSPositionResponse(
            id=gps_position.id,
            vehicle_id=gps_position.vehicle_id,
            driver_id=gps_position.driver_id,
            lat=position.lat,
            lon=position.lon,
            speed=gps_position.speed,
            heading=gps_position.heading,
            timestamp=gps_position.timestamp
        )
        
    except TelematicsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/position/batch", response_model=IngestionStats)
async def ingest_positions_batch(
    batch: GPSPositionBatch,
    db: DbSession = None,
    current_user: WriteUser = None
) -> IngestionStats:
    """
    Ingest a batch of GPS positions.
    
    Useful for:
    - Catching up after connectivity loss
    - High-frequency tracking scenarios
    - Bulk data import
    
    Maximum 1000 positions per batch.
    """
    service = TelematicsService(db)
    return await service.ingest_batch(batch.positions)


@router.get("/status/{vehicle_id}", response_model=VehicleStatusResponse)
async def get_vehicle_status(
    vehicle_id: int,
    db: DbSession = None,
    current_user: ReadUser = None
) -> VehicleStatusResponse:
    """
    Get current status of a specific vehicle.
    
    Returns:
    - Basic vehicle info
    - Online/offline status (based on last GPS ping < 5 min)
    - Current speed and heading
    - Last seen timestamp
    """
    service = TelematicsService(db)
    status_data = await service.get_vehicle_status(vehicle_id)
    
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )
    
    return VehicleStatusResponse(**status_data)


@router.get("/status", response_model=list[VehicleStatusResponse])
async def get_all_vehicles_status(
    db: DbSession = None,
    current_user: ReadUser = None
) -> list[VehicleStatusResponse]:
    """Get status of all vehicles with online indicators."""
    service = TelematicsService(db)
    vehicles = await service.get_all_vehicles_status()
    return [VehicleStatusResponse(**v) for v in vehicles]


@router.get("/stats/online")
async def get_online_stats(
    db: DbSession = None,
    current_user: ReadUser = None
) -> dict:
    """Get count of online vs offline vehicles."""
    service = TelematicsService(db)
    return await service.get_online_vehicles_count()


# Lightweight endpoint for device heartbeats (no auth required for devices)
@router.post("/ping")
async def device_ping(
    position: GPSPositionCreate,
    db: DbSession = None
) -> dict:
    """
    Lightweight ping endpoint for telematics devices.
    
    This endpoint has minimal overhead for high-frequency updates.
    Returns simple success/failure response.
    """
    service = TelematicsService(db)
    
    try:
        gps_position = await service.ingest_position(position)
        return {
            "status": "ok",
            "id": gps_position.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except TelematicsServiceError as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "Internal error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }



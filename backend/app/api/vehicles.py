from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleWithDriver
from app.api.deps import DbSession, ReadUser, WriteUser


router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=list[VehicleWithDriver])
async def list_vehicles(
    db: DbSession,
    current_user: ReadUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: VehicleStatus | None = Query(None, alias="status")
) -> list[VehicleWithDriver]:
    """List all vehicles with pagination and optional status filter."""
    query = select(Vehicle).options(selectinload(Vehicle.current_driver))
    
    if status_filter:
        query = query.where(Vehicle.status == status_filter)
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Vehicle.id)
    )
    return result.scalars().all()


@router.get("/{vehicle_id}", response_model=VehicleWithDriver)
async def get_vehicle(
    vehicle_id: int,
    db: DbSession,
    current_user: ReadUser
) -> VehicleWithDriver:
    """Get a specific vehicle by ID."""
    result = await db.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.current_driver))
        .where(Vehicle.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )
    
    return vehicle


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can create
) -> VehicleResponse:
    """Create a new vehicle."""
    # Check if registration plate already exists
    result = await db.execute(
        select(Vehicle).where(Vehicle.registration_plate == vehicle_data.registration_plate)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration plate already registered"
        )
    
    # Check if VIN already exists
    result = await db.execute(
        select(Vehicle).where(Vehicle.vin == vehicle_data.vin)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VIN already registered"
        )
    
    new_vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(new_vehicle)
    await db.flush()
    await db.refresh(new_vehicle)
    
    return new_vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can update
) -> VehicleResponse:
    """Update an existing vehicle."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )
    
    update_data = vehicle_data.model_dump(exclude_unset=True)
    
    # Validate uniqueness constraints
    if "registration_plate" in update_data:
        result = await db.execute(
            select(Vehicle).where(
                Vehicle.registration_plate == update_data["registration_plate"],
                Vehicle.id != vehicle_id
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration plate already registered"
            )
    
    if "vin" in update_data:
        result = await db.execute(
            select(Vehicle).where(
                Vehicle.vin == update_data["vin"],
                Vehicle.id != vehicle_id
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="VIN already registered"
            )
    
    for field, value in update_data.items():
        setattr(vehicle, field, value)
    
    await db.flush()
    await db.refresh(vehicle)
    
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: int,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can delete
) -> None:
    """Delete a vehicle."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )
    
    # Check if vehicle is assigned to a driver
    result = await db.execute(
        select(Driver).where(Driver.current_vehicle_id == vehicle_id)
    )
    driver = result.scalar_one_or_none()
    if driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete vehicle. It is assigned to driver {driver.name}. Unassign first."
        )
    
    await db.delete(vehicle)
    await db.flush()


@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
async def update_vehicle_status(
    vehicle_id: int,
    new_status: VehicleStatus,
    db: DbSession,
    current_user: WriteUser
) -> VehicleResponse:
    """Update vehicle status (ACTIVE, MAINTENANCE, INACTIVE)."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )
    
    vehicle.status = new_status
    
    await db.flush()
    await db.refresh(vehicle)
    
    return vehicle


@router.get("/by-plate/{plate}", response_model=VehicleWithDriver)
async def get_vehicle_by_plate(
    plate: str,
    db: DbSession,
    current_user: ReadUser
) -> VehicleWithDriver:
    """Get a vehicle by its registration plate."""
    result = await db.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.current_driver))
        .where(Vehicle.registration_plate == plate)
    )
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with plate {plate} not found"
        )
    
    return vehicle




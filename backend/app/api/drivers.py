from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse, DriverWithVehicle
from app.api.deps import DbSession, ReadUser, WriteUser


router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverWithVehicle])
async def list_drivers(
    db: DbSession,
    current_user: ReadUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> list[DriverWithVehicle]:
    """List all drivers with pagination."""
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.current_vehicle))
        .offset(skip)
        .limit(limit)
        .order_by(Driver.id)
    )
    return result.scalars().all()


@router.get("/{driver_id}", response_model=DriverWithVehicle)
async def get_driver(
    driver_id: int,
    db: DbSession,
    current_user: ReadUser
) -> DriverWithVehicle:
    """Get a specific driver by ID."""
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.current_vehicle))
        .where(Driver.id == driver_id)
    )
    driver = result.scalar_one_or_none()
    
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    return driver


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_data: DriverCreate,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can create
) -> DriverResponse:
    """Create a new driver."""
    # Check if license number already exists
    result = await db.execute(
        select(Driver).where(Driver.license_number == driver_data.license_number)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License number already registered"
        )
    
    # Check if RFID tag already exists (if provided)
    if driver_data.rfid_tag:
        result = await db.execute(
            select(Driver).where(Driver.rfid_tag == driver_data.rfid_tag)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RFID tag already registered"
            )
    
    # Validate vehicle exists if provided
    if driver_data.current_vehicle_id:
        result = await db.execute(
            select(Vehicle).where(Vehicle.id == driver_data.current_vehicle_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with ID {driver_data.current_vehicle_id} not found"
            )
    
    new_driver = Driver(**driver_data.model_dump())
    db.add(new_driver)
    await db.flush()
    await db.refresh(new_driver)
    
    return new_driver


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can update
) -> DriverResponse:
    """Update an existing driver."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    update_data = driver_data.model_dump(exclude_unset=True)
    
    # Validate uniqueness constraints
    if "license_number" in update_data:
        result = await db.execute(
            select(Driver).where(
                Driver.license_number == update_data["license_number"],
                Driver.id != driver_id
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered"
            )
    
    if "rfid_tag" in update_data and update_data["rfid_tag"]:
        result = await db.execute(
            select(Driver).where(
                Driver.rfid_tag == update_data["rfid_tag"],
                Driver.id != driver_id
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RFID tag already registered"
            )
    
    # Validate vehicle exists if provided
    if "current_vehicle_id" in update_data and update_data["current_vehicle_id"]:
        result = await db.execute(
            select(Vehicle).where(Vehicle.id == update_data["current_vehicle_id"])
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with ID {update_data['current_vehicle_id']} not found"
            )
    
    for field, value in update_data.items():
        setattr(driver, field, value)
    
    await db.flush()
    await db.refresh(driver)
    
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: int,
    db: DbSession,
    current_user: WriteUser  # Only RH and ADMIN can delete
) -> None:
    """Delete a driver."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    await db.delete(driver)
    await db.flush()


@router.post("/{driver_id}/assign-vehicle/{vehicle_id}", response_model=DriverWithVehicle)
async def assign_vehicle_to_driver(
    driver_id: int,
    vehicle_id: int,
    db: DbSession,
    current_user: WriteUser
) -> DriverWithVehicle:
    """Assign a vehicle to a driver."""
    # Get driver
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.current_vehicle))
        .where(Driver.id == driver_id)
    )
    driver = result.scalar_one_or_none()
    
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    # Get vehicle
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
    
    # Check if vehicle is already assigned to another driver
    if vehicle.current_driver and vehicle.current_driver.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle is already assigned to driver {vehicle.current_driver.name}"
        )
    
    # Unassign current vehicle if any
    if driver.current_vehicle_id and driver.current_vehicle_id != vehicle_id:
        driver.current_vehicle_id = None
    
    # Assign new vehicle
    driver.current_vehicle_id = vehicle_id
    
    await db.flush()
    await db.refresh(driver)
    
    return driver


@router.post("/{driver_id}/unassign-vehicle", response_model=DriverResponse)
async def unassign_vehicle_from_driver(
    driver_id: int,
    db: DbSession,
    current_user: WriteUser
) -> DriverResponse:
    """Unassign the current vehicle from a driver."""
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    driver.current_vehicle_id = None
    
    await db.flush()
    await db.refresh(driver)
    
    return driver




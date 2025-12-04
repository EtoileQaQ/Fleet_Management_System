from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DriverBase(BaseModel):
    """Base driver schema."""
    name: str
    license_number: str
    rfid_tag: str | None = None
    timezone: str = "UTC"


class DriverCreate(DriverBase):
    """Driver creation schema."""
    current_vehicle_id: int | None = None


class DriverUpdate(BaseModel):
    """Driver update schema."""
    name: str | None = None
    license_number: str | None = None
    rfid_tag: str | None = None
    timezone: str | None = None
    current_vehicle_id: int | None = None


class DriverResponse(DriverBase):
    """Driver response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    current_vehicle_id: int | None
    created_at: datetime
    updated_at: datetime


class VehicleBasic(BaseModel):
    """Basic vehicle info for nested responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    registration_plate: str
    brand: str
    model: str


class DriverWithVehicle(DriverResponse):
    """Driver response with vehicle details."""
    current_vehicle: VehicleBasic | None = None




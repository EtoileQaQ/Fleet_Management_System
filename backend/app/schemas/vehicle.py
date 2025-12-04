from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.vehicle import VehicleStatus


class VehicleBase(BaseModel):
    """Base vehicle schema."""
    registration_plate: str
    vin: str = Field(..., min_length=17, max_length=17)
    brand: str
    model: str
    status: VehicleStatus = VehicleStatus.ACTIVE


class VehicleCreate(VehicleBase):
    """Vehicle creation schema."""
    pass


class VehicleUpdate(BaseModel):
    """Vehicle update schema."""
    registration_plate: str | None = None
    vin: str | None = Field(None, min_length=17, max_length=17)
    brand: str | None = None
    model: str | None = None
    status: VehicleStatus | None = None


class VehicleResponse(VehicleBase):
    """Vehicle response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class DriverBasic(BaseModel):
    """Basic driver info for nested responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    license_number: str


class VehicleWithDriver(VehicleResponse):
    """Vehicle response with driver details."""
    current_driver: DriverBasic | None = None




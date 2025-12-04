from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class GPSPositionCreate(BaseModel):
    """Schema for incoming GPS position data from telematics devices."""
    vehicle_id: int
    driver_id: Optional[int] = None
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, le=360, description="Heading in degrees")
    odometer: Optional[float] = Field(None, ge=0, description="Odometer reading in km")
    ignition: Optional[bool] = Field(False, description="Ignition status")
    timestamp: datetime = Field(..., description="Position timestamp in UTC")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future."""
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        # Allow 1 minute tolerance for clock drift
        if v > now + timedelta(minutes=1):
            raise ValueError("Timestamp cannot be in the future")
        return v


class GPSPositionBatch(BaseModel):
    """Schema for batch GPS position upload."""
    positions: list[GPSPositionCreate] = Field(..., min_length=1, max_length=1000)


class GPSPositionResponse(BaseModel):
    """Response schema for GPS position."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    vehicle_id: int
    driver_id: Optional[int]
    lat: float
    lon: float
    speed: Optional[float]
    heading: Optional[float]
    timestamp: datetime


class VehicleStatusResponse(BaseModel):
    """Vehicle status with online indicator."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    registration_plate: str
    brand: str
    model: str
    status: str
    is_online: bool
    last_seen: Optional[datetime]
    current_speed: Optional[float]
    current_heading: Optional[float]


class IngestionStats(BaseModel):
    """Statistics for ingestion operations."""
    total_received: int
    successfully_processed: int
    failed: int
    errors: list[str] = []



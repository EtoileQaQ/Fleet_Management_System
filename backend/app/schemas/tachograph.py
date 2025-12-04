from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.driver_activity import ActivityType, ActivitySource


class ActivityRecord(BaseModel):
    """Parsed activity record from tachograph file."""
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    odometer_start: Optional[float] = None
    odometer_end: Optional[float] = None
    distance_km: Optional[float] = None


class TachographParseResult(BaseModel):
    """Result of parsing a tachograph file."""
    success: bool
    card_number: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_registration: Optional[str] = None
    activities: list[ActivityRecord] = []
    total_driving_minutes: int = 0
    total_rest_minutes: int = 0
    total_work_minutes: int = 0
    errors: list[str] = []
    warnings: list[str] = []


class DriverActivityCreate(BaseModel):
    """Schema for creating driver activity."""
    driver_id: int
    vehicle_id: Optional[int] = None
    activity_type: ActivityType
    source: ActivitySource = ActivitySource.TACHOGRAPH
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    odometer_start: Optional[float] = None
    odometer_end: Optional[float] = None
    distance_km: Optional[float] = None
    source_file: Optional[str] = None
    card_number: Optional[str] = None


class DriverActivityResponse(BaseModel):
    """Response schema for driver activity."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    driver_id: int
    vehicle_id: Optional[int]
    activity_type: ActivityType
    source: ActivitySource
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    odometer_start: Optional[float]
    odometer_end: Optional[float]
    distance_km: Optional[float]
    source_file: Optional[str]
    card_number: Optional[str]
    created_at: datetime


class TachographUploadResponse(BaseModel):
    """Response for tachograph file upload."""
    success: bool
    filename: str
    driver_id: Optional[int] = None
    activities_created: int = 0
    activities_skipped: int = 0  # Duplicates/overlaps
    parse_result: TachographParseResult
    errors: list[str] = []


class ActivitySummary(BaseModel):
    """Summary of driver activities for a period."""
    driver_id: int
    driver_name: str
    period_start: datetime
    period_end: datetime
    total_driving_hours: float
    total_rest_hours: float
    total_work_hours: float
    total_distance_km: float
    violations: list[str] = []  # e.g., "Exceeded 9h driving limit"



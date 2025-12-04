"""
Tachograph file upload and processing endpoints.

Handles:
- File upload (DDD/TGD)
- Parsing and activity extraction
- Storage of driver activities
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy import select

from app.models.driver import Driver
from app.models.driver_activity import DriverActivity, ActivityType
from app.schemas.tachograph import (
    TachographUploadResponse,
    DriverActivityResponse,
    ActivitySummary
)
from app.services.tachograph_parser import parse_tachograph_bytes
from app.services.activity_service import ActivityService, ActivityServiceError
from app.api.deps import DbSession, WriteUser, ReadUser


router = APIRouter(prefix="/tachograph", tags=["Tachograph"])


ALLOWED_EXTENSIONS = {'.ddd', '.tgd', '.DDD', '.TGD'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=TachographUploadResponse)
async def upload_tachograph_file(
    file: UploadFile = File(...),
    driver_id: int = Form(...),
    vehicle_id: Optional[int] = Form(None),
    db: DbSession = None,
    current_user: WriteUser = None
) -> TachographUploadResponse:
    """
    Upload and process a tachograph file (.DDD or .TGD).
    
    - **file**: Tachograph file (DDD for driver card, TGD for vehicle unit)
    - **driver_id**: ID of the driver to associate activities with
    - **vehicle_id**: Optional vehicle ID
    
    Returns parsed activities and storage results.
    """
    # Validate file extension
    filename = file.filename or "unknown"
    extension = "." + filename.split(".")[-1] if "." in filename else ""
    
    if extension.lower() not in {'.ddd', '.tgd'}:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            errors=[f"Invalid file type. Allowed: .DDD, .TGD. Got: {extension}"]
        )
    
    # Read file content
    try:
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            return TachographUploadResponse(
                success=False,
                filename=filename,
                errors=[f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"]
            )
        
        if len(content) == 0:
            return TachographUploadResponse(
                success=False,
                filename=filename,
                errors=["Empty file"]
            )
            
    except Exception as e:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            errors=[f"Failed to read file: {str(e)}"]
        )
    
    # Verify driver exists
    driver_result = await db.execute(
        select(Driver).where(Driver.id == driver_id)
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            errors=[f"Driver with ID {driver_id} not found"]
        )
    
    # Parse the tachograph file
    parse_result = parse_tachograph_bytes(content, filename)
    
    if not parse_result.success:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            driver_id=driver_id,
            parse_result=parse_result,
            errors=parse_result.errors
        )
    
    # Store activities
    try:
        service = ActivityService(db)
        created, skipped = await service.store_activities_from_tachograph(
            driver_id=driver_id,
            parse_result=parse_result,
            source_file=filename,
            vehicle_id=vehicle_id
        )
        
        # Update driver's card number if found
        if parse_result.card_number and not driver.card_number:
            driver.card_number = parse_result.card_number
            await db.flush()
        
        return TachographUploadResponse(
            success=True,
            filename=filename,
            driver_id=driver_id,
            activities_created=created,
            activities_skipped=skipped,
            parse_result=parse_result
        )
        
    except ActivityServiceError as e:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            driver_id=driver_id,
            parse_result=parse_result,
            errors=[str(e)]
        )
    except Exception as e:
        return TachographUploadResponse(
            success=False,
            filename=filename,
            driver_id=driver_id,
            parse_result=parse_result,
            errors=[f"Failed to store activities: {str(e)}"]
        )


@router.get("/activities/{driver_id}", response_model=list[DriverActivityResponse])
async def get_driver_activities(
    driver_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    activity_type: Optional[ActivityType] = Query(None),
    db: DbSession = None,
    current_user: ReadUser = None
) -> list[DriverActivityResponse]:
    """Get activities for a specific driver."""
    service = ActivityService(db)
    activities = await service.get_driver_activities(
        driver_id, start_date, end_date, activity_type
    )
    return activities


@router.get("/summary/{driver_id}", response_model=ActivitySummary)
async def get_activity_summary(
    driver_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: DbSession = None,
    current_user: ReadUser = None
) -> ActivitySummary:
    """Get activity summary for a driver over a period."""
    service = ActivityService(db)
    try:
        return await service.get_activity_summary(driver_id, start_date, end_date)
    except ActivityServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/fuse-gps/{driver_id}")
async def fuse_gps_with_activities(
    driver_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: DbSession = None,
    current_user: WriteUser = None
) -> dict:
    """Associate GPS positions with driver activities."""
    service = ActivityService(db)
    count = await service.fuse_gps_with_activities(driver_id, start_time, end_time)
    return {
        "driver_id": driver_id,
        "gps_positions_associated": count
    }



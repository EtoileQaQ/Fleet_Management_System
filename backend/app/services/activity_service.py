"""
Activity service for managing driver activities.

This service handles:
- Storing parsed tachograph activities
- Detecting and handling overlapping activities
- Fusing GPS data with driver activities
- Activity summary and compliance reporting
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.driver import Driver
from app.models.driver_activity import DriverActivity, ActivityType, ActivitySource
from app.models.gps_position import GPSPosition
from app.schemas.tachograph import (
    TachographParseResult, 
    DriverActivityCreate,
    ActivitySummary
)


class ActivityServiceError(Exception):
    """Exception raised for activity service errors."""
    pass


class ActivityService:
    """Service for managing driver activities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def store_activities_from_tachograph(
        self,
        driver_id: int,
        parse_result: TachographParseResult,
        source_file: str,
        vehicle_id: Optional[int] = None
    ) -> tuple[int, int]:
        """
        Store activities from a parsed tachograph file.
        
        Args:
            driver_id: ID of the driver
            parse_result: Parsed tachograph result
            source_file: Name of the source file
            vehicle_id: Optional vehicle ID
            
        Returns:
            Tuple of (created_count, skipped_count)
        """
        created = 0
        skipped = 0
        
        for activity in parse_result.activities:
            # Check for overlapping activities
            existing = await self._find_overlapping_activity(
                driver_id,
                activity.start_time,
                activity.end_time
            )
            
            if existing:
                # Skip if exact duplicate
                if (existing.start_time == activity.start_time and
                    existing.end_time == activity.end_time and
                    existing.activity_type == activity.activity_type):
                    skipped += 1
                    continue
                
                # Handle partial overlap - for now, skip
                # Future: implement merging logic
                skipped += 1
                continue
            
            # Create new activity
            new_activity = DriverActivity(
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                activity_type=activity.activity_type,
                source=ActivitySource.TACHOGRAPH,
                start_time=activity.start_time,
                end_time=activity.end_time,
                duration_minutes=activity.duration_minutes,
                odometer_start=activity.odometer_start,
                odometer_end=activity.odometer_end,
                distance_km=activity.distance_km,
                source_file=source_file,
                card_number=parse_result.card_number
            )
            
            self.db.add(new_activity)
            created += 1
        
        if created > 0:
            await self.db.flush()
        
        return created, skipped
    
    async def create_activity(
        self,
        activity_data: DriverActivityCreate
    ) -> DriverActivity:
        """Create a single driver activity."""
        # Check for overlaps
        existing = await self._find_overlapping_activity(
            activity_data.driver_id,
            activity_data.start_time,
            activity_data.end_time
        )
        
        if existing:
            raise ActivityServiceError(
                f"Activity overlaps with existing activity from "
                f"{existing.start_time} to {existing.end_time}"
            )
        
        activity = DriverActivity(**activity_data.model_dump())
        self.db.add(activity)
        await self.db.flush()
        await self.db.refresh(activity)
        
        return activity
    
    async def _find_overlapping_activity(
        self,
        driver_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[DriverActivity]:
        """Find any activity that overlaps with the given time range."""
        result = await self.db.execute(
            select(DriverActivity).where(
                and_(
                    DriverActivity.driver_id == driver_id,
                    DriverActivity.start_time < end_time,
                    DriverActivity.end_time > start_time
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_driver_activities(
        self,
        driver_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_type: Optional[ActivityType] = None
    ) -> list[DriverActivity]:
        """Get activities for a driver with optional filters."""
        query = select(DriverActivity).where(
            DriverActivity.driver_id == driver_id
        )
        
        if start_date:
            query = query.where(DriverActivity.start_time >= start_date)
        if end_date:
            query = query.where(DriverActivity.end_time <= end_date)
        if activity_type:
            query = query.where(DriverActivity.activity_type == activity_type)
        
        query = query.order_by(DriverActivity.start_time.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_activity_summary(
        self,
        driver_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> ActivitySummary:
        """Get activity summary for a driver over a period."""
        # Get driver
        driver_result = await self.db.execute(
            select(Driver).where(Driver.id == driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if not driver:
            raise ActivityServiceError(f"Driver {driver_id} not found")
        
        # Get activities in range
        activities = await self.get_driver_activities(
            driver_id, start_date, end_date
        )
        
        # Calculate totals
        driving_minutes = sum(
            a.duration_minutes for a in activities 
            if a.activity_type == ActivityType.DRIVING
        )
        rest_minutes = sum(
            a.duration_minutes for a in activities 
            if a.activity_type in [ActivityType.REST, ActivityType.BREAK]
        )
        work_minutes = sum(
            a.duration_minutes for a in activities 
            if a.activity_type == ActivityType.WORK
        )
        distance = sum(
            a.distance_km or 0 for a in activities
        )
        
        # Check for violations (simplified)
        violations = []
        
        # Check daily driving limit (9h normal, 10h max 2x/week)
        daily_driving_hours = driving_minutes / 60
        if daily_driving_hours > 10:
            violations.append(f"Exceeded maximum daily driving limit: {daily_driving_hours:.1f}h")
        elif daily_driving_hours > 9:
            violations.append(f"Extended daily driving: {daily_driving_hours:.1f}h (max 2x/week)")
        
        return ActivitySummary(
            driver_id=driver_id,
            driver_name=driver.name,
            period_start=start_date,
            period_end=end_date,
            total_driving_hours=driving_minutes / 60,
            total_rest_hours=rest_minutes / 60,
            total_work_hours=work_minutes / 60,
            total_distance_km=distance,
            violations=violations
        )
    
    async def fuse_gps_with_activities(
        self,
        driver_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        Associate GPS positions with driver activities based on timestamps.
        
        Returns the number of GPS positions associated.
        """
        # Get activities in range
        activities = await self.get_driver_activities(
            driver_id, start_time, end_time
        )
        
        if not activities:
            return 0
        
        # Get GPS positions for the driver in the time range
        result = await self.db.execute(
            select(GPSPosition).where(
                and_(
                    GPSPosition.driver_id == driver_id,
                    GPSPosition.timestamp >= start_time,
                    GPSPosition.timestamp <= end_time
                )
            )
        )
        gps_positions = result.scalars().all()
        
        # Associate each GPS position with the corresponding activity
        associated_count = 0
        for gps in gps_positions:
            for activity in activities:
                if activity.start_time <= gps.timestamp <= activity.end_time:
                    # GPS position falls within this activity
                    # Store association in raw_data or create separate table
                    if not activity.raw_data:
                        activity.raw_data = "[]"
                    
                    import json
                    data = json.loads(activity.raw_data)
                    data.append({
                        "gps_id": gps.id,
                        "timestamp": gps.timestamp.isoformat()
                    })
                    activity.raw_data = json.dumps(data)
                    associated_count += 1
                    break
        
        if associated_count > 0:
            await self.db.flush()
        
        return associated_count



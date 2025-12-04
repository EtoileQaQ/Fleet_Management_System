import asyncio
from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy import delete
from app.celery_worker.celery_app import celery_app
from app.database import async_session_maker
from app.models.gps_position import GPSPosition


@celery_app.task(name="app.celery_worker.tasks.cleanup_old_positions")
def cleanup_old_positions(days: int = 90):
    """
    Cleanup GPS positions older than specified days.
    This is a periodic maintenance task.
    """
    async def _cleanup():
        async with async_session_maker() as session:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = await session.execute(
                delete(GPSPosition).where(GPSPosition.timestamp < cutoff_date)
            )
            await session.commit()
            
            return result.rowcount
    
    deleted_count = asyncio.run(_cleanup())
    return {"deleted_positions": deleted_count, "days_threshold": days}


@celery_app.task(name="app.celery_worker.tasks.process_gps_data")
def process_gps_data(vehicle_id: int, lat: float, lon: float, speed: float = None):
    """
    Process incoming GPS data asynchronously.
    This task can be called when receiving GPS data from trackers.
    """
    async def _process():
        from geoalchemy2.elements import WKTElement
        
        async with async_session_maker() as session:
            position = GPSPosition(
                vehicle_id=vehicle_id,
                timestamp=datetime.now(timezone.utc),
                location=WKTElement(f"POINT({lon} {lat})", srid=4326),
                speed=speed
            )
            session.add(position)
            await session.commit()
            
            return position.id
    
    position_id = asyncio.run(_process())
    return {"position_id": position_id, "vehicle_id": vehicle_id}


@celery_app.task(name="app.celery_worker.tasks.send_notification")
def send_notification(user_id: int, message: str, notification_type: str = "info"):
    """
    Send notification to user (placeholder for future implementation).
    """
    # TODO: Implement actual notification logic (email, push, etc.)
    return {
        "user_id": user_id,
        "message": message,
        "type": notification_type,
        "status": "sent"
    }




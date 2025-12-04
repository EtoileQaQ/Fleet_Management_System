from celery import Celery
from app.config import settings


celery_app = Celery(
    "fleet_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.celery_worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-positions": {
        "task": "app.celery_worker.tasks.cleanup_old_positions",
        "schedule": 86400.0,  # Daily
    },
}




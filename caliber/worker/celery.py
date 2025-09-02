"""
Celery configuration and app setup
"""

from celery import Celery
import os
from config.settings import settings

# Create Celery app
celery_app = Celery(
    "caliber",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["worker.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-reports": {
        "task": "worker.tasks.cleanup_old_reports",
        "schedule": 60.0 * 60 * 24,  # Daily
    },
}

if __name__ == "__main__":
    celery_app.start()
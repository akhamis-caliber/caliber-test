from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "caliber_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['worker.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'worker.tasks.process_campaign_scoring': {'queue': 'scoring'},
        'worker.tasks.process_scoring_task': {'queue': 'scoring'},
        'worker.tasks.generate_optimization_lists_task': {'queue': 'scoring'},
        'worker.tasks.cleanup_old_files_task': {'queue': 'maintenance'},
        'worker.tasks.generate_export': {'queue': 'exports'},
        'worker.tasks.health_check': {'queue': 'monitoring'},
        'worker.tasks.cleanup_old_exports': {'queue': 'maintenance'},
        'worker.tasks.update_campaign_statistics': {'queue': 'maintenance'},
        'worker.tasks.send_completion_notification': {'queue': 'notifications'},
    },
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster'
    },
    
    # Worker settings
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Rate limiting
    task_annotations={
        'worker.tasks.process_campaign_scoring': {'rate_limit': '10/m'},
        'worker.tasks.process_scoring_task': {'rate_limit': '10/m'},
        'worker.tasks.cleanup_old_files_task': {'rate_limit': '1/h'},
        'worker.tasks.generate_export': {'rate_limit': '50/m'},
        'worker.tasks.health_check': {'rate_limit': '12/m'},
    }
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'worker.tasks.cleanup_old_files_task',
        'schedule': 24 * 60 * 60,  # Run daily at midnight
        'options': {'queue': 'maintenance'}
    },
    'cleanup-old-exports': {
        'task': 'worker.tasks.cleanup_old_exports',
        'schedule': 4 * 60 * 60,  # Run every 4 hours
        'options': {'queue': 'maintenance'}
    },
    'health-check': {
        'task': 'worker.tasks.health_check',
        'schedule': 5 * 60,  # Run every 5 minutes
        'options': {'queue': 'monitoring'}
    },
    'update-campaign-stats': {
        'task': 'worker.tasks.update_campaign_statistics',
        'schedule': 60 * 60,  # Run hourly
        'options': {'queue': 'maintenance'}
    }
}

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready event"""
    logger.info("Celery worker is ready and waiting for tasks")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown event"""
    logger.info("Celery worker is shutting down")

# Task failure handler
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures"""
    logger.error(f"Task {task_id} failed: {error}")
    logger.error(f"Traceback: {traceback}") 
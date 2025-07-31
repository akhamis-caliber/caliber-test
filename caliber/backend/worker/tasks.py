from celery import current_task
from celery.exceptions import Retry
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging
import uuid
import traceback
import json
import asyncio
import os
from pathlib import Path
from typing import Dict, Any

from config.settings import settings
from worker.celery import celery_app
from scoring_service.controllers import ScoringController
from report_service.storage import file_storage
from report_service.exports import ExportService
from db.models import Campaign, User, ScoringResult, FileUpload
from scoring_service.config import ScoringConfigManager, ScoringPlatform, CampaignGoal, Channel
from common.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

# Create database session factory
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """Get database session for tasks"""
    return SessionLocal()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_campaign_scoring(self, campaign_id_str: str, user_id_str: str):
    """
    Main task for processing campaign scoring
    
    Args:
        campaign_id_str: Campaign UUID as string
        user_id_str: User UUID as string
    """
    campaign_id = uuid.UUID(campaign_id_str)
    user_id = uuid.UUID(user_id_str)
    
    db = get_db_session()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting scoring task {task_id} for campaign {campaign_id}")
        
        # Get user and campaign
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception(f"User {user_id} not found")
        
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id
        ).first()
        if not campaign:
            raise Exception(f"Campaign {campaign_id} not found for user {user_id}")
        
        # Update task metadata
        self.update_state(
            state='PROGRESS',
            meta={
                'campaign_id': campaign_id_str,
                'current_step': 'initializing',
                'progress': 0,
                'message': 'Starting scoring process'
            }
        )
        
        # Set campaign status to processing
        campaign.status = "processing"
        campaign.progress_percentage = 5
        db.commit()
        
        # Progress tracking function
        def update_progress(percentage: int, step: str, message: str = ""):
            campaign.progress_percentage = percentage
            db.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'campaign_id': campaign_id_str,
                    'current_step': step,
                    'progress': percentage,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Task {task_id}: {step} - {percentage}% - {message}")
        
        # Step 1: Load and validate data
        update_progress(10, 'loading_data', 'Loading campaign data file')
        
        if not campaign.file_path:
            raise Exception("No file uploaded for campaign")
        
        # Step 2: Process scoring using the main controller
        update_progress(20, 'preprocessing', 'Preprocessing and validating data')
        
        # Get scoring configuration
        config = ScoringConfigManager.get_config(
            platform=ScoringPlatform(campaign.scoring_platform or "trade_desk"),
            goal=CampaignGoal(campaign.goal or "awareness"),
            channel=Channel(campaign.channel or "display"),
            ctr_sensitivity=campaign.ctr_sensitivity or False
        )
        
        # Use the existing scoring controller with progress callbacks
        result = ScoringController._process_scoring(db, campaign, config)
        
        # Step 3: Finalize results
        update_progress(95, 'finalizing', 'Finalizing scoring results')
        
        # Update campaign status
        campaign.status = "completed"
        campaign.progress_percentage = 100
        campaign.completed_at = datetime.utcnow()
        campaign.error_message = None
        db.commit()
        
        update_progress(100, 'completed', 'Scoring completed successfully')
        
        logger.info(f"Scoring task {task_id} completed successfully for campaign {campaign_id}")
        
        return {
            'success': True,
            'campaign_id': campaign_id_str,
            'total_records': result.get('total_records', 0),
            'processing_time': result.get('processing_time', 0),
            'campaign_score': result.get('campaign_score', 0),
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Scoring task {task_id} failed: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update campaign with error
        try:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                campaign.status = "failed"
                campaign.error_message = str(exc)
                campaign.progress_percentage = 0
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update campaign error status: {db_error}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'campaign_id': campaign_id_str,
                'error': str(exc),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 60  # Exponential backoff
            logger.info(f"Retrying task {task_id} in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=countdown)
        
        raise exc
        
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=2)
def generate_export(self, campaign_id_str: str, user_id_str: str, export_format: str, 
                   include_insights: bool = True, filters: dict = None):
    """
    Generate export files in background
    
    Args:
        campaign_id_str: Campaign UUID as string
        user_id_str: User UUID as string
        export_format: Export format ('csv' or 'pdf')
        include_insights: Whether to include AI insights
        filters: Export filters
    """
    campaign_id = uuid.UUID(campaign_id_str)
    user_id = uuid.UUID(user_id_str)
    
    db = get_db_session()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting export task {task_id} for campaign {campaign_id} in {export_format} format")
        
        # Verify campaign
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id
        ).first()
        
        if not campaign:
            raise Exception(f"Campaign {campaign_id} not found")
        
        self.update_state(
            state='PROGRESS',
            meta={
                'campaign_id': campaign_id_str,
                'format': export_format,
                'progress': 25,
                'message': f'Generating {export_format.upper()} export'
            }
        )
        
        # Generate export
        if export_format == "csv":
            export_data = ExportService.export_to_csv(
                db=db,
                campaign_id=campaign_id,
                filters=filters,
                include_breakdown=include_insights
            )
        elif export_format == "pdf":
            from report_service.pdf_generator import PDFReportGenerator
            pdf_generator = PDFReportGenerator()
            export_data = pdf_generator.generate_campaign_report(
                db=db,
                campaign_id=campaign_id,
                include_insights=include_insights
            )
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        self.update_state(
            state='PROGRESS',
            meta={
                'campaign_id': campaign_id_str,
                'format': export_format,
                'progress': 75,
                'message': 'Saving export file'
            }
        )
        
        # Save export file
        filename = f"caliber_export_{campaign.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        # Use asyncio to call async storage function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            export_path, file_size = loop.run_until_complete(
                file_storage.save_uploaded_file(
                    export_data, filename, str(user_id), f"export_{campaign_id}"
                )
            )
        finally:
            loop.close()
        
        result = {
            'success': True,
            'export_path': export_path,
            'filename': filename,
            'file_size': file_size,
            'format': export_format,
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        self.update_state(
            state='SUCCESS',
            meta={
                'campaign_id': campaign_id_str,
                'format': export_format,
                'progress': 100,
                'message': 'Export completed successfully',
                'result': result
            }
        )
        
        logger.info(f"Export task {task_id} completed: {filename} ({file_size} bytes)")
        return result
        
    except Exception as exc:
        logger.error(f"Export task {task_id} failed: {exc}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'campaign_id': campaign_id_str,
                'format': export_format,
                'error': str(exc),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 30
            raise self.retry(exc=exc, countdown=countdown)
        
        raise exc
        
    finally:
        db.close()

@celery_app.task
def cleanup_old_exports():
    """
    Cleanup old export files (older than 24 hours)
    Runs every 4 hours
    """
    try:
        logger.info("Starting export cleanup task")
        
        storage_path = Path("storage")
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        cleaned_count = 0
        total_size_freed = 0
        
        # Find and remove old export files
        for user_dir in storage_path.iterdir():
            if user_dir.is_dir():
                for file_path in user_dir.glob("export_*"):
                    try:
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            
                            cleaned_count += 1
                            total_size_freed += file_size
                            
                            logger.info(f"Cleaned up export file: {file_path} ({file_size} bytes)")
                            
                    except Exception as e:
                        logger.error(f"Failed to cleanup export file {file_path}: {e}")
        
        logger.info(f"Export cleanup completed: {cleaned_count} files removed, {total_size_freed} bytes freed")
        
        return {
            'exports_cleaned': cleaned_count,
            'bytes_freed': total_size_freed,
            'cutoff_time': cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Export cleanup task failed: {e}")
        raise

@celery_app.task
def health_check():
    """
    Health check task to monitor system status
    Runs every 5 minutes
    """
    try:
        db = get_db_session()
        
        # Test database connection
        try:
            campaign_count = db.query(Campaign).count()
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            campaign_count = 0
        finally:
            db.close()
        
        # Test Redis connection
        try:
            from config.redis import redis_manager
            redis_client = redis_manager.get_client()
            if redis_client:
                redis_client.ping()
                redis_status = "healthy"
            else:
                redis_status = "disconnected"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        # Test file storage
        try:
            storage_path = Path("storage")
            storage_available = storage_path.exists() and storage_path.is_dir()
            storage_status = "healthy" if storage_available else "unavailable"
        except Exception as e:
            storage_status = f"unhealthy: {str(e)}"
        
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'status': db_status,
                'campaign_count': campaign_count
            },
            'redis': {
                'status': redis_status
            },
            'storage': {
                'status': storage_status
            },
            'overall': 'healthy' if all(
                status in ['healthy'] for status in [db_status, redis_status, storage_status]
            ) else 'degraded'
        }
        
        logger.info(f"Health check completed: {health_status['overall']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall': 'failed',
            'error': str(e)
        }

@celery_app.task
def update_campaign_statistics():
    """
    Update campaign statistics and metrics
    Runs hourly
    """
    db = get_db_session()
    
    try:
        logger.info("Starting campaign statistics update")
        
        # Calculate statistics
        stats = {
            'total_campaigns': db.query(Campaign).count(),
            'completed_campaigns': db.query(Campaign).filter(
                Campaign.status == 'completed'
            ).count(),
            'processing_campaigns': db.query(Campaign).filter(
                Campaign.status == 'processing'
            ).count(),
            'total_users': db.query(User).count(),
            'total_scored_domains': db.query(ScoringResult).count(),
            'avg_campaign_score': db.query(func.avg(ScoringResult.score)).scalar() or 0
        }
        
        # Store in Redis for quick access
        try:
            from config.redis import redis_manager
            redis_client = redis_manager.get_client()
            if redis_client:
                redis_client.setex(
                    'campaign_statistics',
                    3600,  # 1 hour expiry
                    json.dumps(stats)
                )
        except Exception as e:
            logger.warning(f"Failed to cache statistics in Redis: {e}")
        
        logger.info(f"Campaign statistics updated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to update campaign statistics: {e}")
        raise
    finally:
        db.close()

@celery_app.task(bind=True)
def send_completion_notification(self, campaign_id_str: str, user_email: str):
    """
    Send notification when campaign scoring is completed
    (Placeholder for email/notification integration)
    """
    try:
        logger.info(f"Sending completion notification for campaign {campaign_id_str} to {user_email}")
        
        # TODO: Integrate with email service (SendGrid, SES, etc.)
        # For now, just log the notification
        
        notification_data = {
            'campaign_id': campaign_id_str,
            'user_email': user_email,
            'message': 'Your campaign scoring has been completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store notification in Redis for potential UI pickup
        try:
            from config.redis import redis_manager
            redis_client = redis_manager.get_client()
            if redis_client:
                redis_client.lpush(
                    f'notifications:{user_email}',
                    json.dumps(notification_data)
                )
                redis_client.expire(f'notifications:{user_email}', 86400)  # 24 hours
        except Exception as e:
            logger.warning(f"Failed to store notification: {e}")
        
        return notification_data
        
    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")
        raise

@celery_app.task(bind=True)
def generate_optimization_lists_task(self, campaign_id: str, user_id: str) -> Dict[str, Any]:
    """
    Background task to generate whitelist and blacklist for a campaign
    """
    try:
        campaign_uuid = uuid.UUID(campaign_id)
        user_uuid = uuid.UUID(user_id)
        
        # Get database session
        db = next(get_db())
        
        # Get campaign and user
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_uuid,
            Campaign.user_id == user_uuid
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise NotFoundError("User")
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Generating optimization lists...'}
        )
        
        # Generate whitelist
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Generating whitelist...'}
        )
        
        whitelist = ScoringController.generate_optimization_list(
            db=db,
            campaign_id=campaign_uuid,
            user=user,
            list_type="whitelist",
            min_impressions=250
        )
        
        # Generate blacklist
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Generating blacklist...'}
        )
        
        blacklist = ScoringController.generate_optimization_list(
            db=db,
            campaign_id=campaign_uuid,
            user=user,
            list_type="blacklist",
            min_impressions=250
        )
        
        # Update final state
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': 'Optimization lists generated successfully',
                'whitelist_count': len(whitelist['domains']),
                'blacklist_count': len(blacklist['domains'])
            }
        )
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'whitelist': whitelist,
            'blacklist': blacklist
        }
        
    except Exception as e:
        logger.error(f"Optimization lists task failed for campaign {campaign_id}: {e}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Failed to generate optimization lists: {str(e)}',
                'error': str(e)
            }
        )
        
        raise

@celery_app.task(bind=True)
def cleanup_old_files_task(self) -> Dict[str, Any]:
    """
    Background task to cleanup old uploaded files
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting cleanup...'}
        )
        
        # Find old files (older than 30 days)
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_files = db.query(FileUpload).filter(
            FileUpload.upload_date < cutoff_date,
            FileUpload.status == "uploaded"  # Only cleanup unassigned files
        ).all()
        
        deleted_count = 0
        
        for file_upload in old_files:
            try:
                # Delete file from storage
                # await file_storage.delete_file(file_upload.file_path)
                
                # Delete database record
                db.delete(file_upload)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to delete file {file_upload.id}: {e}")
        
        db.commit()
        
        # Update final state
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': f'Cleanup completed. Deleted {deleted_count} files.',
                'deleted_count': deleted_count
            }
        )
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Cleanup failed: {str(e)}',
                'error': str(e)
            }
        )
        
        raise

@celery_app.task(bind=True)
def validate_file_task(self, file_id: str, user_id: str) -> Dict[str, Any]:
    """
    Background task to validate uploaded file structure
    """
    try:
        file_uuid = uuid.UUID(file_id)
        user_uuid = uuid.UUID(user_id)
        
        # Get database session
        db = get_db_session()
        
        # Get file upload record
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_uuid,
            FileUpload.user_id == user_uuid
        ).first()
        
        if not file_upload:
            raise NotFoundError("File upload record")
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Reading file...'}
        )
        
        # Read file content
        file_content = file_storage.read_file(file_upload.file_path)
        
        # Parse file
        import pandas as pd
        import io
        
        if file_upload.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        else:
            df = pd.read_excel(io.BytesIO(file_content))
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Validating file structure...'}
        )
        
        # Validate file structure
        from report_service.uploads import FileUploadService
        upload_service = FileUploadService(db)
        validation_result = upload_service.validate_file_structure(df)
        
        # Update final state
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': 'File validation completed',
                'validation_result': validation_result
            }
        )
        
        return {
            'success': True,
            'file_id': file_id,
            'validation_result': validation_result
        }
        
    except Exception as e:
        logger.error(f"File validation task failed for file {file_id}: {e}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'File validation failed: {str(e)}',
                'error': str(e)
            }
        )
        
        raise 
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..auth_service.middleware import get_current_user
from ..config.database import get_db
from .service import NotificationService
from .schemas import (
    NotificationCreate, 
    NotificationUpdate, 
    NotificationResponse,
    NotificationListResponse,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    BulkNotificationCreate,
    NotificationStats
)
from .models import NotificationType, NotificationPriority

router = APIRouter()

def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get user notifications with pagination"""
    try:
        return notification_service.get_user_notifications(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            unread_only=unread_only,
            notification_type=notification_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}"
        )

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get notification statistics for the current user"""
    try:
        return notification_service.get_notification_stats(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notification stats: {str(e)}"
        )

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create notifications"
        )
    
    try:
        return notification_service.create_notification(notification_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create multiple notifications for multiple users (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create bulk notifications"
        )
    
    try:
        return notification_service.create_bulk_notifications(bulk_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk notifications: {str(e)}"
        )

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read"""
    try:
        notification = notification_service.mark_as_read(notification_id, current_user.id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.put("/read-all")
async def mark_all_notifications_as_read(
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read for the current user"""
    try:
        count = notification_service.mark_all_as_read(current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification"""
    try:
        success = notification_service.delete_notification(notification_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

# Template management routes (admin only)
@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def get_notification_templates(
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get all notification templates"""
    try:
        return notification_service.get_all_templates()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch templates: {str(e)}"
        )

@router.post("/templates", response_model=NotificationTemplateResponse)
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification template (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create templates"
        )
    
    try:
        return notification_service.create_template(template_data.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )

@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_id: int,
    template_data: NotificationTemplateUpdate,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Update a notification template (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update templates"
        )
    
    try:
        template = notification_service.update_template(template_id, template_data.dict(exclude_unset=True))
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )

@router.delete("/templates/{template_id}")
async def delete_notification_template(
    template_id: int,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification template (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete templates"
        )
    
    try:
        success = notification_service.delete_template(template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return {"message": "Template deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )

# System notification routes
@router.post("/system/campaign-completed")
async def notify_campaign_completed(
    user_id: int,
    campaign_name: str,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a campaign completion notification (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system notifications"
        )
    
    try:
        notification = notification_service.notify_campaign_completed(user_id, campaign_name)
        return {"message": "Campaign completion notification created", "notification": notification.to_dict()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.post("/system/data-upload-warning")
async def notify_data_upload_warning(
    user_id: int,
    filename: str,
    issues: List[str],
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a data upload warning notification (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system notifications"
        )
    
    try:
        notification = notification_service.notify_data_upload_warning(user_id, filename, issues)
        return {"message": "Data upload warning notification created", "notification": notification.to_dict()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.post("/system/scoring-completed")
async def notify_scoring_completed(
    user_id: int,
    campaign_name: str,
    score: float,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a scoring completion notification (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system notifications"
        )
    
    try:
        notification = notification_service.notify_scoring_completed(user_id, campaign_name, score)
        return {"message": "Scoring completion notification created", "notification": notification.to_dict()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.post("/system/maintenance")
async def notify_system_maintenance(
    user_ids: List[int],
    maintenance_time: str,
    current_user = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create system maintenance notifications (admin only)"""
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create system notifications"
        )
    
    try:
        notifications = notification_service.notify_system_maintenance(user_ids, maintenance_time)
        return {
            "message": f"System maintenance notifications created for {len(notifications)} users",
            "notifications": [n.to_dict() for n in notifications]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notifications: {str(e)}"
        )

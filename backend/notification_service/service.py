from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import string
from .models import Notification, NotificationTemplate, NotificationType, NotificationPriority
from .schemas import NotificationCreate, NotificationUpdate, BulkNotificationCreate

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification"""
        # If template is specified, use it to format the notification
        if notification_data.template_name:
            template = self.get_template_by_name(notification_data.template_name)
            if template:
                title = self._format_template(template.title_template, notification_data.template_data)
                message = self._format_template(template.message_template, notification_data.template_data)
                notification_type = template.notification_type
                priority = template.priority
            else:
                title = notification_data.title
                message = notification_data.message
                notification_type = notification_data.notification_type
                priority = notification_data.priority
        else:
            title = notification_data.title
            message = notification_data.message
            notification_type = notification_data.notification_type
            priority = notification_data.priority

        notification = Notification(
            user_id=notification_data.user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def create_bulk_notifications(self, bulk_data: BulkNotificationCreate) -> List[Notification]:
        """Create multiple notifications for multiple users"""
        notifications = []
        template = None
        
        if bulk_data.template_name:
            template = self.get_template_by_name(bulk_data.template_name)
        
        for user_id in bulk_data.user_ids:
            if template:
                title = self._format_template(template.title_template, bulk_data.template_data)
                message = self._format_template(template.message_template, bulk_data.template_data)
                notification_type = template.notification_type
                priority = template.priority
            else:
                title = "Notification"
                message = "You have a new notification"
                notification_type = bulk_data.notification_type
                priority = bulk_data.priority
            
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority
            )
            notifications.append(notification)
        
        self.db.add_all(notifications)
        self.db.commit()
        
        for notification in notifications:
            self.db.refresh(notification)
        
        return notifications

    def get_user_notifications(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 20,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None
    ) -> Dict[str, Any]:
        """Get paginated notifications for a user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        
        total = query.count()
        unread_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).count()
        
        notifications = query.order_by(desc(Notification.created_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "notifications": [notification.to_dict() for notification in notifications],
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "per_page": per_page
        }

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as read"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.read = True
            notification.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notification)
        
        return notification

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        result = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).update({
            "read": True,
            "updated_at": datetime.utcnow()
        })
        
        self.db.commit()
        return result

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        
        return False

    def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        total = self.db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).count()
        read = total - unread
        
        # Notifications by type
        by_type = self.db.query(
            Notification.notification_type,
            func.count(Notification.id)
        ).filter(Notification.user_id == user_id)\
         .group_by(Notification.notification_type)\
         .all()
        
        notifications_by_type = {nt.value: count for nt, count in by_type}
        
        # Notifications by priority
        by_priority = self.db.query(
            Notification.priority,
            func.count(Notification.id)
        ).filter(Notification.user_id == user_id)\
         .group_by(Notification.priority)\
         .all()
        
        notifications_by_priority = {np.value: count for np, count in by_priority}
        
        return {
            "total_notifications": total,
            "unread_count": unread,
            "read_count": read,
            "notifications_by_type": notifications_by_type,
            "notifications_by_priority": notifications_by_priority
        }

    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Clean up old read notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = self.db.query(Notification).filter(
            Notification.read == True,
            Notification.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return result

    # Template management methods
    def create_template(self, template_data: Dict[str, Any]) -> NotificationTemplate:
        """Create a new notification template"""
        template = NotificationTemplate(**template_data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get a template by name"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.name == name,
            NotificationTemplate.is_active == True
        ).first()

    def get_all_templates(self) -> List[NotificationTemplate]:
        """Get all active templates"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.is_active == True
        ).all()

    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Optional[NotificationTemplate]:
        """Update a template"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if template:
            for key, value in template_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            self.db.commit()
            self.db.refresh(template)
        
        return template

    def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if template:
            self.db.delete(template)
            self.db.commit()
            return True
        
        return False

    def _format_template(self, template: str, data: Dict[str, Any]) -> str:
        """Format a template string with provided data"""
        try:
            return string.Template(template).safe_substitute(data)
        except Exception:
            return template

    # System notification methods
    def notify_campaign_completed(self, user_id: int, campaign_name: str) -> Notification:
        """Create a campaign completion notification"""
        return self.create_notification(NotificationCreate(
            user_id=user_id,
            title="Campaign Completed",
            message=f"Your campaign '{campaign_name}' has been successfully processed.",
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.MEDIUM
        ))

    def notify_data_upload_warning(self, user_id: int, filename: str, issues: List[str]) -> Notification:
        """Create a data upload warning notification"""
        issues_text = ", ".join(issues[:3])  # Show first 3 issues
        if len(issues) > 3:
            issues_text += f" and {len(issues) - 3} more"
        
        return self.create_notification(NotificationCreate(
            user_id=user_id,
            title="Data Upload Warning",
            message=f"Some data entries in '{filename}' need attention: {issues_text}",
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH
        ))

    def notify_scoring_completed(self, user_id: int, campaign_name: str, score: float) -> Notification:
        """Create a scoring completion notification"""
        return self.create_notification(NotificationCreate(
            user_id=user_id,
            title="Scoring Completed",
            message=f"Scoring for campaign '{campaign_name}' completed with score: {score:.2f}",
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.MEDIUM
        ))

    def notify_system_maintenance(self, user_ids: List[int], maintenance_time: str) -> List[Notification]:
        """Create system maintenance notifications"""
        return self.create_bulk_notifications(BulkNotificationCreate(
            user_ids=user_ids,
            template_name="system_maintenance",
            template_data={"maintenance_time": maintenance_time},
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.HIGH
        ))

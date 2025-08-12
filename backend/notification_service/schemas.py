from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.MEDIUM

class NotificationCreate(NotificationBase):
    user_id: int
    template_name: Optional[str] = None
    template_data: Optional[dict] = {}

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    read: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int

class NotificationTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    title_template: str = Field(..., min_length=1, max_length=255)
    message_template: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.MEDIUM

class NotificationTemplateCreate(NotificationTemplateBase):
    pass

class NotificationTemplateUpdate(BaseModel):
    title_template: Optional[str] = Field(None, min_length=1, max_length=255)
    message_template: Optional[str] = Field(None, min_length=1)
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    is_active: Optional[bool] = None

class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class BulkNotificationCreate(BaseModel):
    user_ids: List[int]
    template_name: str
    template_data: Optional[dict] = {}
    notification_type: Optional[NotificationType] = NotificationType.INFO
    priority: Optional[NotificationPriority] = NotificationPriority.MEDIUM

class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    notifications_by_type: dict
    notifications_by_priority: dict

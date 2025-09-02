"""
MongoDB database models using Beanie ODM for Caliber application
"""

from beanie import Document, Link
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class UserRole(str, Enum):
    ADMIN = "Admin"
    USER = "User"


class CampaignType(str, Enum):
    TRADEDESK = "TradeDesk"
    PULSEPOINT = "PulsePoint"


class CampaignGoal(str, Enum):
    AWARENESS = "Awareness" 
    ACTION = "Action"


class AnalysisLevel(str, Enum):
    DOMAIN = "DOMAIN"
    VENDOR = "VENDOR"


class CampaignStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class ReportStatus(str, Enum):
    UPLOADED = "Uploaded"
    SCORING = "Scoring"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ScoreStatus(str, Enum):
    GOOD = "Good"
    MODERATE = "Moderate"
    POOR = "Poor"


class PasswordReset(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = Field(..., index=True)
    email: str = Field(..., index=True)
    reset_token: str = Field(..., unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "password_resets"
        indexes = [
            "user_id",
            "email", 
            "reset_token",
            "expires_at"
        ]


class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: str = Field(..., unique=True, index=True)
    name: str
    password_hash: str = Field(..., exclude=True)  # Exclude from API responses
    firebase_uid: Optional[str] = Field(None, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "firebase_uid"
        ]


class Organization(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "organizations"


class Membership(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    org_id: str
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "memberships"
        indexes = [
            "user_id",
            "org_id",
            [("user_id", 1), ("org_id", 1)]  # compound index
        ]


class CampaignTemplate(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    org_id: str
    name: str
    goal: CampaignGoal
    channels: List[str] = Field(default_factory=list)
    ctr_sensitivity: bool = False
    analysis_level: AnalysisLevel
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "campaign_templates"
        indexes = [
            "org_id",
            "created_by"
        ]


class Campaign(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    org_id: str
    name: str
    campaign_type: CampaignType
    goal: CampaignGoal
    channel: str
    ctr_sensitivity: bool = False
    analysis_level: AnalysisLevel
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    
    class Settings:
        name = "campaigns"
        indexes = [
            "org_id",
            "created_by",
            "status"
        ]


class Report(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    campaign_id: str
    filename: str
    storage_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: ReportStatus = ReportStatus.UPLOADED
    summary_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Settings:
        name = "reports"
        indexes = [
            "campaign_id",
            "status"
        ]


class ScoreRow(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    report_id: str
    domain: str
    publisher: Optional[str] = None
    cpm: Optional[float] = None
    ctr: Optional[float] = None
    conversion_rate: Optional[float] = None
    impressions: Optional[int] = None
    total_spend: Optional[float] = None
    conversions: Optional[int] = None
    score: float  # 0-100
    status: ScoreStatus
    channel: Optional[str] = None
    vendor: Optional[str] = None
    explanation: Optional[str] = None
    
    class Settings:
        name = "score_rows"
        indexes = [
            "report_id",  # Primary query field
            "domain",
            "score",
            "status",
            # Compound indexes for common query patterns
            [("report_id", 1), ("score", -1)],  # For sorting by score within a report
            [("report_id", 1), ("status", 1)],  # For filtering by status within a report
            [("report_id", 1), ("domain", 1)],  # For domain lookups within a report
            # Performance indexes
            [("report_id", 1), ("score", -1), ("status", 1)],  # For complex filtering
            [("report_id", 1), ("ctr", -1)],  # For CTR-based sorting
            [("report_id", 1), ("cpm", 1)],   # For CPM-based sorting (ascending for lower CPM)
        ]
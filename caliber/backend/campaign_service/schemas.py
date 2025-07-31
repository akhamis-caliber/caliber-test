from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid
from common.schemas import BaseSchema

class CampaignType(str, Enum):
    TRADE_DESK = "trade_desk"
    PULSEPOINT = "pulsepoint"

class CampaignGoal(str, Enum):
    AWARENESS = "awareness"
    ACTION = "action"

class Channel(str, Enum):
    CTV = "ctv"
    DISPLAY = "display"
    VIDEO = "video"
    AUDIO = "audio"

class AnalysisLevel(str, Enum):
    DOMAIN = "domain"
    SUPPLY_VENDOR = "supply_vendor"

class CampaignStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CampaignTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    goal: CampaignGoal
    channel: Channel
    ctr_sensitivity: bool
    analysis_level: AnalysisLevel

class CampaignTemplateResponse(BaseSchema):
    name: str
    campaign_type: CampaignType
    goal: CampaignGoal
    channel: Channel
    ctr_sensitivity: bool
    analysis_level: AnalysisLevel
    user_id: uuid.UUID

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    template_id: Optional[uuid.UUID] = None
    # If template_id is None, include template fields
    campaign_type: Optional[CampaignType] = None
    goal: Optional[CampaignGoal] = None
    channel: Optional[Channel] = None
    ctr_sensitivity: Optional[bool] = None
    analysis_level: Optional[AnalysisLevel] = None

    @model_validator(mode='after')
    def validate_template_fields(self):
        if self.template_id is None:
            # If no template, all fields are required
            required_fields = ['campaign_type', 'goal', 'channel', 'ctr_sensitivity', 'analysis_level']
            missing_fields = []
            for field in required_fields:
                if getattr(self, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValueError(f'Fields {", ".join(missing_fields)} are required when template_id is not provided')
        return self

class CampaignResponse(BaseSchema):
    name: str
    status: CampaignStatus
    template_id: Optional[uuid.UUID]
    file_path: Optional[str]
    total_records: Optional[int]
    processed_records: Optional[int]
    error_message: Optional[str]
    completed_at: Optional[datetime]
    user_id: uuid.UUID

class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int 
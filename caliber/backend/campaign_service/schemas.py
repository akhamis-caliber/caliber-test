"""
Pydantic schemas for campaign service
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from db.models import CampaignType, CampaignGoal, AnalysisLevel, CampaignStatus


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    goal: CampaignGoal
    channel: str = Field(..., min_length=1, max_length=100)
    ctr_sensitivity: bool = False
    analysis_level: AnalysisLevel


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[CampaignStatus] = None
    channel: Optional[str] = Field(None, min_length=1, max_length=100)
    ctr_sensitivity: Optional[bool] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: CampaignType
    goal: CampaignGoal
    channel: str
    ctr_sensitivity: bool
    analysis_level: AnalysisLevel
    status: CampaignStatus
    created_at: datetime
    updated_at: Optional[datetime]
    org_id: str
    created_by: str
    reports_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class CampaignTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    goal: CampaignGoal
    channels: List[str] = Field(..., min_items=1)
    ctr_sensitivity: bool = False
    analysis_level: AnalysisLevel


class CampaignTemplateResponse(BaseModel):
    id: str
    name: str
    goal: CampaignGoal
    channels: List[str]
    ctr_sensitivity: bool
    analysis_level: AnalysisLevel
    created_at: datetime
    
    class Config:
        from_attributes = True
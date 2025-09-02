"""
Pydantic schemas for report service
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from db.models import ReportStatus, ScoreStatus


class ReportUploadResponse(BaseModel):
    report_id: str
    filename: str
    rows_count: int
    columns: List[str]
    preview_data: List[Dict[str, Any]]
    validation_errors: List[str] = []
    
    
class StartScoringResponse(BaseModel):
    report_id: str
    message: str
    task_id: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    campaign_id: str
    filename: str
    uploaded_at: datetime
    status: ReportStatus
    summary_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    rows_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ScoreRowResponse(BaseModel):
    id: str
    domain: str
    publisher: Optional[str] = None
    cmp: Optional[float] = None
    ctr: Optional[float] = None
    conversion_rate: Optional[float] = None
    impressions: Optional[int] = None
    total_spend: Optional[float] = None
    conversions: Optional[int] = None
    score: float
    status: ScoreStatus
    channel: Optional[str] = None
    vendor: Optional[str] = None
    explanation: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportSummaryResponse(BaseModel):
    total_rows: int
    score_distribution: Dict[str, int]
    top_domains: List[Dict[str, Any]]
    metrics_summary: Dict[str, Dict[str, float]]
    
    
class ExportRequest(BaseModel):
    format: str = Field(..., regex="^(csv|pdf)$")
    filters: Optional[Dict[str, Any]] = None
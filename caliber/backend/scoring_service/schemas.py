from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from common.schemas import BaseSchema

class ScoringRequest(BaseModel):
    campaign_id: uuid.UUID
    file_path: str
    force_reprocess: bool = False

class ScoringProgress(BaseModel):
    campaign_id: uuid.UUID
    status: str
    progress_percentage: int
    current_step: str
    total_records: Optional[int] = None
    processed_records: Optional[int] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None

class ScoringResultSummary(BaseModel):
    campaign_id: uuid.UUID
    total_domains: int
    average_score: float
    score_distribution: Dict[str, int]
    top_performers: List[Dict[str, Any]]
    bottom_performers: List[Dict[str, Any]]
    data_quality_issues: List[str]
    processing_time_seconds: float

class DomainScore(BaseModel):
    domain: str
    impressions: int
    spend: float
    cpm: float
    ctr: float
    conversions: int
    conversion_rate: float
    score: float
    percentile_rank: int
    quality_status: str
    score_breakdown: Dict[str, Any]

class ScoringResultsResponse(BaseModel):
    campaign_id: uuid.UUID
    results: List[DomainScore]
    summary: ScoringResultSummary
    normalization_stats: Dict[str, Any]
    scoring_config: Dict[str, Any]

class WhitelistBlacklistRequest(BaseModel):
    campaign_id: uuid.UUID
    list_type: str = Field(..., pattern="^(whitelist|blacklist)$")
    min_impressions: int = Field(default=250, ge=1)

class OptimizationListResponse(BaseModel):
    list_type: str
    campaign_id: uuid.UUID
    domains: List[str]
    criteria_used: Dict[str, Any]
    total_impressions: int
    average_score: float 
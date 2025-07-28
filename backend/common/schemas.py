from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Scoring-related enums
class ScoringJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ScoringJobType(str, Enum):
    STANDARD = "standard"
    BATCH = "batch"
    COMPARISON = "comparison"

class MetricType(str, Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    BINARY = "binary"

class NormalizationMethod(str, Enum):
    ZSCORE = "zscore"
    MINMAX = "minmax"
    ROBUST = "robust"

class OutlierMethod(str, Enum):
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"

class OutlierAction(str, Enum):
    MARK = "mark"
    REMOVE = "remove"
    CAP = "cap"

# Scoring Configuration Schemas
class ScoringMetricConfig(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: MetricType
    description: Optional[str] = None
    weight: float = Field(1.0, ge=0.0, le=1.0)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    normalization_method: Optional[NormalizationMethod] = None
    outlier_method: Optional[OutlierMethod] = None
    outlier_action: Optional[OutlierAction] = None
    is_active: bool = True

class ScoringConfig(BaseModel):
    metrics: List[ScoringMetricConfig]
    outlier_config: Optional[Dict[str, Any]] = {
        "method": OutlierMethod.IQR,
        "action": OutlierAction.MARK
    }
    normalization_config: Optional[Dict[str, Any]] = {
        "method": NormalizationMethod.ZSCORE,
        "columns": None
    }
    weighting_config: Optional[Dict[str, Any]] = {
        "strategy": "linear",
        "metrics": None
    }
    explanation_config: Optional[Dict[str, Any]] = {
        "explanation_type": "score_breakdown",
        "include_metrics": None
    }

    @validator('metrics')
    def validate_metrics(cls, v):
        if not v:
            raise ValueError("At least one metric must be configured")
        
        # Validate total weight equals 1.0
        total_weight = sum(metric.weight for metric in v)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError("Total weight of metrics must equal 1.0")
        
        return v

# Scoring Job Schemas
class ScoringJobCreate(BaseModel):
    report_id: int
    campaign_id: int
    job_type: ScoringJobType = ScoringJobType.STANDARD
    config: Optional[ScoringConfig] = None

class ScoringJobUpdate(BaseModel):
    status: Optional[ScoringJobStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    error_message: Optional[str] = None
    config: Optional[ScoringConfig] = None

class ScoringJobResponse(BaseModel):
    id: int
    report_id: int
    campaign_id: int
    user_id: int
    task_id: Optional[str] = None
    status: ScoringJobStatus
    job_type: ScoringJobType
    config: Optional[Dict[str, Any]] = None
    progress: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Scoring Results Schemas
class ScoringResultDetail(BaseModel):
    metric_name: str
    metric_value: Optional[float] = None
    score: float
    weight: float
    weighted_score: Optional[float] = None
    explanation: Optional[str] = None
    metric_metadata: Optional[Dict[str, Any]] = None

class ScoringResultsResponse(BaseModel):
    report_id: int
    campaign_id: int
    final_score: float
    score_rank: int
    component_scores: List[ScoringResultDetail]
    outlier_flags: Optional[Dict[str, bool]] = None
    explanation: Optional[str] = None
    processed_at: datetime

    class Config:
        from_attributes = True

class ScoringSummaryResponse(BaseModel):
    total_records: int
    average_score: float
    median_score: float
    std_score: float
    min_score: float
    max_score: float
    score_distribution: Dict[str, int]
    processing_time: float
    outlier_summary: Optional[Dict[str, Any]] = None
    normalization_summary: Optional[Dict[str, Any]] = None
    weighting_summary: Optional[Dict[str, Any]] = None

# Campaign Scoring Integration Schemas
class CampaignScoringConfig(BaseModel):
    campaign_id: int
    scoring_config: ScoringConfig
    target_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    auto_score_reports: bool = False
    batch_processing: bool = False

class CampaignScoringStats(BaseModel):
    campaign_id: int
    total_reports: int
    scored_reports: int
    average_score: Optional[float] = None
    score_distribution: Dict[str, int]
    recent_scores: List[float]
    performance_trends: Optional[Dict[str, Any]] = None

# API Request/Response Schemas
class ScoreReportRequest(BaseModel):
    report_id: int
    campaign_id: int
    config: Optional[ScoringConfig] = None
    priority: str = "normal"  # low, normal, high

class BatchScoreRequest(BaseModel):
    campaign_id: int
    report_ids: List[int]
    config: Optional[ScoringConfig] = None
    priority: str = "normal"

class ScoringComparisonRequest(BaseModel):
    report_id: int
    campaign_id: int
    configs: List[ScoringConfig]
    comparison_name: Optional[str] = None

# Worker Task Schemas
class ScoringTaskPayload(BaseModel):
    job_id: int
    report_id: int
    campaign_id: int
    user_id: int
    file_path: str
    config: Optional[Dict[str, Any]] = None
    task_type: str = "standard"

class ScoringTaskResult(BaseModel):
    job_id: int
    success: bool
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None

# Utility Schemas
class ScoringTemplate(BaseModel):
    id: int
    name: str
    description: str
    category: str
    config: ScoringConfig
    is_default: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class ScoringValidationError(BaseModel):
    field: str
    message: str
    value: Optional[Any] = None

class ScoringValidationResponse(BaseModel):
    is_valid: bool
    errors: List[ScoringValidationError] = []
    warnings: List[str] = []

# AI Service Schemas
class AIInsightRequest(BaseModel):
    campaign_id: int
    analysis_type: Optional[str] = "comprehensive"
    include_recommendations: bool = True

class AIInsightResponse(BaseModel):
    campaign_id: int
    insights: List[str]
    recommendations: List[str]
    key_findings: List[str]
    trends: Dict[str, Any]
    generated_at: datetime
    data_summary: Dict[str, Any]

class AIExplanationRequest(BaseModel):
    report_id: int
    explanation_type: str = "comprehensive"  # comprehensive, summary, technical
    detail_level: str = "detailed"  # basic, detailed, expert

class AIExplanationResponse(BaseModel):
    report_id: int
    explanation_type: str
    detail_level: str
    explanation: str
    generated_at: datetime

class AIQAResponse(BaseModel):
    question: str
    answer: str
    campaign_id: Optional[int]
    generated_at: datetime

class AIRecommendationRequest(BaseModel):
    campaign_id: int
    focus_area: Optional[str] = None  # performance, quality, efficiency, etc.

class AIRecommendationResponse(BaseModel):
    campaign_id: int
    recommendations: List[str]
    focus_area: Optional[str]
    generated_at: datetime

class AITrendAnalysisResponse(BaseModel):
    campaign_id: int
    time_period: str
    trends: List[Dict[str, Any]]
    patterns: Dict[str, Any]
    insights: List[str]
    forecast: Dict[str, Any]
    generated_at: datetime

# User Authentication Schemas
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    organization: Optional[str] = Field(None, max_length=255)
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    organization: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(BaseModel):
    id: int
    email: str
    full_name: str
    organization: Optional[str] = None
    role: str
    firebase_uid: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: str
    user_id: int

class GoogleLoginRequest(BaseModel):
    id_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# Health Check Schema
class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: datetime
    version: str 
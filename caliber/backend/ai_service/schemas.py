from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class InsightRequest(BaseModel):
    campaign_id: uuid.UUID
    insight_type: str = Field(..., description="Type of insight to generate")
    context_data: Dict[str, Any] = Field(default={}, description="Additional context data")

class DomainInsightRequest(BaseModel):
    campaign_id: uuid.UUID
    domain_data: Dict[str, Any] = Field(..., description="Domain performance data")

class WhitelistInsightRequest(BaseModel):
    campaign_id: uuid.UUID
    whitelist_data: Dict[str, Any] = Field(..., description="Whitelist data for analysis")

class BlacklistInsightRequest(BaseModel):
    campaign_id: uuid.UUID
    blacklist_data: Dict[str, Any] = Field(..., description="Blacklist data for analysis")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    campaign_id: Optional[uuid.UUID] = Field(None, description="Optional campaign context")
    context_data: Dict[str, Any] = Field(default={}, description="Additional context")

class InsightResponse(BaseModel):
    campaign_id: uuid.UUID
    insight_type: str
    content: str
    generated_at: datetime
    context_data: Optional[Dict[str, Any]] = None
    domain: Optional[str] = None
    whitelist_data: Optional[Dict[str, Any]] = None
    blacklist_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime
    context: Optional[str] = None

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    timestamp: datetime

class ChatHistory(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class BatchInsightRequest(BaseModel):
    campaign_id: uuid.UUID
    insight_types: List[str] = Field(..., description="List of insight types to generate")
    context_data: Dict[str, Any] = Field(default={}, description="Shared context data")

class BatchInsightResponse(BaseModel):
    campaign_id: uuid.UUID
    insights: List[InsightResponse]
    generated_at: datetime
    total_insights: int
    failed_insights: List[str] = Field(default=[], description="List of failed insight types")

class InsightSummary(BaseModel):
    insight_id: uuid.UUID
    insight_type: str
    content: str
    created_at: datetime
    campaign_id: uuid.UUID

class CampaignInsightsResponse(BaseModel):
    campaign_id: uuid.UUID
    insights: List[InsightSummary]
    total_insights: int
    insight_types: List[str]

class AIStatusResponse(BaseModel):
    service_status: str = Field(..., description="AI service status")
    openai_configured: bool
    cache_enabled: bool
    rate_limit_remaining: Optional[int] = None
    last_request_time: Optional[datetime] = None

class InsightTypeInfo(BaseModel):
    type: str
    description: str
    required_context: List[str] = Field(default=[], description="Required context fields")
    optional_context: List[str] = Field(default=[], description="Optional context fields")

class InsightTypesResponse(BaseModel):
    insight_types: List[str]
    descriptions: Dict[str, str]
    type_details: List[InsightTypeInfo] = Field(default=[])

class ErrorResponse(BaseModel):
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 
"""
Pydantic schemas for AI service
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID


class InsightResponse(BaseModel):
    report_id: str
    insights_text: str
    key_findings: List[str]
    recommendations: List[str]
    generated_at: str


class ChatRequest(BaseModel):
    report_id: UUID
    message: str = Field(..., min_length=1, max_length=500)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    report_id: str
    conversation_id: str
    timestamp: str
    sources: Optional[List[str]] = None
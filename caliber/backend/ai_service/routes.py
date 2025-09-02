"""
AI service routes for insights and chat (MongoDB/Beanie)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from common.deps import get_current_user, get_current_org
from db.models import User, Organization

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    report_id: Optional[str] = None


@router.post("/insights")
async def generate_insights(
    report_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Generate AI insights for a report"""
    # TODO: Implement actual AI insight generation
    return {
        "report_id": report_id,
        "insights": [
            "40% of domains achieve 'Good' performance scores",
            "Top performer: demo-site.net with score 91.2", 
            "Average CTR across all domains: 2.16%"
        ],
        "recommendations": [
            "Focus budget on top 2 performing domains",
            "Consider blacklisting bottom 20% of domains",
            "Optimize creative for better CTR performance"
        ]
    }


@router.post("/chat")
async def chat_with_report(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Chat with AI about report data"""
    # TODO: Implement actual AI chat functionality
    return {
        "response": f"Thank you for your question: '{chat_request.message}'. This is a placeholder response. AI chat functionality will be implemented with OpenAI integration.",
        "report_id": chat_request.report_id
    }
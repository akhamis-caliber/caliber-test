from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid

from config.database import get_db
from auth_service.dependencies import get_current_user
from ai_service.controllers import AIController
from ai_service.schemas import (
    InsightRequest, ChatRequest, InsightResponse, ChatResponse,
    DomainInsightRequest, WhitelistInsightRequest, BlacklistInsightRequest
)
from common.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/insights/generate", response_model=InsightResponse)
async def generate_insight(
    request: InsightRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI insight for a campaign"""
    try:
        result = AIController.generate_campaign_insight(
            db=db,
            campaign_id=request.campaign_id,
            insight_type=request.insight_type,
            context_data=request.context_data,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")

@router.post("/insights/domain", response_model=InsightResponse)
async def generate_domain_insight(
    request: DomainInsightRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI insight for a specific domain"""
    try:
        result = AIController.generate_domain_insight(
            db=db,
            campaign_id=request.campaign_id,
            domain_data=request.domain_data,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Domain insight generation failed: {str(e)}")

@router.post("/insights/whitelist", response_model=InsightResponse)
async def generate_whitelist_insight(
    request: WhitelistInsightRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI insight for whitelist"""
    try:
        result = AIController.generate_whitelist_insight(
            db=db,
            campaign_id=request.campaign_id,
            whitelist_data=request.whitelist_data,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whitelist insight generation failed: {str(e)}")

@router.post("/insights/blacklist", response_model=InsightResponse)
async def generate_blacklist_insight(
    request: BlacklistInsightRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI insight for blacklist"""
    try:
        result = AIController.generate_blacklist_insight(
            db=db,
            campaign_id=request.campaign_id,
            blacklist_data=request.blacklist_data,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blacklist insight generation failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Chat with AI assistant"""
    try:
        result = AIController.chat_with_ai(
            db=db,
            user_id=str(current_user.id),
            message=request.message,
            campaign_id=request.campaign_id,
            context_data=request.context_data
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/insights/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign_insights(
    campaign_id: uuid.UUID = Path(...),
    insight_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all insights for a campaign"""
    try:
        result = AIController.get_campaign_insights(
            db=db,
            campaign_id=campaign_id,
            insight_type=insight_type,
            user=current_user
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/insights/{insight_id}")
async def delete_insight(
    insight_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an insight"""
    try:
        AIController.delete_insight(
            db=db,
            insight_id=insight_id,
            user=current_user
        )
        return {"message": "Insight deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/insights/campaign/{campaign_id}")
async def clear_campaign_insights(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Clear all insights for a campaign"""
    try:
        AIController.clear_campaign_insights(
            db=db,
            campaign_id=campaign_id,
            user=current_user
        )
        return {"message": "Campaign insights cleared successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/types", response_model=Dict[str, Any])
async def get_insight_types():
    """Get available insight types"""
    from ai_service.config import InsightTypes
    
    return {
        "insight_types": InsightTypes.get_all_types(),
        "descriptions": {
            "performance": "Performance analysis and key metrics insights",
            "optimization": "Optimization recommendations and strategies",
            "whitelist": "Analysis of top-performing domains",
            "blacklist": "Analysis of poor-performing domains",
            "domain": "Individual domain performance analysis",
            "campaign_overview": "Comprehensive campaign overview and assessment"
        }
    }

@router.post("/insights/batch", response_model=Dict[str, Any])
async def generate_batch_insights(
    campaign_id: uuid.UUID = Body(...),
    insight_types: list = Body(...),
    context_data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate multiple insights for a campaign in batch"""
    try:
        result = AIController.generate_batch_insights(
            db=db,
            campaign_id=campaign_id,
            insight_types=insight_types,
            context_data=context_data,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch insight generation failed: {str(e)}")

@router.get("/chat/history/{conversation_id}", response_model=Dict[str, Any])
async def get_chat_history(
    conversation_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get chat conversation history"""
    try:
        result = AIController.get_chat_history(
            db=db,
            conversation_id=conversation_id,
            user=current_user
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/history/{conversation_id}")
async def clear_chat_history(
    conversation_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Clear chat conversation history"""
    try:
        AIController.clear_chat_history(
            db=db,
            conversation_id=conversation_id,
            user=current_user
        )
        return {"message": "Chat history cleared successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
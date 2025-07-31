from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid

from config.database import get_db
from auth_service.dependencies import get_current_user
from scoring_service.controllers import ScoringController
from scoring_service.schemas import (
    ScoringRequest, ScoringProgress, ScoringResultsResponse,
    WhitelistBlacklistRequest, OptimizationListResponse
)
from common.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/scoring", tags=["scoring"])

@router.post("/start", response_model=Dict[str, Any])
async def start_scoring(
    request: ScoringRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start scoring process for a campaign"""
    try:
        result = ScoringController.start_scoring_process(
            db=db,
            campaign_id=request.campaign_id,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@router.get("/progress/{campaign_id}", response_model=ScoringProgress)
async def get_scoring_progress(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get scoring progress for a campaign"""
    try:
        result = ScoringController.get_scoring_progress(
            db=db,
            campaign_id=campaign_id,
            user=current_user
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{campaign_id}", response_model=Dict[str, Any])
async def get_scoring_results(
    campaign_id: uuid.UUID = Path(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("score", regex="^(score|impressions|ctr|conversion_rate|percentile_rank)$"),
    sort_direction: str = Query("desc", regex="^(asc|desc)$"),
    quality_status: Optional[str] = Query(None, regex="^(good|moderate|poor)$"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    min_impressions: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get paginated scoring results with filtering and sorting"""
    try:
        # Build filters
        filters = {}
        if quality_status:
            filters["quality_status"] = quality_status
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score
        if min_impressions is not None:
            filters["min_impressions"] = min_impressions
        
        result = ScoringController.get_scoring_results(
            db=db,
            campaign_id=campaign_id,
            user=current_user,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_direction=sort_direction,
            filters=filters
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign_summary(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive campaign summary"""
    try:
        result = ScoringController.get_campaign_summary(
            db=db,
            campaign_id=campaign_id,
            user=current_user
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimization-list", response_model=OptimizationListResponse)
async def generate_optimization_list(
    request: WhitelistBlacklistRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate whitelist or blacklist for optimization"""
    try:
        result = ScoringController.generate_optimization_list(
            db=db,
            campaign_id=request.campaign_id,
            user=current_user,
            list_type=request.list_type,
            min_impressions=request.min_impressions
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whitelist/{campaign_id}", response_model=OptimizationListResponse)
async def get_whitelist(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get whitelist for a campaign"""
    try:
        result = ScoringController.generate_optimization_list(
            db=db,
            campaign_id=campaign_id,
            user=current_user,
            list_type="whitelist",
            min_impressions=min_impressions
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blacklist/{campaign_id}", response_model=OptimizationListResponse)
async def get_blacklist(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get blacklist for a campaign"""
    try:
        result = ScoringController.generate_optimization_list(
            db=db,
            campaign_id=campaign_id,
            user=current_user,
            list_type="blacklist",
            min_impressions=min_impressions
        )
        return result
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
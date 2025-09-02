"""
Campaign management routes for MongoDB/Beanie
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from common.deps import get_current_user, get_current_org
from campaign_service.schemas import CampaignResponse
from db.models import User, Organization, Campaign

router = APIRouter()


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """List campaigns for the current organization"""
    campaigns = await Campaign.find(
        Campaign.org_id == current_org.id
    ).skip(skip).limit(limit).to_list()
    
    return [
        CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            campaign_type=campaign.campaign_type,
            goal=campaign.goal,
            channel=campaign.channel,
            ctr_sensitivity=campaign.ctr_sensitivity,
            analysis_level=campaign.analysis_level,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            org_id=campaign.org_id,
            created_by=campaign.created_by,
            reports_count=0  # TODO: Count actual reports
        ) for campaign in campaigns
    ]


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Get campaign details"""
    campaign = await Campaign.find_one(
        Campaign.id == campaign_id,
        Campaign.org_id == current_org.id
    )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "campaign_type": campaign.campaign_type,
        "goal": campaign.goal,
        "channel": campaign.channel,
        "ctr_sensitivity": campaign.ctr_sensitivity,
        "analysis_level": campaign.analysis_level,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat(),
        "org_id": campaign.org_id,
        "created_by": campaign.created_by
    }
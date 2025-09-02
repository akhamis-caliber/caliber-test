"""
Campaign service controllers
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from db.models import Campaign, CampaignTemplate
from campaign_service.schemas import (
    CampaignCreate, CampaignResponse, CampaignTemplateCreate,
    CampaignTemplateResponse, CampaignUpdate
)
from common.exceptions import NotFoundError, ValidationError


class CampaignController:
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(
        self, campaign_data: CampaignCreate, user_id: UUID, org_id: UUID
    ) -> CampaignResponse:
        """Create a new campaign"""
        campaign = Campaign(
            **campaign_data.model_dump(),
            org_id=org_id,
            created_by=user_id
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return self._campaign_to_response(campaign)
    
    def list_campaigns(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        campaign_type: Optional[str] = None
    ) -> List[CampaignResponse]:
        """List campaigns with optional filters"""
        query = self.db.query(Campaign).filter(Campaign.org_id == org_id)
        
        if status:
            query = query.filter(Campaign.status == status)
        if campaign_type:
            query = query.filter(Campaign.campaign_type == campaign_type)
        
        campaigns = query.offset(skip).limit(limit).all()
        return [self._campaign_to_response(c) for c in campaigns]
    
    def get_campaign(self, campaign_id: UUID, org_id: UUID) -> CampaignResponse:
        """Get campaign by ID"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.org_id == org_id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign not found")
        
        return self._campaign_to_response(campaign)
    
    def update_campaign(
        self, campaign_id: UUID, campaign_data: CampaignUpdate, org_id: UUID
    ) -> CampaignResponse:
        """Update campaign"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.org_id == org_id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign not found")
        
        # Update fields
        for field, value in campaign_data.model_dump(exclude_unset=True).items():
            setattr(campaign, field, value)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        return self._campaign_to_response(campaign)
    
    def create_template(
        self, template_data: CampaignTemplateCreate, user_id: UUID, org_id: UUID
    ) -> CampaignTemplateResponse:
        """Create campaign template"""
        template = CampaignTemplate(
            **template_data.model_dump(),
            org_id=org_id,
            created_by=user_id
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return CampaignTemplateResponse(
            id=str(template.id),
            name=template.name,
            goal=template.goal,
            channels=template.channels,
            ctr_sensitivity=template.ctr_sensitivity,
            analysis_level=template.analysis_level,
            created_at=template.created_at
        )
    
    def list_templates(self, org_id: UUID) -> List[CampaignTemplateResponse]:
        """List campaign templates"""
        templates = self.db.query(CampaignTemplate).filter(
            CampaignTemplate.org_id == org_id
        ).all()
        
        return [
            CampaignTemplateResponse(
                id=str(t.id),
                name=t.name,
                goal=t.goal,
                channels=t.channels,
                ctr_sensitivity=t.ctr_sensitivity,
                analysis_level=t.analysis_level,
                created_at=t.created_at
            )
            for t in templates
        ]
    
    def _campaign_to_response(self, campaign: Campaign) -> CampaignResponse:
        """Convert campaign model to response"""
        reports_count = len(campaign.reports) if campaign.reports else 0
        
        return CampaignResponse(
            id=str(campaign.id),
            name=campaign.name,
            campaign_type=campaign.campaign_type,
            goal=campaign.goal,
            channel=campaign.channel,
            ctr_sensitivity=campaign.ctr_sensitivity,
            analysis_level=campaign.analysis_level,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            reports_count=reports_count
        )
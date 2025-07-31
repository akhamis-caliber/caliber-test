from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from db.models import Campaign, CampaignTemplate, User
from campaign_service.schemas import (
    CampaignCreate, CampaignTemplateCreate, CampaignStatus
)
from common.exceptions import NotFoundError, ValidationError
import uuid

class CampaignController:
    
    @staticmethod
    def create_template(
        db: Session, 
        template_data: CampaignTemplateCreate, 
        user: User
    ) -> CampaignTemplate:
        """Create a new campaign template"""
        template = CampaignTemplate(
            **template_data.model_dump(),
            user_id=user.id
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def get_user_templates(db: Session, user: User) -> List[CampaignTemplate]:
        """Get all templates for a user"""
        return db.query(CampaignTemplate)\
                .filter(CampaignTemplate.user_id == user.id)\
                .order_by(desc(CampaignTemplate.created_at))\
                .all()
    
    @staticmethod
    def get_template_by_id(db: Session, template_id: uuid.UUID, user: User) -> CampaignTemplate:
        """Get template by ID (user must own it)"""
        template = db.query(CampaignTemplate)\
                    .filter(
                        and_(
                            CampaignTemplate.id == template_id,
                            CampaignTemplate.user_id == user.id
                        )
                    ).first()
        
        if not template:
            raise NotFoundError("Campaign template")
        
        return template
    
    @staticmethod
    def create_campaign(
        db: Session, 
        campaign_data: CampaignCreate, 
        user: User
    ) -> Campaign:
        """Create a new campaign"""
        
        # If template_id is provided, get template settings
        template = None
        if campaign_data.template_id:
            template = CampaignController.get_template_by_id(
                db, campaign_data.template_id, user
            )
        
        campaign = Campaign(
            name=campaign_data.name,
            user_id=user.id,
            template_id=campaign_data.template_id,
            status=CampaignStatus.PENDING
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign
    
    @staticmethod
    def get_user_campaigns(
        db: Session, 
        user: User,
        skip: int = 0,
        limit: int = 50,
        status: Optional[CampaignStatus] = None
    ) -> tuple[List[Campaign], int]:
        """Get user campaigns with pagination"""
        
        query = db.query(Campaign).filter(Campaign.user_id == user.id)
        
        if status:
            query = query.filter(Campaign.status == status)
        
        total = query.count()
        campaigns = query.order_by(desc(Campaign.created_at))\
                        .offset(skip)\
                        .limit(limit)\
                        .all()
        
        return campaigns, total
    
    @staticmethod
    def get_campaign_by_id(db: Session, campaign_id: uuid.UUID, user: User) -> Campaign:
        """Get campaign by ID (user must own it)"""
        campaign = db.query(Campaign)\
                    .filter(
                        and_(
                            Campaign.id == campaign_id,
                            Campaign.user_id == user.id
                        )
                    ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        return campaign
    
    @staticmethod
    def update_campaign_status(
        db: Session, 
        campaign_id: uuid.UUID, 
        status: CampaignStatus,
        user: User,
        error_message: Optional[str] = None
    ) -> Campaign:
        """Update campaign status"""
        campaign = CampaignController.get_campaign_by_id(db, campaign_id, user)
        
        campaign.status = status
        if error_message:
            campaign.error_message = error_message
        
        if status == CampaignStatus.COMPLETED:
            from datetime import datetime
            campaign.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(campaign)
        return campaign
    
    @staticmethod
    def update_campaign_progress(
        db: Session,
        campaign_id: uuid.UUID,
        processed_records: int,
        total_records: Optional[int] = None,
        user: User = None
    ) -> Campaign:
        """Update campaign processing progress"""
        if user:
            campaign = CampaignController.get_campaign_by_id(db, campaign_id, user)
        else:
            # For background tasks, we might not have user context
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise NotFoundError("Campaign")
        
        campaign.processed_records = processed_records
        if total_records:
            campaign.total_records = total_records
        
        db.commit()
        db.refresh(campaign)
        return campaign
    
    @staticmethod
    def set_campaign_file_path(
        db: Session,
        campaign_id: uuid.UUID,
        file_path: str,
        user: User = None
    ) -> Campaign:
        """Set the file path for a campaign"""
        if user:
            campaign = CampaignController.get_campaign_by_id(db, campaign_id, user)
        else:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise NotFoundError("Campaign")
        
        campaign.file_path = file_path
        db.commit()
        db.refresh(campaign)
        return campaign
    
    @staticmethod
    def delete_campaign(
        db: Session,
        campaign_id: uuid.UUID,
        user: User
    ) -> bool:
        """Delete a campaign (user must own it)"""
        campaign = CampaignController.get_campaign_by_id(db, campaign_id, user)
        
        # Only allow deletion of pending or failed campaigns
        if campaign.status in [CampaignStatus.PROCESSING, CampaignStatus.COMPLETED]:
            raise ValidationError("Cannot delete campaigns that are processing or completed")
        
        db.delete(campaign)
        db.commit()
        return True
    
    @staticmethod
    def delete_template(
        db: Session,
        template_id: uuid.UUID,
        user: User
    ) -> bool:
        """Delete a campaign template (user must own it)"""
        template = CampaignController.get_template_by_id(db, template_id, user)
        
        # Check if template is being used by any campaigns
        campaigns_using_template = db.query(Campaign)\
                                    .filter(Campaign.template_id == template_id)\
                                    .count()
        
        if campaigns_using_template > 0:
            raise ValidationError("Cannot delete template that is being used by campaigns")
        
        db.delete(template)
        db.commit()
        return True 
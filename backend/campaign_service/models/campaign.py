from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from db.models import Base, Campaign as DBCampaign, ReportStatus, TemplateType

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class CampaignGoal(str, Enum):
    AWARENESS = "awareness"
    ACTION = "action"

class CampaignChannel(str, Enum):
    CTV = "ctv"
    DISPLAY = "display"
    VIDEO = "video"
    AUDIO = "audio"

class AnalysisLevel(str, Enum):
    DOMAIN = "domain"
    SUPPLY_VENDOR = "supply-vendor"

# Template model for saving campaign configurations
class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    campaign_type = Column(String(50), nullable=False)
    goal = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    ctr_sensitivity = Column(Boolean, default=True)
    analysis_level = Column(String(50), nullable=False)
    scoring_criteria = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# Use the existing Campaign model from db.models
Campaign = DBCampaign

# Pydantic models for API validation
class ScoringCriteria(BaseModel):
    criterion_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    weight: float = Field(..., ge=0.0, le=1.0)
    min_score: float = Field(0.0, ge=0.0)
    max_score: float = Field(100.0, ge=0.0)
    is_required: bool = Field(True)

class CampaignMetadata(BaseModel):
    goal: CampaignGoal = Field(..., description="Campaign goal: awareness or action")
    channel: CampaignChannel = Field(..., description="Advertising channel")
    ctr_sensitivity: bool = Field(True, description="Whether CTR is important for this campaign")
    analysis_level: AnalysisLevel = Field(..., description="Level of analysis: domain or supply vendor")

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    campaign_type: str = Field(..., min_length=1, max_length=50)
    goal: CampaignGoal
    channel: CampaignChannel
    ctr_sensitivity: bool = Field(True)
    analysis_level: AnalysisLevel
    scoring_criteria: Optional[List[ScoringCriteria]] = None
    is_public: bool = Field(False)

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    campaign_type: str
    goal: str
    channel: str
    ctr_sensitivity: bool
    analysis_level: str
    scoring_criteria: Optional[List[Dict[str, Any]]]
    is_public: bool
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    template_id: Optional[int] = None
    scoring_criteria: Optional[List[ScoringCriteria]] = None
    target_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_score: float = Field(100.0, ge=0.0)
    min_score: Optional[float] = Field(None, ge=0.0)
    # New fields for post-campaign flow
    metadata: Optional[CampaignMetadata] = None
    save_as_template: bool = Field(False)
    template_name: Optional[str] = Field(None, min_length=1, max_length=255)

    @validator('scoring_criteria')
    def validate_scoring_criteria(cls, v):
        if v is not None:
            total_weight = sum(criterion.weight for criterion in v)
            if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                raise ValueError("Total weight of scoring criteria must equal 1.0")
        return v

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[CampaignStatus] = None
    template_id: Optional[int] = None
    scoring_criteria: Optional[List[ScoringCriteria]] = None
    target_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_score: Optional[float] = Field(None, ge=0.0)
    min_score: Optional[float] = Field(None, ge=0.0)
    metadata: Optional[CampaignMetadata] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: CampaignStatus
    template_type: str
    scoring_criteria: Optional[List[Dict[str, Any]]]
    target_score: Optional[float]
    max_score: float
    min_score: float = 0.0
    total_submissions: int
    average_score: Optional[float]
    user_id: int
    organization_id: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = False
        
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle metadata mapping and scoring_criteria conversion"""
        data = {}
        for field in cls.__fields__:
            if field == 'metadata':
                # Always set metadata to None for now since we don't have metadata stored
                data[field] = None
            elif field == 'scoring_criteria':
                # Handle scoring_criteria conversion from dict to list if needed
                scoring_criteria = getattr(obj, field, None)
                if isinstance(scoring_criteria, dict):
                    # If it's a dict, check if it contains metadata fields
                    metadata_fields = ['goal', 'channel', 'ctr_sensitivity', 'analysis_level']
                    if any(field_name in scoring_criteria for field_name in metadata_fields):
                        # This is metadata, not scoring criteria
                        data[field] = None
                    else:
                        # Convert dict to list format
                        data[field] = [scoring_criteria]
                else:
                    data[field] = scoring_criteria
            else:
                data[field] = getattr(obj, field, None)
        return cls(**data)

class CampaignCreateResponse(BaseModel):
    campaign_id: int
    upload_url: str
    status: str
    message: str

class CampaignResultsResponse(BaseModel):
    campaign: CampaignResponse
    reports: List[Dict[str, Any]]
    summary: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]

# Campaign CRUD operations
class CampaignService:
    def __init__(self, db_session):
        self.db = db_session

    def create_campaign(self, campaign_data: CampaignCreate, user_id: int, organization_id: int = None) -> Campaign:
        """Create a new campaign with enhanced metadata support and template saving"""
        # Get user's primary organization if not provided
        if organization_id is None:
            from auth_service.models.user import UserService
            user_orgs = UserService.get_user_organizations(self.db, user_id)
            if user_orgs:
                organization_id = user_orgs[0].organization_id
            else:
                # Create a default organization for the user if none exists
                from db.models import Organization
                default_org = Organization(
                    name="Default Organization",
                    description="Default organization for user",
                    is_active=True
                )
                self.db.add(default_org)
                self.db.commit()
                self.db.refresh(default_org)
                organization_id = default_org.id
                
                # Add user to the organization
                from auth_service.models.user import UserService
                UserService.add_user_to_organization(self.db, user_id, organization_id)
        
        # Prepare scoring criteria
        scoring_criteria = None
        if campaign_data.scoring_criteria:
            scoring_criteria = [criteria.dict() for criteria in campaign_data.scoring_criteria]
        elif campaign_data.metadata:
            # Generate default scoring criteria based on metadata
            scoring_criteria = self._generate_default_criteria(campaign_data.metadata)
        
        # Prepare metadata
        metadata = None
        if campaign_data.metadata:
            metadata = campaign_data.metadata.dict()
        
        campaign = Campaign(
            name=campaign_data.name,
            description=campaign_data.description,
            user_id=user_id,
            organization_id=organization_id,
            template_type=campaign_data.template_id or TemplateType.CUSTOM,
            scoring_criteria=scoring_criteria,
            target_score=campaign_data.target_score,
            max_score=campaign_data.max_score,
            status=CampaignStatus.DRAFT
        )
        
        # Store metadata in scoring_criteria if not already set
        if metadata and not scoring_criteria:
            campaign.scoring_criteria = metadata
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Save as template if requested
        if campaign_data.save_as_template and campaign_data.template_name:
            self._save_campaign_as_template(campaign, campaign_data, user_id, organization_id)
        
        return campaign

    def _save_campaign_as_template(self, campaign: Campaign, campaign_data: CampaignCreate, user_id: int, organization_id: int):
        """Save campaign configuration as a reusable template"""
        template = Template(
            name=campaign_data.template_name,
            description=campaign_data.description or f"Template based on {campaign.name}",
            user_id=user_id,
            organization_id=organization_id,
            campaign_type=campaign_data.metadata.goal if campaign_data.metadata else "custom",
            goal=campaign_data.metadata.goal if campaign_data.metadata else "awareness",
            channel=campaign_data.metadata.channel if campaign_data.metadata else "display",
            ctr_sensitivity=campaign_data.metadata.ctr_sensitivity if campaign_data.metadata else True,
            analysis_level=campaign_data.metadata.analysis_level if campaign_data.metadata else "domain",
            scoring_criteria=campaign.scoring_criteria,
            is_public=False
        )
        
        self.db.add(template)
        self.db.commit()

    def create_template(self, template_data: TemplateCreate, user_id: int, organization_id: int = 1) -> Template:
        """Create a new campaign template"""
        template = Template(
            name=template_data.name,
            description=template_data.description,
            user_id=user_id,
            organization_id=organization_id,
            campaign_type=template_data.campaign_type,
            goal=template_data.goal.value,
            channel=template_data.channel.value,
            ctr_sensitivity=template_data.ctr_sensitivity,
            analysis_level=template_data.analysis_level.value,
            scoring_criteria=[criteria.dict() for criteria in template_data.scoring_criteria] if template_data.scoring_criteria else None,
            is_public=template_data.is_public
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_user_templates(self, user_id: int, include_public: bool = True) -> List[Template]:
        """Get all templates for a user, optionally including public templates"""
        query = self.db.query(Template).filter(Template.user_id == user_id)
        
        if include_public:
            query = query.union(
                self.db.query(Template).filter(Template.is_public == True)
            )
        
        return query.all()

    def get_template(self, template_id: int, user_id: int) -> Optional[Template]:
        """Get template by ID (user must own the template or it must be public)"""
        return self.db.query(Template).filter(
            (Template.id == template_id) &
            ((Template.user_id == user_id) | (Template.is_public == True))
        ).first()

    def update_template(self, template_id: int, template_data: TemplateCreate, user_id: int) -> Optional[Template]:
        """Update an existing template"""
        template = self.get_template(template_id, user_id)
        if not template or template.user_id != user_id:
            return None
        
        update_data = template_data.dict(exclude_unset=True)
        
        # Convert enum values to strings
        if 'goal' in update_data:
            update_data['goal'] = update_data['goal'].value
        if 'channel' in update_data:
            update_data['channel'] = update_data['channel'].value
        if 'analysis_level' in update_data:
            update_data['analysis_level'] = update_data['analysis_level'].value
        
        # Convert scoring criteria to JSON if provided
        if 'scoring_criteria' in update_data and update_data['scoring_criteria']:
            update_data['scoring_criteria'] = [criteria.dict() for criteria in update_data['scoring_criteria']]
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template"""
        template = self.get_template(template_id, user_id)
        if not template or template.user_id != user_id:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True

    def create_campaign_from_template(self, template_id: int, campaign_name: str, user_id: int, organization_id: int = 1) -> Optional[Campaign]:
        """Create a new campaign from an existing template"""
        template = self.get_template(template_id, user_id)
        if not template:
            return None
        
        # Create campaign metadata from template
        metadata = CampaignMetadata(
            goal=CampaignGoal(template.goal),
            channel=CampaignChannel(template.channel),
            ctr_sensitivity=template.ctr_sensitivity,
            analysis_level=AnalysisLevel(template.analysis_level)
        )
        
        campaign_data = CampaignCreate(
            name=campaign_name,
            description=f"Campaign created from template: {template.name}",
            metadata=metadata,
            scoring_criteria=template.scoring_criteria,
            target_score=None,
            max_score=100.0,
            min_score=0.0
        )
        
        return self.create_campaign(campaign_data, user_id, organization_id)

    def _generate_default_criteria(self, metadata: CampaignMetadata) -> List[Dict[str, Any]]:
        """Generate default scoring criteria based on campaign metadata"""
        base_criteria = [
            {
                "criterion_name": "Impressions",
                "description": "Total number of impressions",
                "weight": 0.2,
                "min_score": 0.0,
                "max_score": 100.0,
                "is_required": True
            },
            {
                "criterion_name": "CTR",
                "description": "Click-through rate",
                "weight": 0.3 if metadata.ctr_sensitivity else 0.2,
                "min_score": 0.0,
                "max_score": 100.0,
                "is_required": True
            },
            {
                "criterion_name": "eCPM",
                "description": "Effective cost per thousand impressions",
                "weight": 0.3,
                "min_score": 0.0,
                "max_score": 100.0,
                "is_required": True
            }
        ]
        
        # Add goal-specific criteria
        if metadata.goal == CampaignGoal.ACTION:
            base_criteria.extend([
                {
                    "criterion_name": "Conversions",
                    "description": "Total number of conversions",
                    "weight": 0.2,
                    "min_score": 0.0,
                    "max_score": 100.0,
                    "is_required": True
                },
                {
                    "criterion_name": "Conversion_Rate",
                    "description": "Conversion rate percentage",
                    "weight": 0.1,
                    "min_score": 0.0,
                    "max_score": 100.0,
                    "is_required": True
                }
            ])
        
        # Normalize weights to sum to 1.0
        total_weight = sum(criterion["weight"] for criterion in base_criteria)
        for criterion in base_criteria:
            criterion["weight"] = criterion["weight"] / total_weight
        
        return base_criteria

    def get_campaign(self, campaign_id: int, user_id: int) -> Optional[Campaign]:
        """Get campaign by ID (user must own the campaign)"""
        return self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id
        ).first()

    def get_user_campaigns(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Campaign]:
        """Get all campaigns for a user"""
        return self.db.query(Campaign).filter(
            Campaign.user_id == user_id
        ).offset(skip).limit(limit).all()

    def update_campaign(self, campaign_id: int, campaign_data: CampaignUpdate, user_id: int) -> Optional[Campaign]:
        """Update an existing campaign"""
        campaign = self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        update_data = campaign_data.dict(exclude_unset=True)
        
        # Convert scoring criteria to JSON if provided
        if 'scoring_criteria' in update_data and update_data['scoring_criteria']:
            update_data['scoring_criteria'] = [criteria.dict() for criteria in update_data['scoring_criteria']]
        
        # Convert metadata to JSON if provided
        if 'metadata' in update_data and update_data['metadata']:
            update_data['scoring_criteria'] = update_data['metadata'].dict()
            del update_data['metadata']
        
        # Convert enum to string if provided
        if 'status' in update_data:
            update_data['status'] = update_data['status'].value
        
        # Map template_id to template_type
        if 'template_id' in update_data:
            update_data['template_type'] = update_data.pop('template_id') or TemplateType.CUSTOM
        
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def delete_campaign(self, campaign_id: int, user_id: int) -> bool:
        """Delete a campaign"""
        campaign = self.get_campaign(campaign_id, user_id)
        if not campaign:
            return False
        
        self.db.delete(campaign)
        self.db.commit()
        return True

    def get_campaign_stats(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """Get campaign statistics"""
        campaign = self.get_campaign(campaign_id, user_id)
        if not campaign:
            return {}
        
        # Get report statistics
        total_reports = len(campaign.reports)
        completed_reports = len([r for r in campaign.reports if r.status == ReportStatus.COMPLETED])
        average_score = 0
        
        if completed_reports > 0:
            scores = []
            for r in campaign.reports:
                if r.status == ReportStatus.COMPLETED and r.score_data:
                    # Extract score from score_data
                    if isinstance(r.score_data, dict):
                        if 'overall_score' in r.score_data:
                            scores.append(r.score_data['overall_score'])
                        elif 'total_score' in r.score_data:
                            scores.append(r.score_data['total_score'])
                        elif 'scores' in r.score_data and isinstance(r.score_data['scores'], list):
                            # Calculate average from individual scores
                            if r.score_data['scores']:
                                scores.append(sum(r.score_data['scores']) / len(r.score_data['scores']))
            
            average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_reports": total_reports,
            "completed_reports": completed_reports,
            "pending_reports": total_reports - completed_reports,
            "average_score": round(average_score, 2),
            "target_score": campaign.target_score,
            "max_score": campaign.max_score,
            "min_score": 0.0
        }

    def get_campaign_results(self, campaign_id: int, user_id: int) -> Dict[str, Any]:
        """Get comprehensive campaign results including scoring data"""
        campaign = self.get_campaign(campaign_id, user_id)
        if not campaign:
            return {}
        
        # Get all reports for this campaign
        reports = campaign.reports
        
        # Aggregate results
        all_scores = []
        detailed_results = []
        
        for report in reports:
            if report.score_data:
                detailed_results.append(report.score_data)
                if 'scores' in report.score_data:
                    all_scores.extend(report.score_data['scores'])
        
        # Calculate summary statistics
        summary = {
            "total_reports": len(reports),
            "total_records": len(all_scores),
            "average_score": sum(all_scores) / len(all_scores) if all_scores else 0,
            "score_distribution": {
                "excellent": len([s for s in all_scores if s >= 90]),
                "good": len([s for s in all_scores if 80 <= s < 90]),
                "fair": len([s for s in all_scores if 70 <= s < 80]),
                "poor": len([s for s in all_scores if s < 70])
            }
        }
        
        # Prepare reports data with proper score extraction
        reports_data = []
        for r in reports:
            score = None
            if r.score_data and isinstance(r.score_data, dict):
                if 'overall_score' in r.score_data:
                    score = r.score_data['overall_score']
                elif 'total_score' in r.score_data:
                    score = r.score_data['total_score']
                elif 'scores' in r.score_data and isinstance(r.score_data['scores'], list):
                    if r.score_data['scores']:
                        score = sum(r.score_data['scores']) / len(r.score_data['scores'])
            
            reports_data.append({
                "id": r.id, 
                "filename": r.filename, 
                "status": r.status, 
                "score": score
            })
        
        return {
            "campaign": campaign,
            "reports": reports_data,
            "summary": summary,
            "detailed_results": detailed_results
        }

    def update_campaign_status(self, campaign_id: int, user_id: int, new_status: CampaignStatus) -> bool:
        """Update campaign status"""
        campaign = self.get_campaign(campaign_id, user_id)
        if not campaign:
            return False
        
        campaign.status = new_status
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True 
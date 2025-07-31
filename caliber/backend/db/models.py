from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, DECIMAL, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import BaseModel

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization")

class User(BaseModel):
    __tablename__ = "users"
    
    firebase_uid = Column(String(128), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    campaigns = relationship("Campaign", back_populates="user")
    templates = relationship("CampaignTemplate", back_populates="user")
    file_uploads = relationship("FileUpload", back_populates="user")

class CampaignTemplate(BaseModel):
    __tablename__ = "campaign_templates"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # 'trade_desk', 'pulsepoint'
    goal = Column(String(50), nullable=False)  # 'awareness', 'action'
    channel = Column(String(50), nullable=False)  # 'ctv', 'display', 'video', 'audio'
    ctr_sensitivity = Column(Boolean, nullable=False)
    analysis_level = Column(String(50), nullable=False)  # 'domain', 'supply_vendor'
    
    # Relationships
    user = relationship("User", back_populates="templates")
    campaigns = relationship("Campaign", back_populates="template")

class Campaign(BaseModel):
    __tablename__ = "campaigns"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("campaign_templates.id"))
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    file_path = Column(String(500))
    results_path = Column(String(500))
    total_records = Column(Integer)
    processed_records = Column(Integer)
    error_message = Column(Text)
    completed_at = Column(DateTime)
    
    # Scoring configuration
    scoring_platform = Column(String(50), nullable=True)  # 'trade_desk', 'pulsepoint'
    scoring_config_snapshot = Column(JSON, nullable=True)  # Config used for scoring
    
    # Data processing stats
    data_quality_report = Column(JSON, nullable=True)  # Validation results
    column_mapping_used = Column(JSON, nullable=True)  # How columns were mapped
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    template = relationship("CampaignTemplate", back_populates="campaigns")
    results = relationship("ScoringResult", back_populates="campaign")
    insights = relationship("AIInsight", back_populates="campaign")
    file_uploads = relationship("FileUpload", back_populates="campaign")

class ScoringResult(BaseModel):
    __tablename__ = "scoring_results"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    
    # Original data
    domain = Column(String(255), nullable=False, index=True)
    impressions = Column(Integer, nullable=False)
    ctr = Column(DECIMAL(10, 6), nullable=False)
    conversions = Column(Integer, nullable=False)
    total_spend = Column(DECIMAL(12, 2), nullable=False)
    
    # Additional platform-specific metrics (stored as JSON for flexibility)
    raw_metrics = Column(JSON, nullable=True)  # Original metrics from file
    normalized_metrics = Column(JSON, nullable=True)  # Normalized 0-100 values
    
    # Calculated metrics
    cpm = Column(DECIMAL(10, 2), nullable=True)
    conversion_rate = Column(DECIMAL(10, 6), nullable=True)
    cost_per_conversion = Column(DECIMAL(10, 2), nullable=True)
    
    # Scoring details
    score = Column(Integer, nullable=False)  # Final 0-100 score
    score_breakdown = Column(JSON, nullable=True)  # Component scores
    normalization_stats = Column(JSON, nullable=True)  # Min/max values used
    scoring_config_used = Column(JSON, nullable=True)  # Config snapshot
    
    # Quality assessment
    status = Column(String(20), nullable=False, index=True)  # 'good', 'moderate', 'poor'
    percentile_rank = Column(Integer, nullable=True)
    quality_flags = Column(JSON, nullable=True)  # Any quality issues found
    
    # Relationships
    campaign = relationship("Campaign", back_populates="results")

class AIInsight(BaseModel):
    __tablename__ = "ai_insights"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    insight_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="insights")

class FileUpload(BaseModel):
    __tablename__ = "file_uploads"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="uploaded")  # 'uploaded', 'assigned', 'processed'
    
    # Relationships
    user = relationship("User", back_populates="file_uploads")
    campaign = relationship("Campaign", back_populates="file_uploads")


from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Enum, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from typing import Optional, Dict, Any

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ReportStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TemplateType(str, enum.Enum):
    CUSTOMER_SCORING = "customer_scoring"
    LEAD_SCORING = "lead_scoring"
    PRODUCT_SCORING = "product_scoring"
    EMPLOYEE_SCORING = "employee_scoring"
    CUSTOM = "custom"


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # For password authentication
    organization = Column(String(255), nullable=True)  # Legacy field for backward compatibility
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="user", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_firebase_uid', 'firebase_uid'),
        Index('idx_users_created_at', 'created_at'),
    )


class Organization(Base):
    """Organization model for multi-tenancy support"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_organizations_name', 'name'),
        Index('idx_organizations_created_at', 'created_at'),
    )


class UserOrganization(Base):
    """Many-to-many relationship between users and organizations with roles"""
    __tablename__ = "user_organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_organizations")
    organization = relationship("Organization", back_populates="user_organizations")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_organizations_user_id', 'user_id'),
        Index('idx_user_organizations_org_id', 'organization_id'),
        Index('idx_user_organizations_role', 'role'),
        Index('idx_user_organizations_unique', 'user_id', 'organization_id', unique=True),
    )


class Campaign(Base):
    """Campaign model for scoring campaigns"""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    template_type = Column(Enum(TemplateType), default=TemplateType.CUSTOM, nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    scoring_criteria = Column(JSON, nullable=True)  # Store scoring criteria as JSON
    target_score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0, nullable=False)
    total_submissions = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    organization = relationship("Organization", back_populates="campaigns")
    reports = relationship("Report", back_populates="campaign", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_campaigns_user_id', 'user_id'),
        Index('idx_campaigns_org_id', 'organization_id'),
        Index('idx_campaigns_status', 'status'),
        Index('idx_campaigns_template_type', 'template_type'),
        Index('idx_campaigns_created_at', 'created_at'),
        Index('idx_campaigns_name_org', 'name', 'organization_id'),
    )
    
    @property
    def min_score(self) -> float:
        """Computed property for min_score (always 0.0)"""
        return 0.0

    @property
    def campaign_metadata(self) -> Optional[Dict[str, Any]]:
        """Extract metadata from scoring_criteria if it contains metadata fields"""
        if not self.scoring_criteria:
            return None
        
        # Check if scoring_criteria contains metadata fields
        if isinstance(self.scoring_criteria, dict):
            metadata_fields = ['goal', 'channel', 'ctr_sensitivity', 'analysis_level']
            if any(field in self.scoring_criteria for field in metadata_fields):
                return self.scoring_criteria
        
        # If scoring_criteria is a list, check if any item contains metadata
        elif isinstance(self.scoring_criteria, list):
            for item in self.scoring_criteria:
                if isinstance(item, dict) and 'goal' in item:
                    return item
        
        return None

    def get_campaign_metadata_dict(self) -> Optional[Dict[str, Any]]:
        """Get campaign metadata as dictionary without naming conflicts"""
        if not self.scoring_criteria:
            return None
        
        # Check if scoring_criteria contains metadata fields
        if isinstance(self.scoring_criteria, dict):
            metadata_fields = ['goal', 'channel', 'ctr_sensitivity', 'analysis_level']
            if any(field in self.scoring_criteria for field in metadata_fields):
                return self.scoring_criteria
        
        # If scoring_criteria is a list, check if any item contains metadata
        elif isinstance(self.scoring_criteria, list):
            for item in self.scoring_criteria:
                if isinstance(item, dict) and 'goal' in item:
                    return item
        
        return None


class Report(Base):
    """Report model for storing file uploads and processing results"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Path to uploaded file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    file_type = Column(String(50), nullable=True)  # File extension
    status = Column(Enum(ReportStatus), default=ReportStatus.PROCESSING, nullable=False)
    report_type = Column(String(50), default="scoring_summary", nullable=False)
    task_id = Column(String(255), nullable=True)  # Celery task ID for processing
    score_data = Column(JSON, nullable=True)  # Store scoring results as JSON
    report_metadata = Column(JSON, nullable=True)  # Additional metadata
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="reports")
    user = relationship("User", back_populates="reports")
    scoring_results = relationship("ScoringResult", back_populates="report", cascade="all, delete-orphan")
    scoring_jobs = relationship("ScoringJob", back_populates="report", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_reports_campaign_id', 'campaign_id'),
        Index('idx_reports_user_id', 'user_id'),
        Index('idx_reports_status', 'status'),
        Index('idx_reports_created_at', 'created_at'),
        Index('idx_reports_filename', 'filename'),
        Index('idx_reports_campaign_status', 'campaign_id', 'status'),
    )


class ScoringResult(Base):
    """Detailed scoring results for individual metrics"""
    __tablename__ = "scoring_results"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=True)  # Raw metric value
    score = Column(Float, nullable=False)  # Calculated score
    weight = Column(Float, default=1.0, nullable=False)  # Weight for this metric
    weighted_score = Column(Float, nullable=True)  # score * weight
    explanation = Column(Text, nullable=True)  # AI-generated explanation
    metric_metadata = Column(JSON, nullable=True)  # Additional metric metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    report = relationship("Report", back_populates="scoring_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_scoring_results_report_id', 'report_id'),
        Index('idx_scoring_results_metric_name', 'metric_name'),
        Index('idx_scoring_results_score', 'score'),
        Index('idx_scoring_results_created_at', 'created_at'),
        Index('idx_scoring_results_report_metric', 'report_id', 'metric_name'),
    )


class ScoringJob(Base):
    """Scoring job model for tracking background scoring tasks"""
    __tablename__ = "scoring_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(255), nullable=True)  # Celery task ID
    status = Column(Enum(ReportStatus), default=ReportStatus.QUEUED, nullable=False)
    job_type = Column(String(50), default="standard", nullable=False)  # standard, batch, comparison
    config = Column(JSON, nullable=True)  # Scoring configuration
    progress = Column(Float, default=0.0, nullable=False)  # Progress percentage
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    report = relationship("Report", back_populates="scoring_jobs")
    campaign = relationship("Campaign")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_scoring_jobs_report_id', 'report_id'),
        Index('idx_scoring_jobs_campaign_id', 'campaign_id'),
        Index('idx_scoring_jobs_status', 'status'),
        Index('idx_scoring_jobs_created_at', 'created_at'),
    )


class ScoringMetrics(Base):
    """Scoring metrics configuration and results"""
    __tablename__ = "scoring_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # continuous, categorical, binary
    description = Column(Text, nullable=True)
    weight = Column(Float, default=1.0, nullable=False)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    normalization_method = Column(String(50), nullable=True)  # zscore, minmax, robust
    outlier_method = Column(String(50), nullable=True)  # iqr, zscore, isolation_forest
    outlier_action = Column(String(50), nullable=True)  # mark, remove, cap
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    campaign = relationship("Campaign")
    
    # Indexes
    __table_args__ = (
        Index('idx_scoring_metrics_campaign_id', 'campaign_id'),
        Index('idx_scoring_metrics_name', 'metric_name'),
        Index('idx_scoring_metrics_active', 'is_active'),
    )


class ScoringHistory(Base):
    """Historical scoring results for analysis and comparison"""
    __tablename__ = "scoring_history"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    scoring_job_id = Column(Integer, ForeignKey("scoring_jobs.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), default="1.0", nullable=False)
    config_snapshot = Column(JSON, nullable=True)  # Configuration used for this scoring
    results_summary = Column(JSON, nullable=True)  # Summary statistics
    performance_metrics = Column(JSON, nullable=True)  # Processing time, accuracy, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    campaign = relationship("Campaign")
    report = relationship("Report")
    scoring_job = relationship("ScoringJob")
    
    # Indexes
    __table_args__ = (
        Index('idx_scoring_history_campaign_id', 'campaign_id'),
        Index('idx_scoring_history_report_id', 'report_id'),
        Index('idx_scoring_history_created_at', 'created_at'),
    )


class AuditLog(Base):
    """Audit log for tracking important system events"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(50), nullable=False)  # USER, CAMPAIGN, REPORT, etc.
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # Additional details about the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(String(500), nullable=True)  # User agent string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    organization = relationship("Organization")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_org_id', 'organization_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
    )


class SystemConfig(Base):
    """System configuration settings"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_configs_key', 'key'),
        Index('idx_system_configs_active', 'is_active'),
    )


# Helper functions for common operations
def get_user_by_email(db, email: str):
    """Get user by email address"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_firebase_uid(db, firebase_uid: str):
    """Get user by Firebase UID"""
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def get_user_organizations(db, user_id: int):
    """Get all organizations for a user"""
    return db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.is_active == True
    ).all()


def get_campaign_reports(db, campaign_id: int):
    """Get all reports for a campaign"""
    return db.query(Report).filter(Report.campaign_id == campaign_id).all()


def get_report_scoring_results(db, report_id: int):
    """Get all scoring results for a report"""
    return db.query(ScoringResult).filter(ScoringResult.report_id == report_id).all()


def create_audit_log(db, user_id: int = None, organization_id: int = None, action: str = None, 
                    resource_type: str = None, resource_id: int = None, details: dict = None,
                    ip_address: str = None, user_agent: str = None):
    """Create an audit log entry"""
    audit_log = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()
    return audit_log 
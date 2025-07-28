"""
Database utilities and helper functions for the Caliber application.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from db.models import (
    User, Organization, UserOrganization, Campaign, Report, 
    ScoringResult, AuditLog, SystemConfig, UserRole, CampaignStatus, ReportStatus
)


# User operations
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address"""
    return db.query(User).filter(User.email == email, User.is_active == True).first()


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    """Get user by Firebase UID"""
    return db.query(User).filter(User.firebase_uid == firebase_uid, User.is_active == True).first()


def create_user(db: Session, email: str, full_name: str, firebase_uid: str = None) -> User:
    """Create a new user"""
    user = User(
        email=email,
        full_name=full_name,
        firebase_uid=firebase_uid,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user information"""
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user"""
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


# Organization operations
def get_organization_by_id(db: Session, org_id: int) -> Optional[Organization]:
    """Get organization by ID"""
    return db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()


def create_organization(db: Session, name: str, description: str = None) -> Organization:
    """Create a new organization"""
    org = Organization(
        name=name,
        description=description,
        is_active=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_user_organizations(db: Session, user_id: int) -> List[UserOrganization]:
    """Get all organizations for a user"""
    return db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.is_active == True
    ).all()


def add_user_to_organization(db: Session, user_id: int, org_id: int, role: UserRole = UserRole.USER) -> UserOrganization:
    """Add a user to an organization"""
    # Check if user is already in organization
    existing = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.organization_id == org_id
    ).first()
    
    if existing:
        existing.role = role
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    user_org = UserOrganization(
        user_id=user_id,
        organization_id=org_id,
        role=role,
        is_active=True
    )
    db.add(user_org)
    db.commit()
    db.refresh(user_org)
    return user_org


def remove_user_from_organization(db: Session, user_id: int, org_id: int) -> bool:
    """Remove a user from an organization"""
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.organization_id == org_id
    ).first()
    
    if user_org:
        user_org.is_active = False
        user_org.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


# Campaign operations
def get_campaign_by_id(db: Session, campaign_id: int) -> Optional[Campaign]:
    """Get campaign by ID"""
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


def get_user_campaigns(db: Session, user_id: int, org_id: int = None, status: CampaignStatus = None) -> List[Campaign]:
    """Get campaigns for a user"""
    query = db.query(Campaign).filter(Campaign.user_id == user_id)
    
    if org_id:
        query = query.filter(Campaign.organization_id == org_id)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    return query.order_by(desc(Campaign.created_at)).all()


def create_campaign(db: Session, name: str, user_id: int, org_id: int, **kwargs) -> Campaign:
    """Create a new campaign"""
    campaign = Campaign(
        name=name,
        user_id=user_id,
        organization_id=org_id,
        **kwargs
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def update_campaign(db: Session, campaign_id: int, **kwargs) -> Optional[Campaign]:
    """Update campaign information"""
    campaign = get_campaign_by_id(db, campaign_id)
    if campaign:
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)
    return campaign


def delete_campaign(db: Session, campaign_id: int) -> bool:
    """Delete a campaign (soft delete by setting status to archived)"""
    campaign = get_campaign_by_id(db, campaign_id)
    if campaign:
        campaign.status = CampaignStatus.ARCHIVED
        campaign.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


# Report operations
def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
    """Get report by ID"""
    return db.query(Report).filter(Report.id == report_id).first()


def get_campaign_reports(db: Session, campaign_id: int, status: ReportStatus = None) -> List[Report]:
    """Get all reports for a campaign"""
    query = db.query(Report).filter(Report.campaign_id == campaign_id)
    
    if status:
        query = query.filter(Report.status == status)
    
    return query.order_by(desc(Report.created_at)).all()


def create_report(db: Session, campaign_id: int, user_id: int, title: str, filename: str, **kwargs) -> Report:
    """Create a new report"""
    report = Report(
        campaign_id=campaign_id,
        user_id=user_id,
        title=title,
        filename=filename,
        **kwargs
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report_status(db: Session, report_id: int, status: ReportStatus, **kwargs) -> Optional[Report]:
    """Update report status and other fields"""
    report = get_report_by_id(db, report_id)
    if report:
        report.status = status
        report.updated_at = datetime.utcnow()
        
        if status == ReportStatus.COMPLETED:
            report.processed_at = datetime.utcnow()
        
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        db.commit()
        db.refresh(report)
    return report


# Scoring result operations
def get_report_scoring_results(db: Session, report_id: int) -> List[ScoringResult]:
    """Get all scoring results for a report"""
    return db.query(ScoringResult).filter(ScoringResult.report_id == report_id).all()


def create_scoring_result(db: Session, report_id: int, metric_name: str, score: float, **kwargs) -> ScoringResult:
    """Create a new scoring result"""
    scoring_result = ScoringResult(
        report_id=report_id,
        metric_name=metric_name,
        score=score,
        **kwargs
    )
    db.add(scoring_result)
    db.commit()
    db.refresh(scoring_result)
    return scoring_result


def bulk_create_scoring_results(db: Session, report_id: int, results: List[Dict[str, Any]]) -> List[ScoringResult]:
    """Bulk create scoring results"""
    scoring_results = []
    for result_data in results:
        result_data['report_id'] = report_id
        scoring_result = ScoringResult(**result_data)
        scoring_results.append(scoring_result)
    
    db.add_all(scoring_results)
    db.commit()
    
    for result in scoring_results:
        db.refresh(result)
    
    return scoring_results


# Audit log operations
def create_audit_log(db: Session, user_id: int = None, organization_id: int = None, 
                    action: str = None, resource_type: str = None, resource_id: int = None,
                    details: dict = None, ip_address: str = None, user_agent: str = None) -> AuditLog:
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
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(db: Session, user_id: int = None, organization_id: int = None, 
                  action: str = None, resource_type: str = None, 
                  limit: int = 100, offset: int = 0) -> List[AuditLog]:
    """Get audit logs with filters"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()


# System configuration operations
def get_system_config(db: Session, key: str) -> Optional[str]:
    """Get system configuration value by key"""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == key,
        SystemConfig.is_active == True
    ).first()
    return config.value if config else None


def set_system_config(db: Session, key: str, value: str, description: str = None) -> SystemConfig:
    """Set system configuration value"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
        if description:
            config.description = description
    else:
        config = SystemConfig(
            key=key,
            value=value,
            description=description,
            is_active=True
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    return config


# Statistics and analytics
def get_campaign_statistics(db: Session, campaign_id: int) -> Dict[str, Any]:
    """Get statistics for a campaign"""
    campaign = get_campaign_by_id(db, campaign_id)
    if not campaign:
        return {}
    
    reports = get_campaign_reports(db, campaign_id)
    completed_reports = [r for r in reports if r.status == ReportStatus.COMPLETED]
    
    total_reports = len(reports)
    completed_count = len(completed_reports)
    failed_count = len([r for r in reports if r.status == ReportStatus.FAILED])
    
    # Calculate average scores
    total_score = 0
    score_count = 0
    
    for report in completed_reports:
        if report.score_data and 'overall_score' in report.score_data:
            total_score += report.score_data['overall_score']
            score_count += 1
    
    avg_score = total_score / score_count if score_count > 0 else 0
    
    return {
        'total_reports': total_reports,
        'completed_reports': completed_count,
        'failed_reports': failed_count,
        'processing_reports': total_reports - completed_count - failed_count,
        'average_score': round(avg_score, 2),
        'completion_rate': round((completed_count / total_reports * 100), 2) if total_reports > 0 else 0
    }


def get_user_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """Get statistics for a user"""
    campaigns = get_user_campaigns(db, user_id)
    reports = db.query(Report).filter(Report.user_id == user_id).all()
    
    active_campaigns = len([c for c in campaigns if c.status == CampaignStatus.ACTIVE])
    total_reports = len(reports)
    completed_reports = len([r for r in reports if r.status == ReportStatus.COMPLETED])
    
    return {
        'total_campaigns': len(campaigns),
        'active_campaigns': active_campaigns,
        'total_reports': total_reports,
        'completed_reports': completed_reports,
        'success_rate': round((completed_reports / total_reports * 100), 2) if total_reports > 0 else 0
    } 
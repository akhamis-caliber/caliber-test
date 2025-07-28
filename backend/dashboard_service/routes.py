"""
Dashboard routes for providing analytics and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta

from config.database import get_db
from auth_service.middleware import get_current_user
from auth_service.models.user import User
from db.models import Campaign, Report, ScoringResult, CampaignStatus, ReportStatus
from db.utils import get_user_campaigns, get_campaign_statistics, get_user_statistics

dashboard_router = APIRouter()


@dashboard_router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics"""
    try:
        # Get user statistics
        user_stats = get_user_statistics(db, current_user.id)
        
        # Get recent campaigns
        campaigns = get_user_campaigns(db, current_user.id)
        recent_campaigns = sorted(campaigns, key=lambda x: x.created_at, reverse=True)[:5]
        
        # Get recent reports
        recent_reports = db.query(Report).filter(
            Report.user_id == current_user.id
        ).order_by(Report.created_at.desc()).limit(10).all()
        
        # Calculate scoring trends
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.user_id == current_user.id
        ).all()
        
        avg_score = 0
        if scoring_results:
            avg_score = sum(r.score for r in scoring_results) / len(scoring_results)
        
        return {
            "user_stats": user_stats,
            "recent_campaigns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "created_at": c.created_at,
                    "total_submissions": c.total_submissions,
                    "average_score": c.average_score
                }
                for c in recent_campaigns
            ],
            "recent_reports": [
                {
                    "id": r.id,
                    "title": r.title,
                    "status": r.status.value,
                    "created_at": r.created_at,
                    "filename": r.filename
                }
                for r in recent_reports
            ],
            "scoring_insights": {
                "average_score": round(avg_score, 2),
                "total_scoring_results": len(scoring_results),
                "top_performing_campaigns": []
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard stats: {str(e)}"
        )


@dashboard_router.get("/activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent user activity"""
    try:
        # Get recent reports
        recent_reports = db.query(Report).filter(
            Report.user_id == current_user.id
        ).order_by(Report.created_at.desc()).limit(20).all()
        
        # Get recent campaigns
        recent_campaigns = db.query(Campaign).filter(
            Campaign.user_id == current_user.id
        ).order_by(Campaign.created_at.desc()).limit(10).all()
        
        activities = []
        
        # Add report activities
        for report in recent_reports:
            activities.append({
                "type": "report",
                "id": report.id,
                "title": f"Report '{report.title}' {report.status.value}",
                "timestamp": report.created_at,
                "status": report.status.value
            })
        
        # Add campaign activities
        for campaign in recent_campaigns:
            activities.append({
                "type": "campaign",
                "id": campaign.id,
                "title": f"Campaign '{campaign.name}' created",
                "timestamp": campaign.created_at,
                "status": campaign.status.value
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "activities": activities[:20]  # Return top 20 activities
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent activity: {str(e)}"
        )


@dashboard_router.get("/trends")
async def get_scoring_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scoring trends over time"""
    try:
        # Get scoring results from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.user_id == current_user.id,
            ScoringResult.created_at >= thirty_days_ago
        ).all()
        
        # Group by date
        daily_scores = {}
        for result in scoring_results:
            date_key = result.created_at.date().isoformat()
            if date_key not in daily_scores:
                daily_scores[date_key] = []
            daily_scores[date_key].append(result.score)
        
        # Calculate daily averages
        trends = []
        for date, scores in sorted(daily_scores.items()):
            trends.append({
                "date": date,
                "average_score": round(sum(scores) / len(scores), 2),
                "count": len(scores)
            })
        
        return {
            "trends": trends,
            "period": "30_days"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring trends: {str(e)}"
        )


@dashboard_router.get("/quick-stats")
async def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quick statistics for dashboard widgets"""
    try:
        # Count active campaigns
        active_campaigns = db.query(Campaign).filter(
            Campaign.user_id == current_user.id,
            Campaign.status == CampaignStatus.ACTIVE
        ).count()
        
        # Count completed reports this month
        this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_reports = db.query(Report).filter(
            Report.user_id == current_user.id,
            Report.status == ReportStatus.COMPLETED,
            Report.created_at >= this_month
        ).count()
        
        # Average score this month
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.user_id == current_user.id,
            ScoringResult.created_at >= this_month
        ).all()
        
        avg_score = 0
        if scoring_results:
            avg_score = sum(r.score for r in scoring_results) / len(scoring_results)
        
        # Total reports processed
        total_reports = db.query(Report).filter(
            Report.user_id == current_user.id
        ).count()
        
        return {
            "active_campaigns": active_campaigns,
            "completed_reports_this_month": completed_reports,
            "average_score_this_month": round(avg_score, 2),
            "total_reports": total_reports
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quick stats: {str(e)}"
        ) 
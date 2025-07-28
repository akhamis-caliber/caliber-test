from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import os

from config.database import get_db
from auth_service.middleware import get_current_user
from auth_service.models.user import User
from campaign_service.models.campaign import (
    CampaignService,
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignCreateResponse, CampaignResultsResponse,
    CampaignStatus, CampaignGoal, CampaignChannel, AnalysisLevel,
    TemplateCreate, TemplateResponse
)
from scoring_service import ScoringEngine
from analytics_service.analytics import CampaignAnalytics
from db.models import Report, ScoringJob, ScoringResult, ScoringHistory, ReportStatus

router = APIRouter(tags=["campaigns"])

# Campaign routes
@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[CampaignStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all campaigns for the current user"""
    try:
        service = CampaignService(db)
        campaigns = service.get_user_campaigns(current_user.id, skip=skip, limit=limit)
        
        # Filter by status if provided
        if status:
            campaigns = [c for c in campaigns if c.status == status.value]
        
        # Convert SQLAlchemy objects to Pydantic models
        campaign_responses = []
        for campaign in campaigns:
            campaign_response = CampaignResponse.from_orm(campaign)
            campaign_responses.append(campaign_response)
        
        return campaign_responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaigns: {str(e)}"
        )

@router.post("/", response_model=CampaignCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign and return upload URL for post-campaign flow"""
    try:
        service = CampaignService(db)
        campaign = service.create_campaign(campaign_data, current_user.id, organization_id=None)
        
        # Return campaign_id and upload URL for seamless flow
        return CampaignCreateResponse(
            campaign_id=campaign.id,
            upload_url=f"/upload?campaign_id={campaign.id}",
            status="created",
            message="Campaign created successfully. Please upload your dataset."
        )
    except ValueError as e:
        print(f"Campaign creation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Campaign creation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific campaign by ID"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign: {str(e)}"
        )

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing campaign"""
    try:
        service = CampaignService(db)
        campaign = service.update_campaign(campaign_id, campaign_data, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return campaign
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a campaign"""
    try:
        service = CampaignService(db)
        success = service.delete_campaign(campaign_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )

@router.get("/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign statistics"""
    try:
        service = CampaignService(db)
        stats = service.get_campaign_stats(campaign_id, current_user.id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign stats: {str(e)}"
        )

@router.get("/{campaign_id}/results", response_model=CampaignResultsResponse)
async def get_campaign_results(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive campaign results including scoring data"""
    try:
        service = CampaignService(db)
        results = service.get_campaign_results(campaign_id, current_user.id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignResultsResponse(**results)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign results: {str(e)}"
        )

@router.put("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: int,
    status_data: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign status"""
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )
        
        try:
            campaign_status = CampaignStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in CampaignStatus]}"
            )
        
        service = CampaignService(db)
        success = service.update_campaign_status(campaign_id, current_user.id, campaign_status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return {"message": f"Campaign status updated to {new_status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign status: {str(e)}"
        )

# Utility routes
@router.get("/statuses/")
async def get_campaign_statuses():
    """Get available campaign statuses"""
    return [
        {"value": status.value, "label": status.value.title()}
        for status in CampaignStatus
    ]

@router.get("/goals/")
async def get_campaign_goals():
    """Get available campaign goals"""
    return [
        {"value": goal.value, "label": goal.value.title()}
        for goal in CampaignGoal
    ]

@router.get("/channels/")
async def get_campaign_channels():
    """Get available campaign channels"""
    return [
        {"value": channel.value, "label": channel.value.upper()}
        for channel in CampaignChannel
    ]

@router.get("/analysis-levels/")
async def get_analysis_levels():
    """Get available analysis levels"""
    return [
        {"value": level.value, "label": level.value.replace("-", " ").title()}
        for level in AnalysisLevel
    ]

TEMPLATES = [
    {
        "id": 1,
        "name": "Marketing Campaign",
        "description": "Standard template for marketing campaigns with focus on engagement and conversion",
        "category": "Marketing",
        "default_criteria": [
            {"criterion_name": "Engagement Rate", "weight": 0.3, "min_score": 0, "max_score": 100},
            {"criterion_name": "Conversion Rate", "weight": 0.4, "min_score": 0, "max_score": 100},
            {"criterion_name": "Brand Awareness", "weight": 0.3, "min_score": 0, "max_score": 100}
        ]
    },
    {
        "id": 2,
        "name": "Sales Performance",
        "description": "Template optimized for sales team performance evaluation",
        "category": "Sales",
        "default_criteria": [
            {"criterion_name": "Revenue Generated", "weight": 0.5, "min_score": 0, "max_score": 100},
            {"criterion_name": "Lead Quality", "weight": 0.3, "min_score": 0, "max_score": 100},
            {"criterion_name": "Customer Satisfaction", "weight": 0.2, "min_score": 0, "max_score": 100}
        ]
    },
    {
        "id": 3,
        "name": "Content Quality",
        "description": "Template for evaluating content quality and effectiveness",
        "category": "Content",
        "default_criteria": [
            {"criterion_name": "Content Relevance", "weight": 0.25, "min_score": 0, "max_score": 100},
            {"criterion_name": "Readability", "weight": 0.25, "min_score": 0, "max_score": 100},
            {"criterion_name": "SEO Optimization", "weight": 0.25, "min_score": 0, "max_score": 100},
            {"criterion_name": "User Engagement", "weight": 0.25, "min_score": 0, "max_score": 100}
        ]
    }
]

@router.get("/templates")
async def get_templates():
    """Get all available campaign templates"""
    return TEMPLATES

# Template management endpoints
@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign template"""
    try:
        service = CampaignService(db)
        template = service.create_template(template_data, current_user.id)
        return TemplateResponse.from_orm(template)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )

@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    include_public: bool = Query(True, description="Include public templates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all templates for the current user"""
    try:
        service = CampaignService(db)
        templates = service.get_user_templates(current_user.id, include_public)
        return [TemplateResponse.from_orm(template) for template in templates]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID"""
    try:
        service = CampaignService(db)
        template = service.get_template(template_id, current_user.id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return TemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template: {str(e)}"
        )

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing template"""
    try:
        service = CampaignService(db)
        template = service.update_template(template_id, template_data, current_user.id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return TemplateResponse.from_orm(template)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    try:
        service = CampaignService(db)
        success = service.delete_template(template_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )

@router.post("/templates/{template_id}/create-campaign", response_model=CampaignCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign_from_template(
    template_id: int,
    campaign_name: str = Query(..., description="Name for the new campaign"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign from an existing template"""
    try:
        service = CampaignService(db)
        campaign = service.create_campaign_from_template(template_id, campaign_name, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return CampaignCreateResponse(
            campaign_id=campaign.id,
            upload_url=f"/upload?campaign_id={campaign.id}",
            status="created",
            message="Campaign created successfully from template. Please upload your dataset."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign from template: {str(e)}"
        )

# Scoring-related endpoints
@router.post("/{campaign_id}/score-all-reports")
async def score_all_campaign_reports(
    campaign_id: int,
    config: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score all reports for a specific campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get all reports for this campaign
        reports = db.query(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id,
            Report.status.in_([ReportStatus.COMPLETED, ReportStatus.PROCESSING])
        ).all()
        
        if not reports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reports found for this campaign"
            )
        
        results = []
        scoring_engine = ScoringEngine()
        
        for report in reports:
            try:
                # Read the report file
                df = pd.read_csv(report.file_path)
                
                # Prepare scoring configuration
                scoring_config = config or {}
                if campaign.scoring_criteria:
                    scoring_config["scoring_criteria"] = campaign.scoring_criteria
                
                # Calculate scores
                scoring_results = scoring_engine.calculate_scores(
                    df=df,
                    campaign_id=campaign_id,
                    config=scoring_config
                )
                
                # Update report with new scores
                report.score_data = scoring_results
                report.processed_at = datetime.utcnow()
                
                # Save individual scoring results
                for metric_name, metric_data in scoring_results.get("metrics", {}).items():
                    scoring_result = ScoringResult(
                        report_id=report.id,
                        metric_name=metric_name,
                        metric_value=metric_data.get("raw_value"),
                        score=metric_data.get("score", 0.0),
                        weight=metric_data.get("weight", 1.0),
                        weighted_score=metric_data.get("weighted_score", 0.0),
                        explanation=metric_data.get("explanation"),
                        metric_metadata=metric_data.get("metadata", {})
                    )
                    db.add(scoring_result)
                
                results.append({
                    "report_id": report.id,
                    "filename": report.filename,
                    "status": "completed",
                    "total_score": scoring_results.get("total_score", 0.0)
                })
                
            except Exception as e:
                results.append({
                    "report_id": report.id,
                    "filename": report.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        db.commit()
        
        return {
            "campaign_id": campaign_id,
            "total_reports": len(reports),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score campaign reports: {str(e)}"
        )

@router.get("/{campaign_id}/scoring-analytics")
async def get_campaign_scoring_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive scoring analytics for a campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get all scoring results for this campaign
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id
        ).all()
        
        if not scoring_results:
            return {
                "campaign_id": campaign_id,
                "total_reports": 0,
                "total_metrics": 0,
                "analytics": {}
            }
        
        # Calculate analytics
        metrics_data = {}
        for result in scoring_results:
            if result.metric_name not in metrics_data:
                metrics_data[result.metric_name] = {
                    "scores": [],
                    "weights": [],
                    "reports_count": 0
                }
            
            metrics_data[result.metric_name]["scores"].append(result.score)
            metrics_data[result.metric_name]["weights"].append(result.weight)
            metrics_data[result.metric_name]["reports_count"] += 1
        
        # Calculate statistics for each metric
        analytics = {}
        for metric_name, data in metrics_data.items():
            scores = data["scores"]
            weights = data["weights"]
            
            analytics[metric_name] = {
                "total_reports": data["reports_count"],
                "average_score": sum(scores) / len(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "average_weight": sum(weights) / len(weights) if weights else 0,
                "score_distribution": {
                    "excellent": len([s for s in scores if s >= 80]),
                    "good": len([s for s in scores if 60 <= s < 80]),
                    "average": len([s for s in scores if 40 <= s < 60]),
                    "poor": len([s for s in scores if s < 40])
                }
            }
        
        # Get unique reports count
        unique_reports = db.query(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id
        ).count()
        
        return {
            "campaign_id": campaign_id,
            "total_reports": unique_reports,
            "total_metrics": len(analytics),
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring analytics: {str(e)}"
        )

@router.get("/{campaign_id}/scoring-performance")
async def get_campaign_scoring_performance(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scoring performance metrics for a campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get scoring history
        history = db.query(ScoringHistory).filter(
            ScoringHistory.campaign_id == campaign_id
        ).order_by(ScoringHistory.created_at.desc()).limit(10).all()
        
        # Get scoring jobs performance
        jobs = db.query(ScoringJob).filter(
            ScoringJob.campaign_id == campaign_id,
            ScoringJob.user_id == current_user.id
        ).all()
        
        # Calculate performance metrics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j.status == ReportStatus.COMPLETED])
        failed_jobs = len([j for j in jobs if j.status == ReportStatus.FAILED])
        
        avg_processing_time = 0
        if history:
            processing_times = [
                h.performance_metrics.get("processing_time", 0) 
                for h in history 
                if h.performance_metrics
            ]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "campaign_id": campaign_id,
            "job_performance": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            },
            "processing_performance": {
                "average_processing_time": avg_processing_time,
                "total_scoring_runs": len(history)
            },
            "recent_history": [
                {
                    "id": h.id,
                    "report_id": h.report_id,
                    "version": h.version,
                    "created_at": h.created_at,
                    "results_summary": h.results_summary
                }
                for h in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring performance: {str(e)}"
        ) 

# Enhanced Analytics endpoints
@router.get("/{campaign_id}/enhanced-analytics")
async def get_enhanced_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive enhanced analytics for a campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get all reports for this campaign
        reports = db.query(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id,
            Report.status == ReportStatus.COMPLETED
        ).all()
        
        if not reports:
            return {
                "campaign_id": campaign_id,
                "message": "No completed reports found for analytics",
                "analytics": None
            }
        
        # Combine data from all reports
        all_data = []
        for report in reports:
            if report.file_path and os.path.exists(report.file_path):
                try:
                    file_ext = os.path.splitext(report.file_path)[1].lower()
                    if file_ext == '.csv':
                        df = pd.read_csv(report.file_path)
                    elif file_ext == '.json':
                        df = pd.read_json(report.file_path)
                    elif file_ext == '.parquet':
                        df = pd.read_parquet(report.file_path)
                    elif file_ext in ['.xls', '.xlsx']:
                        df = pd.read_excel(report.file_path)
                    else:
                        continue
                    
                    all_data.append(df)
                except Exception as e:
                    print(f"Error reading report {report.id}: {e}")
                    continue
        
        if not all_data:
            return {
                "campaign_id": campaign_id,
                "message": "No valid data found for analytics",
                "analytics": None
            }
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Extract campaign metadata
        campaign_metadata = {}
        if campaign.scoring_criteria and isinstance(campaign.scoring_criteria, dict):
            campaign_metadata = campaign.scoring_criteria
        
        # Generate analytics
        analytics_service = CampaignAnalytics()
        analysis = analytics_service.analyze_campaign_performance(combined_df, campaign_metadata)
        
        # Generate comprehensive report
        report = analytics_service.generate_analytics_report(campaign_id, analysis)
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate enhanced analytics: {str(e)}"
        )

@router.get("/{campaign_id}/analytics/summary")
async def get_analytics_summary(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary for quick dashboard display"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get basic campaign stats
        stats = service.get_campaign_stats(campaign_id, current_user.id)
        
        # Get recent reports
        recent_reports = db.query(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id
        ).order_by(Report.created_at.desc()).limit(5).all()
        
        summary = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "stats": stats,
            "recent_reports": [
                {
                    "id": report.id,
                    "filename": report.filename,
                    "status": report.status,
                    "created_at": report.created_at.isoformat(),
                    "score": report.score_data.get("total_score") if report.score_data else None
                }
                for report in recent_reports
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}"
        )

@router.get("/{campaign_id}/analytics/trends")
async def get_analytics_trends(
    campaign_id: int,
    period: str = Query("30d", description="Analysis period: 7d, 30d, 90d, all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trend analysis for a campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get reports within the specified period
        if period == "all":
            reports = db.query(Report).filter(
                Report.campaign_id == campaign_id,
                Report.user_id == current_user.id
            ).all()
        else:
            days = int(period.replace("d", ""))
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            reports = db.query(Report).filter(
                Report.campaign_id == campaign_id,
                Report.user_id == current_user.id,
                Report.created_at >= cutoff_date
            ).all()
        
        # Analyze trends
        trends_data = []
        for report in reports:
            if report.score_data:
                trends_data.append({
                    "date": report.created_at.isoformat(),
                    "score": report.score_data.get("total_score", 0),
                    "report_id": report.id
                })
        
        # Calculate trend statistics
        if trends_data:
            scores = [d["score"] for d in trends_data]
            trend_analysis = {
                "period": period,
                "data_points": len(trends_data),
                "average_score": sum(scores) / len(scores),
                "trend_direction": "increasing" if len(scores) > 1 and scores[-1] > scores[0] else "decreasing",
                "score_range": {
                    "min": min(scores),
                    "max": max(scores)
                },
                "trend_data": trends_data
            }
        else:
            trend_analysis = {
                "period": period,
                "data_points": 0,
                "message": "No data available for trend analysis"
            }
        
        return trend_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend analysis: {str(e)}"
        )

@router.get("/{campaign_id}/analytics/benchmarks")
async def get_analytics_benchmarks(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get benchmark comparisons for a campaign"""
    try:
        service = CampaignService(db)
        campaign = service.get_campaign(campaign_id, current_user.id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get campaign performance data
        reports = db.query(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id,
            Report.status == ReportStatus.COMPLETED
        ).all()
        
        if not reports:
            return {
                "campaign_id": campaign_id,
                "message": "No completed reports found for benchmark analysis"
            }
        
        # Calculate campaign averages
        scores = []
        for report in reports:
            if report.score_data and "total_score" in report.score_data:
                scores.append(report.score_data["total_score"])
        
        if not scores:
            return {
                "campaign_id": campaign_id,
                "message": "No score data available for benchmark analysis"
            }
        
        avg_score = sum(scores) / len(scores)
        
        # Industry benchmarks (example values)
        industry_benchmarks = {
            "average_score": 75.0,
            "excellent_threshold": 85.0,
            "good_threshold": 70.0,
            "poor_threshold": 50.0
        }
        
        # Calculate performance vs benchmarks
        performance_vs_benchmarks = {
            "campaign_average": avg_score,
            "industry_average": industry_benchmarks["average_score"],
            "performance_ratio": avg_score / industry_benchmarks["average_score"],
            "performance_category": "excellent" if avg_score >= industry_benchmarks["excellent_threshold"] else
                                  "good" if avg_score >= industry_benchmarks["good_threshold"] else
                                  "poor" if avg_score >= industry_benchmarks["poor_threshold"] else "very_poor",
            "percentile_rank": _calculate_percentile_rank(avg_score, industry_benchmarks)
        }
        
        return {
            "campaign_id": campaign_id,
            "industry_benchmarks": industry_benchmarks,
            "performance_vs_benchmarks": performance_vs_benchmarks,
            "score_distribution": {
                "total_reports": len(scores),
                "average_score": avg_score,
                "score_range": {
                    "min": min(scores),
                    "max": max(scores)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get benchmark analysis: {str(e)}"
        )

def _calculate_percentile_rank(score: float, benchmarks: Dict[str, float]) -> float:
    """Calculate percentile rank based on industry benchmarks"""
    # Simple percentile calculation based on industry distribution
    if score >= benchmarks["excellent_threshold"]:
        return 90.0
    elif score >= benchmarks["good_threshold"]:
        return 70.0
    elif score >= benchmarks["poor_threshold"]:
        return 40.0
    else:
        return 20.0 
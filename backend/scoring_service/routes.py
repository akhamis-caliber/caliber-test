from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import json

from config.database import get_db
from auth_service.middleware import get_current_user
from auth_service.models.user import User
from db.models import (
    Report, Campaign, ScoringJob, ScoringMetrics, ScoringHistory,
    ScoringResult, ReportStatus
)
from common.schemas import (
    ScoringJobCreate, ScoringJobUpdate, ScoringJobResponse,
    ScoringConfig, ScoringResultsResponse, ScoringSummaryResponse,
    ScoreReportRequest, BatchScoreRequest, ScoringComparisonRequest,
    ScoringValidationResponse, ScoringJobStatus, ScoringJobType
)
from scoring_service.scoring import ScoringEngine
from worker.tasks import process_file

router = APIRouter(prefix="/api/scoring", tags=["scoring"])

# Scoring Jobs Management
@router.post("/jobs", response_model=ScoringJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scoring_job(
    job_data: ScoringJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new scoring job"""
    try:
        # Verify report and campaign exist and belong to user
        report = db.query(Report).filter(
            Report.id == job_data.report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        campaign = db.query(Campaign).filter(
            Campaign.id == job_data.campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Create scoring job
        scoring_job = ScoringJob(
            report_id=job_data.report_id,
            campaign_id=job_data.campaign_id,
            user_id=current_user.id,
            job_type=job_data.job_type.value,
            config=job_data.config.dict() if job_data.config else None,
            status=ReportStatus.QUEUED
        )
        
        db.add(scoring_job)
        db.commit()
        db.refresh(scoring_job)
        
        # Queue background task
        if report.file_path:
            task = process_file.delay(
                report.file_path,
                job_data.campaign_id,
                current_user.id
            )
            scoring_job.task_id = task.id
            db.commit()
        
        return scoring_job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scoring job: {str(e)}"
        )

@router.get("/jobs", response_model=List[ScoringJobResponse])
async def get_scoring_jobs(
    campaign_id: Optional[int] = None,
    status: Optional[ScoringJobStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scoring jobs for the current user"""
    try:
        query = db.query(ScoringJob).filter(ScoringJob.user_id == current_user.id)
        
        if campaign_id:
            query = query.filter(ScoringJob.campaign_id == campaign_id)
        
        if status:
            query = query.filter(ScoringJob.status == status.value)
        
        jobs = query.offset(skip).limit(limit).all()
        return jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring jobs: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=ScoringJobResponse)
async def get_scoring_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific scoring job"""
    try:
        job = db.query(ScoringJob).filter(
            ScoringJob.id == job_id,
            ScoringJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring job not found"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring job: {str(e)}"
        )

@router.put("/jobs/{job_id}", response_model=ScoringJobResponse)
async def update_scoring_job(
    job_id: int,
    job_data: ScoringJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a scoring job"""
    try:
        job = db.query(ScoringJob).filter(
            ScoringJob.id == job_id,
            ScoringJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring job not found"
            )
        
        update_data = job_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(job, field, value)
        
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scoring job: {str(e)}"
        )

# Scoring Results
@router.get("/results/{report_id}", response_model=ScoringResultsResponse)
async def get_scoring_results(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scoring results for a specific report"""
    try:
        # Verify report belongs to user
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get scoring results
        scoring_results = db.query(ScoringResult).filter(
            ScoringResult.report_id == report_id
        ).all()
        
        if not scoring_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring results found for this report"
            )
        
        # Calculate final score and rank
        final_score = sum(result.weighted_score or 0 for result in scoring_results)
        score_rank = 1  # This would need to be calculated against other reports
        
        # Build component scores
        component_scores = []
        for result in scoring_results:
            component_scores.append({
                "metric_name": result.metric_name,
                "metric_value": result.metric_value,
                "score": result.score,
                "weight": result.weight,
                "weighted_score": result.weighted_score,
                "explanation": result.explanation,
                "metric_metadata": result.metric_metadata
            })
        
        return {
            "report_id": report_id,
            "campaign_id": report.campaign_id,
            "final_score": final_score,
            "score_rank": score_rank,
            "component_scores": component_scores,
            "processed_at": report.processed_at or datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring results: {str(e)}"
        )

@router.get("/summary/{campaign_id}", response_model=ScoringSummaryResponse)
async def get_campaign_scoring_summary(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scoring summary for a campaign"""
    try:
        # Verify campaign belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get all scoring results for the campaign
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.campaign_id == campaign_id,
            Report.user_id == current_user.id
        ).all()
        
        if not scoring_results:
            return {
                "total_records": 0,
                "average_score": 0.0,
                "median_score": 0.0,
                "std_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "score_distribution": {},
                "processing_time": 0.0
            }
        
        # Calculate summary statistics
        final_scores = []
        for result in scoring_results:
            if result.weighted_score:
                final_scores.append(result.weighted_score)
        
        if not final_scores:
            return {
                "total_records": len(scoring_results),
                "average_score": 0.0,
                "median_score": 0.0,
                "std_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "score_distribution": {},
                "processing_time": 0.0
            }
        
        import numpy as np
        final_scores = np.array(final_scores)
        
        # Calculate score distribution
        score_distribution = {
            "excellent": len(final_scores[final_scores >= 80]),
            "good": len(final_scores[(final_scores >= 60) & (final_scores < 80)]),
            "average": len(final_scores[(final_scores >= 40) & (final_scores < 60)]),
            "below_average": len(final_scores[(final_scores >= 20) & (final_scores < 40)]),
            "poor": len(final_scores[final_scores < 20])
        }
        
        return {
            "total_records": len(final_scores),
            "average_score": float(np.mean(final_scores)),
            "median_score": float(np.median(final_scores)),
            "std_score": float(np.std(final_scores)),
            "min_score": float(np.min(final_scores)),
            "max_score": float(np.max(final_scores)),
            "score_distribution": score_distribution,
            "processing_time": 0.0  # This would be calculated from job history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scoring summary: {str(e)}"
        )

# Batch Scoring
@router.post("/batch", response_model=List[ScoringJobResponse])
async def batch_score_reports(
    batch_data: BatchScoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score multiple reports in batch"""
    try:
        # Verify campaign belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == batch_data.campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        created_jobs = []
        
        for report_id in batch_data.report_ids:
            # Verify report belongs to user
            report = db.query(Report).filter(
                Report.id == report_id,
                Report.user_id == current_user.id
            ).first()
            
            if not report:
                continue
            
            # Create scoring job
            scoring_job = ScoringJob(
                report_id=report_id,
                campaign_id=batch_data.campaign_id,
                user_id=current_user.id,
                job_type=ScoringJobType.BATCH.value,
                config=batch_data.config.dict() if batch_data.config else None,
                status=ReportStatus.QUEUED
            )
            
            db.add(scoring_job)
            created_jobs.append(scoring_job)
        
        db.commit()
        
        # Queue background tasks
        for job in created_jobs:
            report = db.query(Report).filter(Report.id == job.report_id).first()
            if report and report.file_path:
                task = process_file.delay(
                    report.file_path,
                    batch_data.campaign_id,
                    current_user.id
                )
                job.task_id = task.id
        
        db.commit()
        
        return created_jobs
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch scoring jobs: {str(e)}"
        )

# Scoring Configuration
@router.post("/config/validate", response_model=ScoringValidationResponse)
async def validate_scoring_config(
    config: ScoringConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate scoring configuration"""
    try:
        errors = []
        warnings = []
        
        # Validate metrics
        if not config.metrics:
            errors.append({
                "field": "metrics",
                "message": "At least one metric must be configured",
                "value": None
            })
        
        # Validate weights sum to 1.0
        total_weight = sum(metric.weight for metric in config.metrics)
        if abs(total_weight - 1.0) > 0.01:
            errors.append({
                "field": "metrics",
                "message": f"Total weight must equal 1.0, got {total_weight}",
                "value": total_weight
            })
        
        # Validate metric configurations
        for i, metric in enumerate(config.metrics):
            if metric.min_value is not None and metric.max_value is not None:
                if metric.min_value >= metric.max_value:
                    errors.append({
                        "field": f"metrics[{i}].min_value",
                        "message": "min_value must be less than max_value",
                        "value": metric.min_value
                    })
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}"
        )

# Utility endpoints
@router.get("/status")
async def get_scoring_service_status():
    """Get scoring service status"""
    return {
        "status": "healthy",
        "service": "scoring",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

@router.get("/templates")
async def get_scoring_templates():
    """Get available scoring templates"""
    templates = [
        {
            "id": 1,
            "name": "Standard Scoring",
            "description": "Basic scoring template with equal weights",
            "category": "General",
            "config": {
                "metrics": [
                    {
                        "metric_name": "Performance",
                        "metric_type": "continuous",
                        "weight": 0.5
                    },
                    {
                        "metric_name": "Quality",
                        "metric_type": "continuous",
                        "weight": 0.5
                    }
                ]
            }
        },
        {
            "id": 2,
            "name": "Marketing Campaign",
            "description": "Template optimized for marketing campaigns",
            "category": "Marketing",
            "config": {
                "metrics": [
                    {
                        "metric_name": "Engagement",
                        "metric_type": "continuous",
                        "weight": 0.4
                    },
                    {
                        "metric_name": "Conversion",
                        "metric_type": "continuous",
                        "weight": 0.4
                    },
                    {
                        "metric_name": "Reach",
                        "metric_type": "continuous",
                        "weight": 0.2
                    }
                ]
            }
        }
    ]
    
    return templates 
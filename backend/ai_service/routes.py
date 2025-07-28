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
    Report, Campaign, ScoringJob, ScoringResult, ScoringHistory
)
from common.schemas import (
    AIInsightRequest, AIInsightResponse, AIExplanationRequest, 
    AIExplanationResponse, AIQAResponse, AIRecommendationRequest,
    AIRecommendationResponse, AITrendAnalysisResponse
)
from ai_service.insight_generator import (
    generate_ai_insights, generate_openai_insights, 
    generate_recommendations, extract_key_findings, identify_trends
)
from ai_service.explanation_service import generate_score_explanation
from ai_service.qa_service import answer_question_about_data
from ai_service.trend_analyzer import analyze_trends_over_time

router = APIRouter(prefix="/api/ai", tags=["AI Services"])

@router.post("/insights", response_model=AIInsightResponse)
async def generate_insights(
    request: AIInsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered insights for scoring results"""
    try:
        # Verify campaign belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        ).first()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Get scoring results for the campaign
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.campaign_id == request.campaign_id,
            Report.user_id == current_user.id
        ).all()

        if not scoring_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring results found for this campaign"
            )

        # Convert to DataFrame for analysis
        data = []
        for result in scoring_results:
            data.append({
                'report_id': result.report_id,
                'metric_name': result.metric_name,
                'metric_value': result.metric_value,
                'score': result.score,
                'weight': result.weight,
                'weighted_score': result.weighted_score,
                'explanation': result.explanation
            })

        scores_df = pd.DataFrame(data)
        
        # Calculate final scores per report
        final_scores = scores_df.groupby('report_id')['weighted_score'].sum().reset_index()
        final_scores.columns = ['report_id', 'final_score']

        # Generate AI insights
        insights_data = generate_ai_insights(final_scores, request.campaign_id)

        return {
            "campaign_id": request.campaign_id,
            "insights": insights_data.get("insights", []),
            "recommendations": insights_data.get("recommendations", []),
            "key_findings": insights_data.get("key_findings", []),
            "trends": insights_data.get("trends", {}),
            "generated_at": datetime.utcnow(),
            "data_summary": {
                "total_reports": len(final_scores),
                "average_score": float(final_scores['final_score'].mean()),
                "score_range": float(final_scores['final_score'].max() - final_scores['final_score'].min())
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )

@router.post("/explain", response_model=AIExplanationResponse)
async def explain_score(
    request: AIExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI explanation for a specific score"""
    try:
        # Verify report belongs to user
        report = db.query(Report).filter(
            Report.id == request.report_id,
            Report.user_id == current_user.id
        ).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Get scoring results for the report
        scoring_results = db.query(ScoringResult).filter(
            ScoringResult.report_id == request.report_id
        ).all()

        if not scoring_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring results found for this report"
            )

        # Generate explanation
        explanation = generate_score_explanation(
            scoring_results, 
            request.explanation_type,
            request.detail_level
        )

        return {
            "report_id": request.report_id,
            "explanation_type": request.explanation_type,
            "detail_level": request.detail_level,
            "explanation": explanation,
            "generated_at": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.post("/qa", response_model=AIQAResponse)
async def answer_question(
    question: str = Query(..., description="Question about the scoring data"),
    campaign_id: Optional[int] = Query(None, description="Campaign ID to focus on"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Answer questions about scoring data using AI"""
    try:
        # Get scoring data
        query = db.query(ScoringResult).join(Report).filter(
            Report.user_id == current_user.id
        )

        if campaign_id:
            query = query.filter(Report.campaign_id == campaign_id)

        scoring_results = query.all()

        if not scoring_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring data found"
            )

        # Convert to DataFrame
        data = []
        for result in scoring_results:
            data.append({
                'report_id': result.report_id,
                'campaign_id': result.report.campaign_id,
                'metric_name': result.metric_name,
                'metric_value': result.metric_value,
                'score': result.score,
                'weight': result.weight,
                'weighted_score': result.weighted_score
            })

        scores_df = pd.DataFrame(data)

        # Generate answer
        answer = answer_question_about_data(scores_df, question, campaign_id)

        return {
            "question": question,
            "answer": answer,
            "campaign_id": campaign_id,
            "generated_at": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )

@router.post("/recommendations", response_model=AIRecommendationResponse)
async def generate_recommendations_for_campaign(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI recommendations for campaign improvement"""
    try:
        # Verify campaign belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        ).first()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Get scoring results
        scoring_results = db.query(ScoringResult).join(Report).filter(
            Report.campaign_id == request.campaign_id,
            Report.user_id == current_user.id
        ).all()

        if not scoring_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring data found for this campaign"
            )

        # Convert to DataFrame
        data = []
        for result in scoring_results:
            data.append({
                'report_id': result.report_id,
                'metric_name': result.metric_name,
                'metric_value': result.metric_value,
                'score': result.score,
                'weight': result.weight,
                'weighted_score': result.weighted_score
            })

        scores_df = pd.DataFrame(data)

        # Generate recommendations
        recommendations = generate_recommendations(scores_df, [])

        return {
            "campaign_id": request.campaign_id,
            "recommendations": recommendations,
            "focus_area": request.focus_area,
            "generated_at": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.get("/trends/{campaign_id}", response_model=AITrendAnalysisResponse)
async def analyze_trends(
    campaign_id: int,
    time_period: str = Query("30d", description="Time period for trend analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze trends in scoring data over time"""
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

        # Get scoring history
        scoring_history = db.query(ScoringHistory).filter(
            ScoringHistory.campaign_id == campaign_id
        ).order_by(ScoringHistory.created_at.desc()).all()

        if not scoring_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring history found for this campaign"
            )

        # Analyze trends
        trends = analyze_trends_over_time(scoring_history, time_period)

        return {
            "campaign_id": campaign_id,
            "time_period": time_period,
            "trends": trends,
            "generated_at": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trends: {str(e)}"
        )

@router.get("/status")
async def get_ai_service_status():
    """Get AI service status"""
    return {
        "status": "healthy",
        "service": "ai",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "features": [
            "insights_generation",
            "score_explanation",
            "qa_system",
            "recommendations",
            "trend_analysis"
        ]
    } 
import pandas as pd
import io
from sqlalchemy.orm import Session
from typing import Tuple, Dict, Any, List
import uuid
import json
import logging
from datetime import datetime, timedelta
import asyncio

from db.models import Campaign, ScoringResult, User
from scoring_service.config import ScoringConfigManager, ScoringPlatform, CampaignGoal, Channel
from scoring_service.preprocess import DataPreprocessor
from scoring_service.normalize import DataNormalizer
from scoring_service.scoring import ScoringEngine, OutlierDetector
from report_service.storage import file_storage
from common.exceptions import ValidationError, NotFoundError
from campaign_service.schemas import CampaignStatus

logger = logging.getLogger(__name__)

class ScoringController:
    
    @staticmethod
    def start_scoring_process(
        db: Session,
        campaign_id: uuid.UUID,
        user: User
    ) -> Dict[str, Any]:
        """Start the scoring process for a campaign"""
        
        # Get campaign
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if not campaign.file_path:
            raise ValidationError("No file uploaded for this campaign")
        
        # Update campaign status
        campaign.status = CampaignStatus.PROCESSING
        campaign.progress_percentage = 0
        db.commit()
        
        try:
            # Get scoring configuration
            config = ScoringConfigManager.get_config(
                platform=ScoringPlatform(campaign.campaign_type),
                goal=CampaignGoal(campaign.goal),
                channel=Channel(campaign.channel),
                ctr_sensitivity=campaign.ctr_sensitivity
            )
            
            # Store config snapshot
            campaign.scoring_config_snapshot = config.__dict__
            campaign.scoring_config_snapshot["metrics"] = [
                metric.__dict__ for metric in config.metrics
            ]
            db.commit()
            
            # Start processing (this would typically be a background task)
            results = ScoringController._process_scoring(db, campaign, config)
            
            return {
                "campaign_id": campaign_id,
                "status": "started",
                "estimated_completion": datetime.utcnow() + timedelta(minutes=5),
                "config_used": campaign.scoring_config_snapshot
            }
            
        except Exception as e:
            campaign.status = CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit()
            raise
    
    @staticmethod
    def _process_scoring(
        db: Session,
        campaign: Campaign,
        config
    ) -> Dict[str, Any]:
        """Process scoring for a campaign (main scoring pipeline)"""
        
        try:
            logger.info(f"Starting scoring process for campaign {campaign.id}")
            start_time = datetime.utcnow()
            
            # Step 1: Load data file
            campaign.progress_percentage = 10
            db.commit()
            
            file_content = asyncio.run(file_storage.read_file(campaign.file_path))
            
            # Parse file based on extension
            if campaign.file_path.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            campaign.total_records = len(df)
            campaign.progress_percentage = 20
            db.commit()
            
            # Step 2: Preprocess data
            logger.info("Starting data preprocessing")
            preprocessor = DataPreprocessor(config)
            df_processed, processing_report = preprocessor.process_file(df)
            
            campaign.data_quality_report = processing_report
            campaign.progress_percentage = 40
            db.commit()
            
            # Step 3: Normalize metrics
            logger.info("Starting data normalization")
            normalizer = DataNormalizer(config)
            df_normalized, normalization_stats = normalizer.normalize_data(df_processed)
            
            campaign.progress_percentage = 60
            db.commit()
            
            # Step 4: Calculate scores
            logger.info("Calculating scores")
            scoring_engine = ScoringEngine(config)
            df_scored, scoring_stats = scoring_engine.calculate_scores(df_normalized)
            
            campaign.progress_percentage = 80
            db.commit()
            
            # Step 5: Detect outliers
            outlier_detector = OutlierDetector()
            metrics_to_check = [metric.name for metric in config.metrics]
            df_final = outlier_detector.detect_outliers(df_scored, metrics_to_check)
            
            # Step 6: Save results to database
            logger.info("Saving results to database")
            ScoringController._save_results_to_db(db, campaign, df_final, config)
            
            # Calculate campaign-level metrics
            campaign_metrics = scoring_engine.get_campaign_level_score(df_final)
            
            # Update campaign status
            campaign.status = CampaignStatus.COMPLETED
            campaign.progress_percentage = 100
            campaign.processed_records = len(df_final)
            campaign.completed_at = datetime.utcnow()
            
            # Store campaign-level score in error_message field (temporary solution)
            campaign.error_message = json.dumps(campaign_metrics)
            
            db.commit()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Scoring completed in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "total_records": len(df_final),
                "processing_time": processing_time,
                "campaign_score": campaign_metrics["campaign_level_score"],
                "data_quality_issues": processing_report.get("data_quality_issues", [])
            }
            
        except Exception as e:
            logger.error(f"Scoring process failed: {e}")
            campaign.status = CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit()
            raise
    
    @staticmethod
    def _save_results_to_db(
        db: Session,
        campaign: Campaign,
        df: pd.DataFrame,
        config
    ):
        """Save scoring results to database"""
        
        # Clear existing results
        db.query(ScoringResult).filter(ScoringResult.campaign_id == campaign.id).delete()
        
        # Determine dimension column
        dimension_col = "domain" if "domain" in df.columns else "supply_vendor"
        
        # Save each result
        for _, row in df.iterrows():
            # Extract raw metrics
            raw_metrics = {}
            normalized_metrics = {}
            
            for metric in config.metrics:
                if metric.name in row:
                    raw_metrics[metric.name] = float(row[metric.name]) if pd.notna(row[metric.name]) else None
                
                normalized_col = f"{metric.name}_normalized"
                if normalized_col in row:
                    normalized_metrics[metric.name] = float(row[normalized_col]) if pd.notna(row[normalized_col]) else None
            
            # Create scoring result
            result = ScoringResult(
                campaign_id=campaign.id,
                domain=str(row[dimension_col]),
                impressions=int(row["impressions"]) if pd.notna(row["impressions"]) else 0,
                ctr=float(row["ctr"]) if pd.notna(row["ctr"]) else 0.0,
                conversions=int(row["conversions"]) if "conversions" in row and pd.notna(row["conversions"]) else 0,
                total_spend=float(row.get("total_spend", row.get("advertiser_cost", 0))) if pd.notna(row.get("total_spend", row.get("advertiser_cost", 0))) else 0.0,
                
                # Calculated metrics
                cpm=float(row.get("cpm", row.get("ecpm", 0))) if pd.notna(row.get("cpm", row.get("ecpm", 0))) else 0.0,
                conversion_rate=float(row["conversion_rate"]) if "conversion_rate" in row and pd.notna(row["conversion_rate"]) else 0.0,
                
                # Raw and normalized metrics
                raw_metrics=raw_metrics,
                normalized_metrics=normalized_metrics,
                
                # Scoring
                score=int(round(row["coegi_inventory_quality_score"])),
                score_breakdown=row.get("score_breakdown", {}),
                status=row["quality_status"],
                percentile_rank=int(row["percentile_rank"]),
                
                # Quality flags
                quality_flags=row.get("outlier_flags", [])
            )
            
            db.add(result)
        
        db.commit()
        logger.info(f"Saved {len(df)} scoring results to database")
    
    @staticmethod
    def get_scoring_progress(
        db: Session,
        campaign_id: uuid.UUID,
        user: User
    ) -> Dict[str, Any]:
        """Get scoring progress for a campaign"""
        
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Estimate completion time based on progress
        estimated_completion = None
        if campaign.status == CampaignStatus.PROCESSING and campaign.progress_percentage > 0:
            # Rough estimation: 5 minutes total processing time
            remaining_percentage = 100 - campaign.progress_percentage
            remaining_minutes = (remaining_percentage / 100) * 5
            estimated_completion = datetime.utcnow() + timedelta(minutes=remaining_minutes)
        
        return {
            "campaign_id": campaign_id,
            "status": campaign.status,
            "progress_percentage": campaign.progress_percentage or 0,
            "total_records": campaign.total_records,
            "processed_records": campaign.processed_records,
            "error_message": campaign.error_message if campaign.status == CampaignStatus.FAILED else None,
            "estimated_completion": estimated_completion,
            "completed_at": campaign.completed_at
        }
    
    @staticmethod
    def get_scoring_results(
        db: Session,
        campaign_id: uuid.UUID,
        user: User,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = "score",
        sort_direction: str = "desc",
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get paginated scoring results"""
        
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if campaign.status != CampaignStatus.COMPLETED:
            raise ValidationError("Campaign scoring not completed")
        
        # Build query
        query = db.query(ScoringResult).filter(ScoringResult.campaign_id == campaign_id)
        
        # Apply filters
        if filters:
            if filters.get("quality_status"):
                query = query.filter(ScoringResult.status == filters["quality_status"])
            
            if filters.get("min_score"):
                query = query.filter(ScoringResult.score >= filters["min_score"])
            
            if filters.get("max_score"):
                query = query.filter(ScoringResult.score <= filters["max_score"])
            
            if filters.get("min_impressions"):
                query = query.filter(ScoringResult.impressions >= filters["min_impressions"])
        
        # Apply sorting
        sort_column = getattr(ScoringResult, sort_by, ScoringResult.score)
        if sort_direction.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()
        
        # Convert to dict format
        results_data = []
        for result in results:
            result_dict = {
                "domain": result.domain,
                "impressions": result.impressions,
                "spend": float(result.total_spend),
                "cpm": float(result.cpm) if result.cpm else 0.0,
                "ctr": float(result.ctr),
                "conversions": result.conversions,
                "conversion_rate": float(result.conversion_rate) if result.conversion_rate else 0.0,
                "score": result.score,
                "percentile_rank": result.percentile_rank,
                "quality_status": result.status,
                "score_breakdown": result.score_breakdown or {},
                "raw_metrics": result.raw_metrics or {},
                "normalized_metrics": result.normalized_metrics or {},
                "quality_flags": result.quality_flags or []
            }
            results_data.append(result_dict)
        
        return {
            "results": results_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            }
        }
    
    @staticmethod
    def generate_optimization_list(
        db: Session,
        campaign_id: uuid.UUID,
        user: User,
        list_type: str,
        min_impressions: int = 250
    ) -> Dict[str, Any]:
        """Generate whitelist or blacklist for optimization"""
        
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if campaign.status != CampaignStatus.COMPLETED:
            raise ValidationError("Campaign scoring not completed")
        
        # Get all results for the campaign
        results = db.query(ScoringResult).filter(
            ScoringResult.campaign_id == campaign_id,
            ScoringResult.impressions >= min_impressions
        ).all()
        
        if not results:
            raise ValidationError(f"No results found with minimum {min_impressions} impressions")
        
        # Sort by score
        if list_type == "whitelist":
            results = sorted(results, key=lambda x: x.score, reverse=True)
            # Get top 25%
            threshold_index = int(len(results) * 0.75)
            selected_results = results[:threshold_index]
        else:  # blacklist
            results = sorted(results, key=lambda x: x.score)
            # Get bottom 25%
            threshold_index = int(len(results) * 0.25)
            selected_results = results[:threshold_index]
        
        # Calculate summary metrics
        total_impressions = sum(r.impressions for r in selected_results)
        average_score = sum(r.score for r in selected_results) / len(selected_results) if selected_results else 0
        
        return {
            "list_type": list_type,
            "campaign_id": campaign_id,
            "domains": [r.domain for r in selected_results],
            "criteria_used": {
                "min_impressions": min_impressions,
                "threshold_percentage": 25,
                "total_candidates": len(results),
                "selected_count": len(selected_results)
            },
            "total_impressions": total_impressions,
            "average_score": round(average_score, 1)
        }
    
    @staticmethod
    def get_campaign_summary(
        db: Session,
        campaign_id: uuid.UUID,
        user: User
    ) -> Dict[str, Any]:
        """Get comprehensive campaign summary"""
        
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if campaign.status != CampaignStatus.COMPLETED:
            raise ValidationError("Campaign scoring not completed")
        
        # Get all results
        results = db.query(ScoringResult).filter(ScoringResult.campaign_id == campaign_id).all()
        
        if not results:
            raise ValidationError("No scoring results found")
        
        # Calculate summary statistics
        total_domains = len(results)
        scores = [r.score for r in results]
        average_score = sum(scores) / len(scores)
        
        # Score distribution
        score_distribution = {
            "good": len([r for r in results if r.status == "good"]),
            "moderate": len([r for r in results if r.status == "moderate"]),
            "poor": len([r for r in results if r.status == "poor"])
        }
        
        # Top and bottom performers
        top_performers = sorted(results, key=lambda x: x.score, reverse=True)[:5]
        bottom_performers = sorted(results, key=lambda x: x.score)[:5]
        
        # Campaign-level metrics
        total_impressions = sum(r.impressions for r in results)
        total_spend = sum(r.total_spend for r in results)
        average_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        
        # Get campaign-level score from stored metrics
        campaign_metrics = {}
        if campaign.error_message:
            try:
                campaign_metrics = json.loads(campaign.error_message)
            except:
                pass
        
        return {
            "campaign_id": campaign_id,
            "total_domains": total_domains,
            "average_score": round(average_score, 1),
            "score_distribution": score_distribution,
            "top_performers": [
                {"domain": r.domain, "score": r.score, "impressions": r.impressions}
                for r in top_performers
            ],
            "bottom_performers": [
                {"domain": r.domain, "score": r.score, "impressions": r.impressions}
                for r in bottom_performers
            ],
            "campaign_metrics": {
                "total_impressions": total_impressions,
                "total_spend": float(total_spend),
                "average_cpm": round(average_cpm, 2),
                "campaign_level_score": campaign_metrics.get("campaign_level_score", round(average_score, 1))
            },
            "data_quality_issues": campaign.data_quality_report.get("data_quality_issues", []) if campaign.data_quality_report else [],
            "scoring_config": campaign.scoring_config_snapshot
        } 
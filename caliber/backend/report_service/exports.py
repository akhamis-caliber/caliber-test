import pandas as pd
import io
import csv
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from db.models import Campaign, ScoringResult, User
from scoring_service.controllers import ScoringController
from common.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class ExportService:
    """Service for exporting campaign data and generating optimization lists"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_scoring_results_csv(
        self,
        campaign_id: str,
        user: User,
        filters: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export scoring results to CSV format"""
        
        # Validate campaign ownership
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if campaign.status != "completed":
            raise ValidationError("Campaign scoring not completed")
        
        # Get scoring results
        results_data = ScoringController.get_scoring_results(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            page=1,
            per_page=10000,  # Get all results
            filters=filters
        )
        
        if not results_data["results"]:
            raise ValidationError("No results found for export")
        
        # Create DataFrame
        df = pd.DataFrame(results_data["results"])
        
        # Add campaign metadata
        df["campaign_name"] = campaign.name
        df["campaign_type"] = campaign.campaign_type
        df["goal"] = campaign.goal
        df["channel"] = campaign.channel
        df["export_date"] = datetime.utcnow().isoformat()
        
        # Reorder columns for better readability
        column_order = [
            "campaign_name", "campaign_type", "goal", "channel",
            "domain", "score", "quality_status", "percentile_rank",
            "impressions", "spend", "cpm", "ctr", "conversions", "conversion_rate",
            "raw_metrics", "normalized_metrics", "score_breakdown", "quality_flags",
            "export_date"
        ]
        
        # Only include columns that exist in the DataFrame
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Export to CSV
        output = io.BytesIO()
        df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
        output.seek(0)
        
        return output.getvalue()
    
    def export_whitelist_csv(
        self,
        campaign_id: str,
        user: User,
        min_impressions: int = 250
    ) -> bytes:
        """Export whitelist to CSV format"""
        
        # Generate whitelist
        whitelist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="whitelist",
            min_impressions=min_impressions
        )
        
        # Get campaign info
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        # Create DataFrame
        df = pd.DataFrame({
            "domain": whitelist_data["domains"],
            "list_type": "whitelist",
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "min_impressions": min_impressions,
            "average_score": whitelist_data["average_score"],
            "total_impressions": whitelist_data["total_impressions"],
            "export_date": datetime.utcnow().isoformat()
        })
        
        # Export to CSV
        output = io.BytesIO()
        df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
        output.seek(0)
        
        return output.getvalue()
    
    def export_blacklist_csv(
        self,
        campaign_id: str,
        user: User,
        min_impressions: int = 250
    ) -> bytes:
        """Export blacklist to CSV format"""
        
        # Generate blacklist
        blacklist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="blacklist",
            min_impressions=min_impressions
        )
        
        # Get campaign info
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        # Create DataFrame
        df = pd.DataFrame({
            "domain": blacklist_data["domains"],
            "list_type": "blacklist",
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "min_impressions": min_impressions,
            "average_score": blacklist_data["average_score"],
            "total_impressions": blacklist_data["total_impressions"],
            "export_date": datetime.utcnow().isoformat()
        })
        
        # Export to CSV
        output = io.BytesIO()
        df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
        output.seek(0)
        
        return output.getvalue()
    
    def export_campaign_summary_csv(
        self,
        campaign_id: str,
        user: User
    ) -> bytes:
        """Export campaign summary to CSV format"""
        
        # Get campaign summary
        summary_data = ScoringController.get_campaign_summary(
            db=self.db,
            campaign_id=campaign_id,
            user=user
        )
        
        # Create summary DataFrame
        summary_df = pd.DataFrame([{
            "campaign_id": campaign_id,
            "campaign_name": summary_data.get("campaign_name", ""),
            "total_domains": summary_data["total_domains"],
            "average_score": summary_data["average_score"],
            "good_domains": summary_data["score_distribution"]["good"],
            "moderate_domains": summary_data["score_distribution"]["moderate"],
            "poor_domains": summary_data["score_distribution"]["poor"],
            "total_impressions": summary_data["campaign_metrics"]["total_impressions"],
            "total_spend": summary_data["campaign_metrics"]["total_spend"],
            "average_cpm": summary_data["campaign_metrics"]["average_cpm"],
            "campaign_level_score": summary_data["campaign_metrics"]["campaign_level_score"],
            "export_date": datetime.utcnow().isoformat()
        }])
        
        # Export to CSV
        output = io.BytesIO()
        summary_df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
        output.seek(0)
        
        return output.getvalue()
    
    def export_optimization_lists_csv(
        self,
        campaign_id: str,
        user: User,
        min_impressions: int = 250
    ) -> bytes:
        """Export both whitelist and blacklist to a single CSV"""
        
        # Generate both lists
        whitelist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="whitelist",
            min_impressions=min_impressions
        )
        
        blacklist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="blacklist",
            min_impressions=min_impressions
        )
        
        # Get campaign info
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        # Create combined DataFrame
        whitelist_df = pd.DataFrame({
            "domain": whitelist_data["domains"],
            "list_type": "whitelist",
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "min_impressions": min_impressions,
            "average_score": whitelist_data["average_score"],
            "total_impressions": whitelist_data["total_impressions"],
            "export_date": datetime.utcnow().isoformat()
        })
        
        blacklist_df = pd.DataFrame({
            "domain": blacklist_data["domains"],
            "list_type": "blacklist",
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "min_impressions": min_impressions,
            "average_score": blacklist_data["average_score"],
            "total_impressions": blacklist_data["total_impressions"],
            "export_date": datetime.utcnow().isoformat()
        })
        
        # Combine DataFrames
        combined_df = pd.concat([whitelist_df, blacklist_df], ignore_index=True)
        
        # Export to CSV
        output = io.BytesIO()
        combined_df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
        output.seek(0)
        
        return output.getvalue()
    
    def generate_whitelist_json(
        self,
        campaign_id: str,
        user: User,
        min_impressions: int = 250
    ) -> Dict[str, Any]:
        """Generate whitelist in JSON format for API consumption"""
        
        # Generate whitelist
        whitelist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="whitelist",
            min_impressions=min_impressions
        )
        
        # Get campaign info
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        return {
            "list_type": "whitelist",
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "domains": whitelist_data["domains"],
            "criteria": {
                "min_impressions": min_impressions,
                "threshold_percentage": 25,
                "total_candidates": whitelist_data["criteria_used"]["total_candidates"],
                "selected_count": whitelist_data["criteria_used"]["selected_count"]
            },
            "metrics": {
                "total_impressions": whitelist_data["total_impressions"],
                "average_score": whitelist_data["average_score"]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_blacklist_json(
        self,
        campaign_id: str,
        user: User,
        min_impressions: int = 250
    ) -> Dict[str, Any]:
        """Generate blacklist in JSON format for API consumption"""
        
        # Generate blacklist
        blacklist_data = ScoringController.generate_optimization_list(
            db=self.db,
            campaign_id=campaign_id,
            user=user,
            list_type="blacklist",
            min_impressions=min_impressions
        )
        
        # Get campaign info
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        return {
            "list_type": "blacklist",
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "domains": blacklist_data["domains"],
            "criteria": {
                "min_impressions": min_impressions,
                "threshold_percentage": 25,
                "total_candidates": blacklist_data["criteria_used"]["total_candidates"],
                "selected_count": blacklist_data["criteria_used"]["selected_count"]
            },
            "metrics": {
                "total_impressions": blacklist_data["total_impressions"],
                "average_score": blacklist_data["average_score"]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def export_campaign_data_json(
        self,
        campaign_id: str,
        user: User,
        include_results: bool = True,
        include_insights: bool = False
    ) -> Dict[str, Any]:
        """Export complete campaign data in JSON format"""
        
        # Get campaign
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Build export data
        export_data = {
            "campaign": {
                "id": str(campaign.id),
                "name": campaign.name,
                "campaign_type": campaign.campaign_type,
                "goal": campaign.goal,
                "channel": campaign.channel,
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat(),
                "scoring_config": campaign.scoring_config_snapshot,
                "data_quality_report": campaign.data_quality_report
            },
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "exported_by": str(user.id),
                "include_results": include_results,
                "include_insights": include_insights
            }
        }
        
        # Add scoring results if requested
        if include_results and campaign.status == "completed":
            results_data = ScoringController.get_scoring_results(
                db=self.db,
                campaign_id=campaign_id,
                user=user,
                page=1,
                per_page=10000
            )
            export_data["scoring_results"] = results_data
        
        # Add campaign summary
        if campaign.status == "completed":
            summary_data = ScoringController.get_campaign_summary(
                db=self.db,
                campaign_id=campaign_id,
                user=user
            )
            export_data["campaign_summary"] = summary_data
        
        # Add insights if requested
        if include_insights:
            from ai_service.controllers import AIController
            ai_controller = AIController(self.db)
            insights_data = ai_controller.get_campaign_insights(
                campaign_id=campaign_id,
                user=user
            )
            export_data["ai_insights"] = insights_data
        
        return export_data


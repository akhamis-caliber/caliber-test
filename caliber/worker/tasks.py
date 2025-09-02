"""
Celery tasks for background processing
"""

from celery import current_task
import os
import sys
import pandas as pd
import json
from pathlib import Path
from typing import Optional

# Add backend to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from worker.celery import celery_app
from db.base import SessionLocal
from db.models import Report, ScoreRow, Campaign, ReportStatus, ScoreStatus
from scoring_service.preprocess import preprocess_data
from scoring_service.normalize import normalize_campaign_metrics, create_final_normalized_features
from scoring_service.weighting import calculate_weights
from scoring_service.outliers import handle_outliers_for_scoring
from scoring_service.scoring import calculate_domain_scores, rank_domains
from scoring_service.explain import generate_explanations
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def score_report(self, report_id: str) -> dict:
    """
    Main task to score an uploaded report
    
    Args:
        report_id: UUID of the report to process
        
    Returns:
        Dictionary with processing results
    """
    db = SessionLocal()
    
    try:
        # Update task progress
        self.update_state(state="PROGRESS", meta={"current": 0, "total": 100, "status": "Starting..."})
        
        # Get report from database
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Update report status
        report.status = ReportStatus.SCORING
        db.commit()
        
        # Get campaign details for scoring configuration
        campaign = db.query(Campaign).filter(Campaign.id == report.campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {report.campaign_id} not found")
        
        self.update_state(state="PROGRESS", meta={"current": 10, "total": 100, "status": "Loading file..."})
        
        # Load the uploaded file
        file_path = Path(settings.STORAGE_ROOT) / report.storage_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Report file not found: {file_path}")
        
        # Read file based on extension
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        
        self.update_state(state="PROGRESS", meta={"current": 20, "total": 100, "status": "Preprocessing data..."})
        
        # Step 1: Preprocess data
        df, preprocess_summary = preprocess_data(df)
        
        self.update_state(state="PROGRESS", meta={"current": 35, "total": 100, "status": "Handling outliers..."})
        
        # Step 2: Handle outliers
        df, outlier_summary = handle_outliers_for_scoring(df)
        
        self.update_state(state="PROGRESS", meta={"current": 50, "total": 100, "status": "Normalizing metrics..."})
        
        # Step 3: Normalize metrics
        df, norm_summary = normalize_campaign_metrics(df, method='robust')
        
        # Step 4: Create final normalized features
        df, feature_columns = create_final_normalized_features(df)
        
        self.update_state(state="PROGRESS", meta={"current": 65, "total": 100, "status": "Calculating scores..."})
        
        # Step 5: Calculate weights based on campaign configuration
        weights, weight_summary = calculate_weights(
            campaign.goal.value, 
            campaign.ctr_sensitivity
        )
        
        # Step 6: Calculate scores
        df, scoring_summary = calculate_domain_scores(df, weights, feature_columns)
        
        # Step 7: Add rankings
        df, ranking_summary = rank_domains(df)
        
        self.update_state(state="PROGRESS", meta={"current": 80, "total": 100, "status": "Generating explanations..."})
        
        # Step 8: Generate explanations
        df = generate_explanations(df, weights)
        
        self.update_state(state="PROGRESS", meta={"current": 90, "total": 100, "status": "Saving results..."})
        
        # Clear existing score rows
        db.query(ScoreRow).filter(ScoreRow.report_id == report_id).delete()
        
        # Save score rows to database
        score_rows = []
        for _, row in df.iterrows():
            score_row = ScoreRow(
                report_id=report_id,
                domain=row['domain'],
                publisher=row.get('publisher'),
                cpm=row.get('cpm'),
                ctr=row.get('ctr'),
                conversion_rate=row.get('conversion_rate'),
                impressions=row.get('impressions'),
                total_spend=row.get('total_spend'),
                conversions=row.get('conversions'),
                score=row['score'],
                status=ScoreStatus(row['status']),
                channel=row.get('channel'),
                vendor=row.get('vendor'),
                explanation=row.get('explanation')
            )
            score_rows.append(score_row)
        
        # Batch insert
        db.add_all(score_rows)
        
        # Create summary JSON
        summary_json = {
            'preprocessing': preprocess_summary,
            'outlier_handling': outlier_summary,
            'normalization': norm_summary,
            'weighting': weight_summary,
            'scoring': scoring_summary,
            'ranking': ranking_summary,
            'total_rows': len(df),
            'score_distribution': scoring_summary['status_details']['distribution'],
            'top_domains': ranking_summary['top_performers'][:10],
            'metrics_summary': {
                'cpm': {
                    'mean': float(df['cpm'].mean()) if 'cpm' in df else 0,
                    'median': float(df['cpm'].median()) if 'cmp' in df else 0,
                    'min': float(df['cpm'].min()) if 'cpm' in df else 0,
                    'max': float(df['cpm'].max()) if 'cpm' in df else 0
                },
                'ctr': {
                    'mean': float(df['ctr'].mean()) if 'ctr' in df else 0,
                    'median': float(df['ctr'].median()) if 'ctr' in df else 0,
                    'min': float(df['ctr'].min()) if 'ctr' in df else 0,
                    'max': float(df['ctr'].max()) if 'ctr' in df else 0
                },
                'conversion_rate': {
                    'mean': float(df['conversion_rate'].mean()) if 'conversion_rate' in df else 0,
                    'median': float(df['conversion_rate'].median()) if 'conversion_rate' in df else 0,
                    'min': float(df['conversion_rate'].min()) if 'conversion_rate' in df else 0,
                    'max': float(df['conversion_rate'].max()) if 'conversion_rate' in df else 0
                }
            }
        }
        
        # Update report with results
        report.status = ReportStatus.COMPLETED
        report.summary_json = summary_json
        report.error_message = None
        
        db.commit()
        
        # Save processed data as CSV for exports
        results_dir = Path(settings.STORAGE_ROOT) / str(report.campaign.org_id) / str(report_id)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(results_dir / "scores.csv", index=False)
        
        with open(results_dir / "summary.json", "w") as f:
            json.dump(summary_json, f, indent=2, default=str)
        
        self.update_state(state="SUCCESS", meta={"current": 100, "total": 100, "status": "Completed"})
        
        logger.info(f"Successfully scored report {report_id}: {len(score_rows)} rows")
        
        return {
            "status": "completed",
            "report_id": str(report_id),
            "rows_processed": len(score_rows),
            "score_distribution": scoring_summary['status_details']['distribution']
        }
        
    except Exception as e:
        logger.error(f"Error scoring report {report_id}: {str(e)}")
        
        # Update report with error
        if 'report' in locals():
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            db.commit()
        
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_reports():
    """Periodic task to clean up old reports and files"""
    db = SessionLocal()
    
    try:
        # This is a placeholder for cleanup logic
        # In a real implementation, you might:
        # 1. Delete reports older than X days
        # 2. Clean up orphaned files
        # 3. Archive old data
        
        logger.info("Cleanup task executed")
        return {"status": "completed", "message": "Cleanup task executed"}
        
    finally:
        db.close()
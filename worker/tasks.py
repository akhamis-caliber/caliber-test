from celery import current_task
from worker.celery import celery
import pandas as pd
import json
import os
import sys
from datetime import datetime
import numpy as np

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.settings import settings
from scoring_service import ScoringEngine, preprocess_data
from ai_service.insight_generator import generate_openai_insights

@celery.task(bind=True)
def process_and_score_dataset(self, file_path: str, campaign_id: int, user_id: int, report_id: int):
    """
    Enhanced background task to process uploaded files and generate scores for post-campaign flow
    """
    try:
        # Import database models
        from db.models import Report, ReportStatus, ScoringJob, ScoringResult, ScoringHistory, Campaign, CampaignStatus
        from db import SessionLocal
        
        # Get database session
        db = SessionLocal()
        
        # Get campaign metadata
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Find the report and update status to processing
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.campaign_id == campaign_id,
            Report.user_id == user_id
        ).first()
        
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        report.status = ReportStatus.PROCESSING
        db.commit()
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Reading file..."}
        )
        
        # Read the uploaded file (handle both local and S3 paths)
        if file_path.startswith('s3://'):
            # Handle S3 file
            import boto3
            from io import BytesIO
            
            # Parse S3 path
            s3_path = file_path.replace('s3://', '')
            bucket_name = s3_path.split('/')[0]
            key = '/'.join(s3_path.split('/')[1:])
            
            # Download from S3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            file_content = response['Body'].read()
            
            # Read file based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(BytesIO(file_content))
            elif file_ext == '.json':
                df = pd.read_json(BytesIO(file_content))
            elif file_ext == '.parquet':
                df = pd.read_parquet(BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        else:
            # Handle local file
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Preprocessing data..."}
        )
        
        # Preprocess the data
        processed_df = preprocess_data(df)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Calculating scores..."}
        )
        
        # Initialize scoring engine
        scoring_engine = ScoringEngine()
        
        # Prepare scoring configuration with campaign metadata
        scoring_config = {
            "campaign_metadata": {
                "goal": campaign.scoring_criteria.get("goal", "awareness") if isinstance(campaign.scoring_criteria, dict) else "awareness",
                "channel": campaign.scoring_criteria.get("channel", "display") if isinstance(campaign.scoring_criteria, dict) else "display",
                "ctr_sensitivity": campaign.scoring_criteria.get("ctr_sensitivity", True) if isinstance(campaign.scoring_criteria, dict) else True,
                "analysis_level": campaign.scoring_criteria.get("analysis_level", "domain") if isinstance(campaign.scoring_criteria, dict) else "domain"
            },
            "normalization": {"method": "z_score"},
            "outlier_detection": {"method": "iqr", "action": "mark"},
            "weighting": {"strategy": "linear"}
        }
        
        # Calculate scores using the enhanced scoring engine
        scoring_results = scoring_engine.calculate_scores(processed_df, campaign_id, scoring_config)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Generating insights..."}
        )
        
        # Generate AI insights
        insights = generate_openai_insights(scoring_results['scored_dataframe'], campaign_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Saving results..."}
        )
        
        # Save scoring results to database
        scored_df = scoring_results['scored_dataframe']
        
        # Clear existing scoring results for this report
        db.query(ScoringResult).filter(ScoringResult.report_id == report.id).delete()
        
        # Save individual metric results
        for index, row in scored_df.iterrows():
            # Get component scores from the scoring results
            for metric_name in scoring_results['metadata'].get('weighting_summary', {}).get('metrics', []):
                if f"{metric_name}_score" in row:
                    scoring_result = ScoringResult(
                        report_id=report.id,
                        metric_name=metric_name,
                        metric_value=row.get(metric_name, None),
                        score=row[f"{metric_name}_score"],
                        weight=scoring_results['metadata']['weighting_summary']['weights'].get(metric_name, 1.0),
                        weighted_score=row[f"{metric_name}_score"] * scoring_results['metadata']['weighting_summary']['weights'].get(metric_name, 1.0),
                        explanation=scoring_results['explanation'].get(metric_name, None),
                        metric_metadata={
                            'outlier_flag': row.get(f"{metric_name}_outlier", False),
                            'normalized_value': row.get(f"{metric_name}_normalized", None)
                        }
                    )
                    db.add(scoring_result)
        
        # Update report with results
        if report:
            report.status = ReportStatus.COMPLETED
            report.score_data = {
                "scores": scored_df['final_score'].to_dict(),
                "insights": insights,
                "metadata": scoring_results['metadata'],
                "campaign_metadata": scoring_config["campaign_metadata"]
            }
            report.processed_at = datetime.utcnow()
        
        # Update campaign status to completed and update statistics
        campaign.status = CampaignStatus.COMPLETED
        campaign.average_score = float(scored_df['final_score'].mean())
        campaign.total_submissions = len(scored_df)
        campaign.updated_at = datetime.utcnow()
        
        # Create scoring history entry
        history_entry = ScoringHistory(
            campaign_id=campaign_id,
            report_id=report.id,
            scoring_job_id=None,  # We'll create a scoring job record if needed
            version="1.0",
            config_snapshot=scoring_config,
            results_summary={
                "total_records": len(scored_df),
                "average_score": float(scored_df['final_score'].mean()),
                "score_range": f"{scored_df['final_score'].min():.2f} - {scored_df['final_score'].max():.2f}",
                "campaign_goal": scoring_config["campaign_metadata"]["goal"],
                "campaign_channel": scoring_config["campaign_metadata"]["channel"]
            },
            performance_metrics={
                "processing_time": scoring_results['metadata']['processing_time'],
                "memory_usage": "N/A"  # Could be enhanced with actual memory tracking
            }
        )
        db.add(history_entry)
        
        db.commit()
        
        results = {
            "scores": scored_df['final_score'].to_dict(),
            "insights": insights,
            "metadata": scoring_results['metadata'],
            "campaign_metadata": scoring_config["campaign_metadata"],
            "processed_at": datetime.utcnow().isoformat(),
            "file_path": file_path,
            "campaign_id": campaign_id,
            "user_id": user_id,
            "report_id": report_id
        }
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Processing completed"}
        )
        
        db.close()
        return results
        
    except Exception as e:
        # Update report status to failed
        try:
            from db.models import Report, ReportStatus
            from db import SessionLocal
            
            db = SessionLocal()
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = ReportStatus.FAILED
                db.commit()
            db.close()
        except:
            pass
        
        # Re-raise the exception
        raise

@celery.task(bind=True)
def process_file(self, file_path, campaign_id, user_id, job_id=None):
    """
    Legacy background task to process uploaded files and generate scores
    """
    try:
        # Import database models
        from db.models import Report, ReportStatus, ScoringJob, ScoringResult, ScoringHistory
        from db import SessionLocal
        
        # Get database session
        db = SessionLocal()
        
        # Find the scoring job if job_id is provided
        scoring_job = None
        if job_id:
            scoring_job = db.query(ScoringJob).filter(ScoringJob.id == job_id).first()
            if scoring_job:
                scoring_job.status = ReportStatus.PROCESSING
                scoring_job.started_at = datetime.utcnow()
                db.commit()
        
        # Find the report by file_path and update status to processing
        report = db.query(Report).filter(
            Report.file_path == file_path,
            Report.campaign_id == campaign_id,
            Report.user_id == user_id
        ).first()
        
        if report:
            report.status = ReportStatus.PROCESSING
            db.commit()
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Reading file..."}
        )
        
        # Read the uploaded file (handle both local and S3 paths)
        if file_path.startswith('s3://'):
            # Handle S3 file
            import boto3
            from io import BytesIO
            
            # Parse S3 path
            s3_path = file_path.replace('s3://', '')
            bucket_name = s3_path.split('/')[0]
            key = '/'.join(s3_path.split('/')[1:])
            
            # Download from S3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            file_content = response['Body'].read()
            
            # Read CSV from memory
            df = pd.read_csv(BytesIO(file_content))
        else:
            # Handle local file
            df = pd.read_csv(file_path)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Preprocessing data..."}
        )
        
        # Preprocess the data
        processed_df = preprocess_data(df)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Calculating scores..."}
        )
        
        # Initialize scoring engine
        scoring_engine = ScoringEngine()
        
        # Get scoring configuration from job or campaign
        config = None
        if scoring_job and scoring_job.config:
            config = scoring_job.config
        
        # Calculate scores using the enhanced scoring engine
        scoring_results = scoring_engine.calculate_scores(processed_df, campaign_id, config)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Generating insights..."}
        )
        
        # Generate AI insights
        insights = generate_openai_insights(scoring_results['scored_dataframe'], campaign_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Saving results..."}
        )
        
        # Save scoring results to database
        scored_df = scoring_results['scored_dataframe']
        
        # Clear existing scoring results for this report
        db.query(ScoringResult).filter(ScoringResult.report_id == report.id).delete()
        
        # Save individual metric results
        for index, row in scored_df.iterrows():
            # Get component scores from the scoring results
            for metric_name in scoring_results['metadata'].get('weighting_summary', {}).get('metrics', []):
                if f"{metric_name}_score" in row:
                    scoring_result = ScoringResult(
                        report_id=report.id,
                        metric_name=metric_name,
                        metric_value=row.get(metric_name, None),
                        score=row[f"{metric_name}_score"],
                        weight=scoring_results['metadata']['weighting_summary']['weights'].get(metric_name, 1.0),
                        weighted_score=row[f"{metric_name}_score"] * scoring_results['metadata']['weighting_summary']['weights'].get(metric_name, 1.0),
                        explanation=scoring_results['explanation'].get(metric_name, None),
                        metric_metadata={
                            'outlier_flag': row.get(f"{metric_name}_outlier", False),
                            'normalized_value': row.get(f"{metric_name}_normalized", None)
                        }
                    )
                    db.add(scoring_result)
        
        # Update report with results
        if report:
            report.status = ReportStatus.COMPLETED
            report.score_data = {
                "scores": scored_df['final_score'].to_dict(),
                "insights": insights,
                "metadata": scoring_results['metadata']
            }
            report.processed_at = datetime.utcnow()
        
        # Update scoring job
        if scoring_job:
            scoring_job.status = ReportStatus.COMPLETED
            scoring_job.progress = 100.0
            scoring_job.completed_at = datetime.utcnow()
        
        # Create scoring history entry
        if scoring_job:
            history_entry = ScoringHistory(
                campaign_id=campaign_id,
                report_id=report.id,
                scoring_job_id=scoring_job.id,
                version="1.0",
                config_snapshot=config,
                results_summary={
                    "total_records": len(scored_df),
                    "average_score": float(scored_df['final_score'].mean()),
                    "score_range": f"{scored_df['final_score'].min():.2f} - {scored_df['final_score'].max():.2f}"
                },
                performance_metrics={
                    "processing_time": scoring_results['metadata']['processing_time'],
                    "memory_usage": "N/A"  # Could be enhanced with actual memory tracking
                }
            )
            db.add(history_entry)
        
        db.commit()
        
        results = {
            "scores": scored_df['final_score'].to_dict(),
            "insights": insights,
            "metadata": scoring_results['metadata'],
            "processed_at": datetime.utcnow().isoformat(),
            "file_path": file_path,
            "campaign_id": campaign_id,
            "user_id": user_id,
            "job_id": job_id
        }
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Processing completed"}
        )
        
        db.close()
        return results
        
    except Exception as e:
        # Update report status to failed
        try:
            from db.models import Report, ReportStatus
            from db import SessionLocal
            
            db = SessionLocal()
            report = db.query(Report).filter(
                Report.file_path == file_path,
                Report.campaign_id == campaign_id,
                Report.user_id == user_id
            ).first()
            if report:
                report.status = ReportStatus.FAILED
                db.commit()
            db.close()
        except:
            pass
        
        # Re-raise the exception
        raise

@celery.task
def batch_process_files(file_paths, campaign_id, user_id, config=None):
    """
    Batch process multiple files for scoring
    """
    try:
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                # Process each file individually
                result = process_file.delay(file_path, campaign_id, user_id)
                results.append({
                    "file_path": file_path,
                    "task_id": result.id,
                    "status": "queued"
                })
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "total_files": total_files,
            "queued_files": len([r for r in results if r["status"] == "queued"]),
            "failed_files": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    except Exception as e:
        return {"error": str(e)}

@celery.task
def compare_scoring_methods(file_path, campaign_id, user_id, configs):
    """
    Compare different scoring configurations on the same dataset
    """
    try:
        from db.models import Report, ScoringJob, ScoringHistory
        from db import SessionLocal
        
        db = SessionLocal()
        
        # Read the file
        df = pd.read_csv(file_path)
        processed_df = preprocess_data(df)
        
        comparison_results = {}
        scoring_engine = ScoringEngine()
        
        for i, config in enumerate(configs):
            try:
                # Calculate scores with this configuration
                results = scoring_engine.calculate_scores(processed_df, campaign_id, config)
                
                comparison_results[f"method_{i+1}"] = {
                    "config": config,
                    "average_score": results['metadata']['average_score'],
                    "score_range": results['metadata']['score_range'],
                    "processing_time": results['metadata']['processing_time'],
                    "outlier_summary": results['metadata']['outlier_summary']
                }
                
            except Exception as e:
                comparison_results[f"method_{i+1}"] = {
                    "error": str(e),
                    "config": config
                }
        
        # Create comparison job record
        comparison_job = ScoringJob(
            report_id=1,  # This would need to be determined based on the file
            campaign_id=campaign_id,
            user_id=user_id,
            job_type="comparison",
            config={"comparison_configs": configs},
            status=ReportStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        
        db.add(comparison_job)
        db.commit()
        
        db.close()
        return comparison_results
        
    except Exception as e:
        return {"error": str(e)}

@celery.task
def generate_report_pdf(report_id):
    """
    Background task to generate PDF reports
    """
    try:
        # Get storage paths from settings
        from config.settings import get_storage_paths
        storage_paths = get_storage_paths()
        reports_path = storage_paths["reports"]
        
        # Ensure reports directory exists
        os.makedirs(reports_path, exist_ok=True)
        
        # Generate PDF report logic here
        # This would use reportlab or similar library
        pdf_path = os.path.join(reports_path, f"{report_id}.pdf")
        
        return {"status": "success", "pdf_path": pdf_path}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@celery.task
def cleanup_old_scoring_jobs(days_old=30):
    """
    Clean up old scoring jobs and history
    """
    try:
        from db.models import ScoringJob, ScoringHistory
        from db import SessionLocal
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Delete old completed jobs
        old_jobs = db.query(ScoringJob).filter(
            ScoringJob.status == ReportStatus.COMPLETED,
            ScoringJob.completed_at < cutoff_date
        ).all()
        
        for job in old_jobs:
            db.delete(job)
        
        # Delete old history entries
        old_history = db.query(ScoringHistory).filter(
            ScoringHistory.created_at < cutoff_date
        ).all()
        
        for history in old_history:
            db.delete(history)
        
        db.commit()
        db.close()
        
        return {
            "deleted_jobs": len(old_jobs),
            "deleted_history": len(old_history),
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)} 
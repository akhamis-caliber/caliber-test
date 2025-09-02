"""
Report upload controller for handling file uploads and processing
"""

import os
import uuid
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from db.models import Report, Campaign, ReportStatus
from config.settings import settings
from common.exceptions import ValidationError, NotFoundError
from worker.tasks import score_report
import logging

logger = logging.getLogger(__name__)


class ReportUploadController:
    def __init__(self, db: Session):
        self.db = db

    async def upload_file(
        self, file: UploadFile, campaign_id: str, org_id: str
    ) -> Dict[str, Any]:
        """Handle file upload and validation"""
        
        # Validate campaign exists and belongs to org
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.org_id == org_id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign not found")
        
        # Validate file type
        allowed_types = ['.csv', '.xlsx', '.xls']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_types:
            raise ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Create storage directory
        report_id = str(uuid.uuid4())
        storage_dir = Path(settings.STORAGE_ROOT) / str(org_id) / report_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = storage_dir / file.filename
        storage_path = str(Path(str(org_id)) / report_id / file.filename)
        
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Read and validate file
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            raise ValidationError(f"Failed to read file: {str(e)}")
        
        # Validate required columns
        required_columns = ['domain', 'impressions', 'ctr', 'conversions', 'total_spend']
        validation_errors = []
        
        # Normalize column names for checking
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        missing_columns = []
        for required_col in required_columns:
            variants = self._get_column_variants(required_col)
            if not any(variant in df_columns_lower for variant in variants):
                missing_columns.append(required_col)
        
        if missing_columns:
            validation_errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for empty dataframe
        if len(df) == 0:
            validation_errors.append("File contains no data rows")
        
        # Create report record
        report = Report(
            id=report_id,
            campaign_id=campaign_id,
            filename=file.filename,
            storage_path=storage_path,
            status=ReportStatus.UPLOADED
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        # Generate preview data
        preview_data = []
        if len(df) > 0:
            preview_df = df.head(50)  # First 50 rows for preview
            preview_data = preview_df.to_dict('records')
        
        logger.info(f"Uploaded report {report_id}: {file.filename} ({len(df)} rows)")
        
        return {
            "report_id": report_id,
            "filename": file.filename,
            "rows_count": len(df),
            "columns": list(df.columns),
            "preview_data": preview_data,
            "validation_errors": validation_errors
        }
    
    def _get_column_variants(self, column: str) -> List[str]:
        """Get possible variants of column names"""
        variants_map = {
            'domain': ['domain', 'domains', 'site', 'website', 'url'],
            'impressions': ['impressions', 'impression', 'imps', 'views'],
            'ctr': ['ctr', 'click_through_rate', 'clickthrough_rate', 'click_rate'],
            'conversions': ['conversions', 'conversion', 'conv', 'actions'],
            'total_spend': ['total_spend', 'spend', 'cost', 'total_cost', 'budget']
        }
        return variants_map.get(column, [column])
    
    def start_scoring(self, report_id: str, org_id: str) -> Dict[str, Any]:
        """Start the scoring process for a report"""
        
        # Validate report exists and belongs to org
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        if report.status != ReportStatus.UPLOADED:
            raise ValidationError(f"Report is not in uploaded status: {report.status}")
        
        # Start background scoring task
        task = score_report.delay(report_id)
        
        logger.info(f"Started scoring for report {report_id}, task: {task.id}")
        
        return {
            "report_id": report_id,
            "message": "Scoring started successfully",
            "task_id": task.id
        }
    
    def get_report(self, report_id: str, org_id: str) -> Dict[str, Any]:
        """Get report details"""
        
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        return {
            "id": str(report.id),
            "campaign_id": str(report.campaign_id),
            "filename": report.filename,
            "uploaded_at": report.uploaded_at,
            "status": report.status,
            "summary_json": report.summary_json,
            "error_message": report.error_message,
            "rows_count": len(report.score_rows) if report.score_rows else None
        }
    
    def get_report_rows(
        self,
        report_id: str,
        org_id: str,
        skip: int = 0,
        limit: int = 50,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        publisher: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get paginated and filtered score rows"""
        
        from db.models import ScoreRow
        
        # Validate report exists and belongs to org
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        # Build query with filters
        query = self.db.query(ScoreRow).filter(ScoreRow.report_id == report_id)
        
        if min_score is not None:
            query = query.filter(ScoreRow.score >= min_score)
        
        if max_score is not None:
            query = query.filter(ScoreRow.score <= max_score)
        
        if status:
            query = query.filter(ScoreRow.status == status)
        
        if channel:
            query = query.filter(ScoreRow.channel.ilike(f'%{channel}%'))
        
        if publisher:
            query = query.filter(ScoreRow.publisher.ilike(f'%{publisher}%'))
        
        if vendor:
            query = query.filter(ScoreRow.vendor.ilike(f'%{vendor}%'))
        
        # Execute query with pagination
        rows = query.order_by(ScoreRow.score.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": str(row.id),
                "domain": row.domain,
                "publisher": row.publisher,
                "cpm": row.cpm,
                "ctr": row.ctr,
                "conversion_rate": row.conversion_rate,
                "impressions": row.impressions,
                "total_spend": row.total_spend,
                "conversions": row.conversions,
                "score": row.score,
                "status": row.status,
                "channel": row.channel,
                "vendor": row.vendor,
                "explanation": row.explanation
            }
            for row in rows
        ]
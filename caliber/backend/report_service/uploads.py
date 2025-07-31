from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
import pandas as pd
from datetime import datetime
import logging

from db.models import FileUpload, Campaign, User
from common.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class FileUploadService:
    """Service for managing file uploads and validation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_upload_record(
        self,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
        file_size: int,
        campaign_id: Optional[uuid.UUID] = None
    ) -> FileUpload:
        """Create a new file upload record"""
        
        upload_record = FileUpload(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            campaign_id=campaign_id,
            upload_date=datetime.utcnow(),
            status="uploaded"
        )
        
        self.db.add(upload_record)
        self.db.commit()
        self.db.refresh(upload_record)
        
        logger.info(f"Created upload record for file: {filename}")
        return upload_record
    
    def get_file_info(self, file_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get file information"""
        
        upload_record = self.db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == user_id
        ).first()
        
        if not upload_record:
            raise NotFoundError("File upload record")
        
        return {
            "id": upload_record.id,
            "filename": upload_record.filename,
            "file_path": upload_record.file_path,
            "file_size": upload_record.file_size,
            "campaign_id": upload_record.campaign_id,
            "upload_date": upload_record.upload_date,
            "status": upload_record.status
        }
    
    def get_user_files(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """Get paginated list of user's uploaded files"""
        
        offset = (page - 1) * per_page
        
        uploads = self.db.query(FileUpload).filter(
            FileUpload.user_id == user_id
        ).order_by(FileUpload.upload_date.desc()).offset(offset).limit(per_page).all()
        
        return [
            {
                "id": upload.id,
                "filename": upload.filename,
                "file_size": upload.file_size,
                "campaign_id": upload.campaign_id,
                "upload_date": upload.upload_date,
                "status": upload.status
            }
            for upload in uploads
        ]
    
    def validate_file_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate file structure and content"""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "column_count": len(df.columns),
            "row_count": len(df),
            "columns": df.columns.tolist(),
            "data_types": df.dtypes.to_dict()
        }
        
        # Check for required columns (basic validation)
        required_columns = ["impressions", "ctr"]
        missing_columns = [col for col in required_columns if col.lower() not in [c.lower() for c in df.columns]]
        
        if missing_columns:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Missing required columns: {missing_columns}")
        
        # Check for empty dataframe
        if len(df) == 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("File is empty")
        
        # Check for too many columns (potential data quality issue)
        if len(df.columns) > 50:
            validation_result["warnings"].append("File has many columns - may contain unnecessary data")
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            validation_result["warnings"].append("File contains duplicate column names")
        
        # Check for missing values in critical columns
        if "impressions" in df.columns:
            missing_impressions = df["impressions"].isna().sum()
            if missing_impressions > 0:
                validation_result["warnings"].append(f"Found {missing_impressions} rows with missing impressions")
        
        return validation_result
    
    def delete_file(self, file_id: uuid.UUID, user_id: uuid.UUID):
        """Delete file upload record"""
        
        upload_record = self.db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == user_id
        ).first()
        
        if not upload_record:
            raise NotFoundError("File upload record")
        
        # Delete the file from storage (this would be implemented in file_storage)
        # await file_storage.delete_file(upload_record.file_path)
        
        # Delete the database record
        self.db.delete(upload_record)
        self.db.commit()
        
        logger.info(f"Deleted file upload record: {file_id}")
    
    def assign_file_to_campaign(
        self,
        file_id: uuid.UUID,
        campaign_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Assign uploaded file to a campaign"""
        
        # Verify file exists and belongs to user
        upload_record = self.db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == user_id
        ).first()
        
        if not upload_record:
            raise NotFoundError("File upload record")
        
        # Verify campaign exists and belongs to user
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Update the upload record
        upload_record.campaign_id = campaign_id
        upload_record.status = "assigned"
        self.db.commit()
        
        logger.info(f"Assigned file {file_id} to campaign {campaign_id}")
        
        return {
            "file_id": file_id,
            "campaign_id": campaign_id,
            "status": "assigned"
        }
    
    def get_campaign_files(
        self,
        campaign_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get files associated with a campaign"""
        
        # Verify campaign exists and belongs to user
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Get files for the campaign
        uploads = self.db.query(FileUpload).filter(
            FileUpload.campaign_id == campaign_id,
            FileUpload.user_id == user_id
        ).order_by(FileUpload.upload_date.desc()).all()
        
        return [
            {
                "id": upload.id,
                "filename": upload.filename,
                "file_size": upload.file_size,
                "upload_date": upload.upload_date,
                "status": upload.status
            }
            for upload in uploads
        ]


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import pandas as pd
import io

from config.database import get_db
from auth_service.dependencies import get_current_user
from report_service.storage import file_storage
from report_service.uploads import FileUploadService
from report_service.exports import ExportService
from report_service.pdf_generator import PDFReportGenerator
from common.exceptions import ValidationError, NotFoundError
from common.schemas import BaseResponse

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    campaign_id: Optional[uuid.UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload a file for processing"""
    try:
        # Validate file
        if not file.filename:
            raise ValidationError("No file provided")
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = file.filename.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise ValidationError(f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise ValidationError("File too large. Maximum size is 50MB")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        
        # Store file
        file_path = await file_storage.save_file(file_content, filename)
        
        # Create upload record
        upload_service = FileUploadService(db)
        upload_record = upload_service.create_upload_record(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            campaign_id=campaign_id
        )
        
        return {
            "upload_id": upload_record.id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": len(file_content),
            "campaign_id": campaign_id,
            "status": "uploaded"
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files", response_model=List[Dict[str, Any]])
async def list_files(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List uploaded files for the current user"""
    try:
        upload_service = FileUploadService(db)
        files = upload_service.get_user_files(
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}", response_model=Dict[str, Any])
async def get_file_info(
    file_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get file information"""
    try:
        upload_service = FileUploadService(db)
        file_info = upload_service.get_file_info(file_id, current_user.id)
        return file_info
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/preview", response_model=Dict[str, Any])
async def preview_file(
    file_id: uuid.UUID = Path(...),
    rows: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Preview file contents"""
    try:
        upload_service = FileUploadService(db)
        file_info = upload_service.get_file_info(file_id, current_user.id)
        
        # Read file content
        file_content = file_storage.read_file(file_info["file_path"])
        
        # Parse based on file type
        if file_info["filename"].endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content), nrows=rows)
        else:
            df = pd.read_excel(io.BytesIO(file_content), nrows=rows)
        
        # Convert to dict for JSON response
        preview_data = {
            "columns": df.columns.tolist(),
            "rows": df.head(rows).to_dict('records'),
            "total_rows": len(df),
            "file_info": file_info
        }
        
        return preview_data
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/validate", response_model=Dict[str, Any])
async def validate_file(
    file_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Validate file structure and content"""
    try:
        upload_service = FileUploadService(db)
        file_info = upload_service.get_file_info(file_id, current_user.id)
        
        # Read file content
        file_content = file_storage.read_file(file_info["file_path"])
        
        # Parse file
        if file_info["filename"].endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        else:
            df = pd.read_excel(io.BytesIO(file_content))
        
        # Perform validation
        validation_result = upload_service.validate_file_structure(df)
        
        return {
            "file_id": file_id,
            "validation_result": validation_result,
            "file_info": file_info
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}", response_model=BaseResponse)
async def delete_file(
    file_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete uploaded file"""
    try:
        upload_service = FileUploadService(db)
        upload_service.delete_file(file_id, current_user.id)
        
        return BaseResponse(
            success=True,
            message="File deleted successfully"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files/{file_id}/assign-campaign", response_model=Dict[str, Any])
async def assign_file_to_campaign(
    file_id: uuid.UUID = Path(...),
    campaign_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Assign uploaded file to a campaign"""
    try:
        upload_service = FileUploadService(db)
        result = upload_service.assign_file_to_campaign(
            file_id=file_id,
            campaign_id=campaign_id,
            user_id=current_user.id
        )
        
        return {
            "file_id": file_id,
            "campaign_id": campaign_id,
            "status": "assigned"
        }
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/files", response_model=List[Dict[str, Any]])
async def get_campaign_files(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get files associated with a campaign"""
    try:
        upload_service = FileUploadService(db)
        files = upload_service.get_campaign_files(campaign_id, current_user.id)
        return files
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export Routes
@router.get("/export/campaigns/{campaign_id}/results/csv")
async def export_scoring_results_csv(
    campaign_id: uuid.UUID = Path(...),
    quality_status: Optional[str] = Query(None, regex="^(good|moderate|poor)$"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    min_impressions: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export scoring results to CSV"""
    try:
        export_service = ExportService(db)
        
        # Build filters
        filters = {}
        if quality_status:
            filters["quality_status"] = quality_status
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score
        if min_impressions is not None:
            filters["min_impressions"] = min_impressions
        
        csv_data = export_service.export_scoring_results_csv(
            campaign_id=str(campaign_id),
            user=current_user,
            filters=filters
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=scoring_results_{campaign_id}.csv"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/whitelist/csv")
async def export_whitelist_csv(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export whitelist to CSV"""
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_whitelist_csv(
            campaign_id=str(campaign_id),
            user=current_user,
            min_impressions=min_impressions
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=whitelist_{campaign_id}.csv"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/blacklist/csv")
async def export_blacklist_csv(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export blacklist to CSV"""
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_blacklist_csv(
            campaign_id=str(campaign_id),
            user=current_user,
            min_impressions=min_impressions
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=blacklist_{campaign_id}.csv"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/summary/csv")
async def export_campaign_summary_csv(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export campaign summary to CSV"""
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_campaign_summary_csv(
            campaign_id=str(campaign_id),
            user=current_user
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=campaign_summary_{campaign_id}.csv"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/optimization-lists/csv")
async def export_optimization_lists_csv(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export both whitelist and blacklist to CSV"""
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_optimization_lists_csv(
            campaign_id=str(campaign_id),
            user=current_user,
            min_impressions=min_impressions
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=optimization_lists_{campaign_id}.csv"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/whitelist/json")
async def export_whitelist_json(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export whitelist in JSON format"""
    try:
        export_service = ExportService(db)
        json_data = export_service.generate_whitelist_json(
            campaign_id=str(campaign_id),
            user=current_user,
            min_impressions=min_impressions
        )
        return json_data
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/blacklist/json")
async def export_blacklist_json(
    campaign_id: uuid.UUID = Path(...),
    min_impressions: int = Query(250, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export blacklist in JSON format"""
    try:
        export_service = ExportService(db)
        json_data = export_service.generate_blacklist_json(
            campaign_id=str(campaign_id),
            user=current_user,
            min_impressions=min_impressions
        )
        return json_data
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/campaigns/{campaign_id}/data/json")
async def export_campaign_data_json(
    campaign_id: uuid.UUID = Path(...),
    include_results: bool = Query(True),
    include_insights: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export complete campaign data in JSON format"""
    try:
        export_service = ExportService(db)
        json_data = export_service.export_campaign_data_json(
            campaign_id=str(campaign_id),
            user=current_user,
            include_results=include_results,
            include_insights=include_insights
        )
        return json_data
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PDF Report Routes
@router.get("/reports/campaigns/{campaign_id}/pdf")
async def generate_campaign_pdf_report(
    campaign_id: uuid.UUID = Path(...),
    include_charts: bool = Query(True),
    include_details: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate comprehensive PDF report for campaign"""
    try:
        pdf_generator = PDFReportGenerator(db)
        pdf_data = pdf_generator.generate_campaign_report(
            campaign_id=str(campaign_id),
            user=current_user,
            include_charts=include_charts,
            include_details=include_details
        )
        
        from fastapi.responses import Response
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=campaign_report_{campaign_id}.pdf"
            }
        )
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
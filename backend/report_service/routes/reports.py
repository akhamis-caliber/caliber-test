from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Response, Query
from fastapi.responses import StreamingResponse
from report_service.uploads import validate_file, save_file, queue_file_processing, validate_dataset_columns, validate_data_types, normalize_column_names
from report_service.exports import export_service
from report_service.pdf_generator import pdf_generator
from db.models import Report, ReportStatus, Campaign
from config.database import SessionLocal
from auth_service.middleware import get_current_user
from auth_service.models.user import User
from sqlalchemy.orm import Session
import json
import io
import os
import pandas as pd
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This function is now imported from uploads.py

def save_file_to_local(df: pd.DataFrame, filename: str, file_ext: str) -> str:
    """Save DataFrame to local file system"""
    UPLOAD_FOLDER = "uploads" # Assuming this is defined elsewhere or needs to be added
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if file_ext == '.csv':
        df.to_csv(file_path, index=False)
    elif file_ext == '.json':
        df.to_json(file_path, orient='records', indent=2)
    elif file_ext == '.parquet':
        df.to_parquet(file_path, index=False)
    elif file_ext in ['.xls', '.xlsx']:
        df.to_excel(file_path, index=False)
    
    return file_path

@router.post("/reports/upload")
async def upload_report(
    file: UploadFile = File(...),
    campaign_id: Optional[str] = Form(None),  # Changed to str to handle form data
    user_id: Optional[str] = Form(None),      # Changed to str to handle form data
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload dataset for campaign scoring with enhanced validation"""
    
    # Convert string parameters to integers if provided
    campaign_id_int = None
    user_id_int = None
    
    if campaign_id is not None:
        try:
            campaign_id_int = int(campaign_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid campaign_id format")
    
    if user_id is not None:
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid user_id format")
    
    # Use current_user.id if user_id not provided
    if user_id_int is None:
        user_id_int = current_user.id
    
    # Validate file type
    allowed_types = ['.csv', '.json', '.parquet', '.xls', '.xlsx']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    # Validate campaign exists and belongs to user if campaign_id provided
    campaign = None
    campaign_metadata = None
    if campaign_id_int:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id_int,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Extract campaign metadata for validation
        if campaign.scoring_criteria and isinstance(campaign.scoring_criteria, dict):
            campaign_metadata = campaign.scoring_criteria
    
    # Save file and create report
    filename = validate_file(file)
    file_path = save_file(file, filename)
    
    # Read and validate dataset
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        elif file_ext == '.parquet':
            df = pd.read_parquet(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        
        # Enhanced column validation
        column_validation = validate_dataset_columns(df, campaign_metadata)
        
        if not column_validation["valid"]:
            # Clean up the saved file if validation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400, 
                detail=f"Dataset validation failed: {'; '.join(column_validation['suggestions'])}"
            )
        
        # Data type validation
        data_type_validation = validate_data_types(df)
        if not data_type_validation["valid"]:
            # Clean up the saved file if validation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Data type validation failed: {'; '.join(data_type_validation['suggestions'])}"
            )
        
        # Normalize column names if mapping is available
        if column_validation["column_mapping"]:
            df_normalized = normalize_column_names(df, column_validation["column_mapping"])
            # Save normalized version
            normalized_filename = f"normalized_{filename}"
            normalized_file_path = save_file_to_local(df_normalized, normalized_filename, file_ext)
            file_path = normalized_file_path
            filename = normalized_filename
        
    except Exception as e:
        # Clean up the saved file if validation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Dataset validation failed: {str(e)}")
    
    # Create a report record in DB
    report = Report(
        title=filename,
        filename=filename,
        file_path=file_path,
        file_size=file.size,
        file_type=file_ext[1:],  # Remove dot
        campaign_id=campaign_id_int,
        user_id=user_id_int,
        status=ReportStatus.QUEUED
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Queue processing if campaign_id is provided
    task_id = None
    if campaign_id_int:
        try:
            task_id = queue_file_processing(file_path, campaign_id_int, user_id_int, report.id)
            if task_id:
                report.task_id = task_id
                db.commit()
                print(f"File processing queued with task ID: {task_id}")
            else:
                print("Warning: File processing could not be queued")
        except Exception as e:
            print(f"Error queuing file processing: {e}")
            # Don't fail the upload if processing queuing fails
            task_id = None
    
    return {
        "report_id": report.id,
        "task_id": task_id,
        "filename": filename,
        "campaign_id": campaign_id_int,
        "status": "uploaded",
        "message": "File uploaded successfully. Processing in progress..." if task_id else "File uploaded successfully.",
        "validation": {
            "column_validation": column_validation,
            "data_type_validation": data_type_validation
        }
    }

@router.post("/reports/batch-upload")
async def batch_upload_reports(
    files: List[UploadFile] = File(...),
    campaign_id: Optional[str] = Form(None),  # Changed to str to handle form data
    user_id: Optional[str] = Form(None),      # Changed to str to handle form data
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple datasets for batch processing"""
    
    # Convert string parameters to integers if provided
    campaign_id_int = None
    user_id_int = None
    
    if campaign_id is not None:
        try:
            campaign_id_int = int(campaign_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid campaign_id format")
    
    if user_id is not None:
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid user_id format")
    
    # Use current_user.id if user_id not provided
    if user_id_int is None:
        user_id_int = current_user.id
    
    # Validate campaign exists and belongs to user if campaign_id provided
    campaign = None
    campaign_metadata = None
    if campaign_id_int:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id_int,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Extract campaign metadata for validation
        if campaign.scoring_criteria and isinstance(campaign.scoring_criteria, dict):
            campaign_metadata = campaign.scoring_criteria
    
    # Validate number of files
    if len(files) > 10:  # Limit to 10 files per batch
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch upload")
    
    batch_id = str(uuid.uuid4())
    results = []
    
    for i, file in enumerate(files):
        try:
            # Validate file type
            allowed_types = ['.csv', '.json', '.parquet', '.xls', '.xlsx']
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_types:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"Invalid file type. Allowed: {', '.join(allowed_types)}"
                })
                continue
            
            # Validate file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": "File too large. Max 10MB"
                })
                continue
            
            # Save file and create report
            filename = validate_file(file)
            file_path = save_file(file, filename)
            
            # Read and validate dataset
            try:
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                elif file_ext == '.json':
                    df = pd.read_json(file_path)
                elif file_ext == '.parquet':
                    df = pd.read_parquet(file_path)
                elif file_ext in ['.xls', '.xlsx']:
                    df = pd.read_excel(file_path)
                
                # Enhanced column validation
                column_validation = validate_dataset_columns(df, campaign_metadata)
                
                if not column_validation["valid"]:
                    # Clean up the saved file if validation fails
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": f"Dataset validation failed: {'; '.join(column_validation['suggestions'])}"
                    })
                    continue
                
                # Data type validation
                data_type_validation = validate_data_types(df)
                if not data_type_validation["valid"]:
                    # Clean up the saved file if validation fails
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": f"Data type validation failed: {'; '.join(data_type_validation['suggestions'])}"
                    })
                    continue
                
                # Normalize column names if mapping is available
                if column_validation["column_mapping"]:
                    df_normalized = normalize_column_names(df, column_validation["column_mapping"])
                    # Save normalized version
                    normalized_filename = f"normalized_{filename}"
                    normalized_file_path = save_file_to_local(df_normalized, normalized_filename, file_ext)
                    file_path = normalized_file_path
                    filename = normalized_filename
                
            except Exception as e:
                # Clean up the saved file if validation fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"Dataset validation failed: {str(e)}"
                })
                continue
            
            # Create a report record in DB
            report = Report(
                title=filename,
                filename=filename,
                file_path=file_path,
                file_size=file.size,
                file_type=file_ext[1:],  # Remove dot
                campaign_id=campaign_id_int,
                user_id=user_id_int,
                status=ReportStatus.QUEUED
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            # Queue processing if campaign_id is provided
            task_id = None
            if campaign_id_int:
                task_id = queue_file_processing(file_path, campaign_id_int, user_id_int, report.id)
                report.task_id = task_id
                db.commit()
            
            results.append({
                "filename": file.filename,
                "report_id": report.id,
                "task_id": task_id,
                "status": "uploaded",
                "message": "File uploaded successfully. Processing in progress..." if task_id else "File uploaded successfully.",
                "validation": {
                    "column_validation": column_validation,
                    "data_type_validation": data_type_validation
                }
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Upload failed: {str(e)}"
            })
    
    # Calculate batch statistics
    successful_uploads = len([r for r in results if r["status"] == "uploaded"])
    failed_uploads = len([r for r in results if r["status"] == "failed"])
    
    return {
        "batch_id": batch_id,
        "total_files": len(files),
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads,
        "campaign_id": campaign_id_int,
        "results": results
    }

@router.get("/reports/{id}/status")
async def get_report_status(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report processing status with progress tracking"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get progress from task if available
    progress = 0
    if report.task_id:
        try:
            from worker.celery import celery
            task_result = celery.AsyncResult(report.task_id)
            if task_result.info:
                progress = task_result.info.get("current", 0)
        except:
            pass
    
    return {
        "report_id": report.id,
        "status": report.status,
        "task_id": report.task_id,
        "progress": progress,
        "filename": report.filename,
        "created_at": report.created_at,
        "processed_at": report.processed_at
    }

@router.get("/reports")
async def list_reports(
    campaign_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List reports with filtering and pagination"""
    query = db.query(Report).filter(Report.user_id == current_user.id)
    
    if campaign_id:
        query = query.filter(Report.campaign_id == campaign_id)
    
    if status:
        query = query.filter(Report.status == status)
    
    total = query.count()
    reports = query.offset(skip).limit(limit).all()
    
    return {
        "reports": [
            {
                "id": r.id,
                "filename": r.filename,
                "status": r.status,
                "campaign_id": r.campaign_id,
                "file_size": r.file_size,
                "created_at": r.created_at,
                "processed_at": r.processed_at
            } for r in reports
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/reports/{id}")
async def get_report(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed report information"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "filename": report.filename,
        "title": report.title,
        "status": report.status,
        "file_size": report.file_size,
        "file_type": report.file_type,
        "campaign_id": report.campaign_id,
        "user_id": report.user_id,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
        "task_id": report.task_id,
        "score_data": report.score_data
    }

@router.get("/reports/{id}/data")
async def get_report_data(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processed report data with scoring results"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report processing not completed")
    
    # Return actual scoring data if available
    if report.score_data:
        return report.score_data
    
    # Fallback to mock data for development
    mock_data = {
        "overall_score": 87.5,
        "ctr_score": 92.3,
        "cpm_score": 78.1,
        "conversion_score": 85.7,
        "roas_score": 88.9,
        "audience_score": 82.4,
        "ctr": 2.5,
        "cpm": 15.2,
        "cpc": 0.85,
        "conversion_rate": 1.2,
        "roas": 3.8,
        "high_performing": 35,
        "medium_performing": 45,
        "low_performing": 20
    }
    
    return mock_data

@router.get("/reports/{id}/realtime")
async def get_real_time_data(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time data updates for a report"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Mock real-time data - in real implementation, this would come from live data sources
    import random
    from datetime import datetime
    
    mock_realtime_data = {
        "timestamp": datetime.now().isoformat(),
        "current_score": 87.5 + random.uniform(-2, 2),
        "impressions_today": random.randint(8000, 12000),
        "clicks_today": random.randint(200, 400),
        "conversions_today": random.randint(10, 25),
        "ctr_today": round(random.uniform(2.0, 3.5), 2),
        "cpm_today": round(random.uniform(12.0, 18.0), 2),
        "roas_today": round(random.uniform(3.0, 4.5), 2)
    }
    
    return mock_realtime_data

@router.post("/reports/{id}/export/{format_type}")
async def export_report(
    id: int, 
    format_type: str, 
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export report in specified format (pdf, excel, csv)"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format_type not in ['pdf', 'excel', 'csv']:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    try:
        # Get the data to export
        data = request_data.get('data', [])
        report_title = request_data.get('reportTitle', report.filename)
        
        # Generate export
        export_content = export_service.export_data(
            data=data,
            format_type=format_type,
            report_title=report_title
        )
        
        # Set appropriate headers
        if format_type == 'pdf':
            media_type = 'application/pdf'
            filename = f"{report_title.replace(' ', '_')}.pdf"
        elif format_type == 'excel':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{report_title.replace(' ', '_')}.xlsx"
        else:  # csv
            media_type = 'text/csv'
            filename = f"{report_title.replace(' ', '_')}.csv"
        
        # Create streaming response
        def generate():
            yield export_content
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/reports/{id}/export/pdf/advanced")
async def export_advanced_pdf(
    id: int,
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export advanced PDF with custom branding and configuration"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        # Get the data to export
        data = request_data.get('data', [])
        report_config = request_data.get('reportConfig', {})
        branding_config = request_data.get('brandingConfig', {})
        
        # Set default report config
        if not report_config.get('title'):
            report_config['title'] = report.filename
        
        # Generate PDF
        pdf_content = pdf_generator.generate_report(
            data=data,
            report_config=report_config,
            branding_config=branding_config
        )
        
        filename = f"{report_config['title'].replace(' ', '_')}_advanced.pdf"
        
        # Create streaming response
        def generate():
            yield pdf_content
        
        return StreamingResponse(
            generate(),
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.get("/reports/{id}/charts")
async def get_report_charts(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chart data for a report"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Mock chart data - in real implementation, this would be generated from actual data
    chart_data = {
        "score_trend": [
            {"date": "2024-01-01", "score": 75},
            {"date": "2024-01-02", "score": 78},
            {"date": "2024-01-03", "score": 82},
            {"date": "2024-01-04", "score": 85},
            {"date": "2024-01-05", "score": 87},
            {"date": "2024-01-06", "score": 89},
            {"date": "2024-01-07", "score": 92}
        ],
        "performance_metrics": [
            {"name": "CTR", "value": 2.5},
            {"name": "CPM", "value": 15.2},
            {"name": "CPC", "value": 0.85},
            {"name": "Conversion Rate", "value": 1.2},
            {"name": "ROAS", "value": 3.8}
        ],
        "distribution": [
            {"name": "High Performing", "value": 35},
            {"name": "Medium Performing", "value": 45},
            {"name": "Low Performing", "value": 20}
        ]
    }
    
    return chart_data

@router.get("/reports/{id}/insights")
async def get_report_insights(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated insights for a report"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Mock insights - in real implementation, this would come from AI analysis
    insights = {
        "performance_analysis": "Your campaign shows strong CTR performance but has room for improvement in CPM efficiency. Consider optimizing your targeting to reduce costs while maintaining quality.",
        "recommendations": [
            "Optimize bid strategies for better CPM control",
            "Test new audience segments to improve conversion rates",
            "Consider creative refresh to boost engagement"
        ],
        "key_findings": [
            "CTR performance is 15% above industry average",
            "CPM costs are 8% higher than target",
            "Conversion rates show positive trend over time"
        ],
        "risk_factors": [
            "High CPM may impact budget efficiency",
            "Seasonal fluctuations expected in Q2"
        ]
    }
    
    return insights

@router.put("/reports/{id}/link-campaign")
async def link_report_to_campaign(
    id: int, 
    campaign_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a report to a campaign"""
    report = db.query(Report).filter(
        Report.id == id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    campaign_id = campaign_data.get('campaign_id')
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")
    
    # Verify campaign belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update the report with the campaign ID
    report.campaign_id = campaign_id
    db.commit()
    db.refresh(report)
    
    return {
        "message": "Report linked to campaign successfully",
        "report_id": report.id,
        "campaign_id": report.campaign_id
    } 
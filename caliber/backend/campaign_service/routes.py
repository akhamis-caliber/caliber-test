from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from config.database import get_db
from auth_service.dependencies import get_current_user
from db.models import User
from campaign_service.controllers import CampaignController
from campaign_service.schemas import (
    CampaignCreate, CampaignTemplateCreate, CampaignStatus,
    CampaignResponse, CampaignTemplateResponse, CampaignListResponse
)
from common.schemas import APIResponse
from common.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])

# Template endpoints
@router.post("/templates", response_model=APIResponse)
async def create_template(
    template_data: CampaignTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign template"""
    try:
        template = CampaignController.create_template(
            db=db,
            template_data=template_data,
            user=current_user
        )
        return APIResponse(
            success=True,
            data=CampaignTemplateResponse.model_validate(template),
            message="Template created successfully"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@router.get("/templates", response_model=APIResponse)
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all templates for the current user"""
    try:
        templates = CampaignController.get_user_templates(db=db, user=current_user)
        return APIResponse(
            success=True,
            data=[CampaignTemplateResponse.model_validate(template) for template in templates]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/templates/{template_id}", response_model=APIResponse)
async def get_template(
    template_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID"""
    try:
        template = CampaignController.get_template_by_id(
            db=db, template_id=template_id, user=current_user
        )
        return APIResponse(
            success=True,
            data=CampaignTemplateResponse.model_validate(template)
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.delete("/templates/{template_id}", response_model=APIResponse)
async def delete_template(
    template_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    try:
        success = CampaignController.delete_template(
            db=db, template_id=template_id, user=current_user
        )
        if success:
            return APIResponse(
                success=True,
                message="Template deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Template not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")

# Campaign endpoints
@router.post("", response_model=APIResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign"""
    try:
        campaign = CampaignController.create_campaign(
            db=db,
            campaign_data=campaign_data,
            user=current_user
        )
        return APIResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="Campaign created successfully"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

@router.get("", response_model=APIResponse)
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[CampaignStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user campaigns with pagination and filtering"""
    try:
        campaigns, total = CampaignController.get_user_campaigns(
            db=db,
            user=current_user,
            skip=skip,
            limit=limit,
            status=status
        )
        
        return APIResponse(
            success=True,
            data=CampaignListResponse(
                campaigns=[CampaignResponse.model_validate(campaign) for campaign in campaigns],
                total=total
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaigns: {str(e)}")

@router.get("/{campaign_id}", response_model=APIResponse)
async def get_campaign(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific campaign by ID"""
    try:
        campaign = CampaignController.get_campaign_by_id(
            db=db, campaign_id=campaign_id, user=current_user
        )
        return APIResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign)
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaign: {str(e)}")

@router.put("/{campaign_id}/status", response_model=APIResponse)
async def update_campaign_status(
    campaign_id: uuid.UUID = Path(...),
    status: CampaignStatus = Query(...),
    error_message: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign status"""
    try:
        campaign = CampaignController.update_campaign_status(
            db=db,
            campaign_id=campaign_id,
            status=status,
            user=current_user,
            error_message=error_message
        )
        return APIResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="Campaign status updated successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign status: {str(e)}")

@router.put("/{campaign_id}/progress", response_model=APIResponse)
async def update_campaign_progress(
    campaign_id: uuid.UUID = Path(...),
    processed_records: int = Query(..., ge=0),
    total_records: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign processing progress"""
    try:
        campaign = CampaignController.update_campaign_progress(
            db=db,
            campaign_id=campaign_id,
            processed_records=processed_records,
            total_records=total_records,
            user=current_user
        )
        return APIResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="Campaign progress updated successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign progress: {str(e)}")

@router.delete("/{campaign_id}", response_model=APIResponse)
async def delete_campaign(
    campaign_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a campaign"""
    try:
        success = CampaignController.delete_campaign(
            db=db, campaign_id=campaign_id, user=current_user
        )
        if success:
            return APIResponse(
                success=True,
                message="Campaign deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Campaign not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e)}")

# File upload endpoint
@router.post("/{campaign_id}/upload", response_model=APIResponse)
async def upload_campaign_file(
    campaign_id: uuid.UUID = Path(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a file for campaign processing"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Only CSV and Excel files are supported"
            )
        
        # Save file and update campaign
        # This would typically involve saving to cloud storage
        # For now, we'll just update the file path
        file_path = f"uploads/{campaign_id}/{file.filename}"
        
        campaign = CampaignController.set_campaign_file_path(
            db=db,
            campaign_id=campaign_id,
            file_path=file_path,
            user=current_user
        )
        
        return APIResponse(
            success=True,
            data=CampaignResponse.model_validate(campaign),
            message="File uploaded successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}") 
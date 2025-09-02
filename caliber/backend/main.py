"""
Caliber - AI-Powered Inventory Scoring Backend
FastAPI application with MongoDB integration and multi-user support
"""

from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form, status, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import logging
import uvicorn
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
import io
import pandas as pd
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import database models
from db.models import User, Organization, Membership, Campaign, Report, ScoreRow, UserRole, PasswordReset, ScoreStatus, ReportStatus, CampaignStatus, CampaignGoal, AnalysisLevel, CampaignType

# Create FastAPI app
app = FastAPI(
    title="Caliber API",
    description="AI-Powered Inventory Scoring Platform - Multi-User Ready",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add CORS headers to all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Caliber backend...")
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/caliber')
    client = AsyncIOMotorClient(mongo_url)
    database = client.get_database()
    
    # Initialize Beanie with models
    await init_beanie(database=database, document_models=[
        User, Organization, Membership, Campaign, Report, ScoreRow, PasswordReset
    ])
    logger.info("MongoDB initialized with Beanie ODM")

# Authentication Models
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    organizations: List[dict]

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    """Create JWT token for user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Get current authenticated user with proper validation"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    # Verify JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_user_organizations(user: User) -> List[dict]:
    """Get organizations user belongs to with their roles"""
    memberships = await Membership.find(Membership.user_id == user.id).to_list()
    organizations = []
    
    for membership in memberships:
        org = await Organization.get(membership.org_id)
        if org:
            organizations.append({
                'id': org.id,
                'name': org.name,
                'role': membership.role
            })
    
    return organizations

async def process_file_and_generate_scores(file_content: bytes, filename: str, report_id: str, campaign, campaign_id: str = None) -> list:
    """Process uploaded file and generate scoring results using basic scoring engine"""
    try:
        logger.info(f"Processing file {filename} with basic scoring engine")
        
        # Read the file content
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format")
        
        logger.info(f"Loaded {len(df)} rows from {filename}")
        
        # Basic scoring logic
        score_rows = []
        for index, row in df.iterrows():
            try:
                # Extract basic metrics (adjust column names as needed)
                domain = row.get('domain', row.get('Domain', f'domain_{index}'))
                publisher = row.get('publisher', row.get('Publisher', f'publisher_{index}'))
                cpm = float(row.get('cpm', row.get('CPM', 0)))
                ctr = float(row.get('ctr', row.get('CTR', 0)))
                conversion_rate = float(row.get('conversion_rate', row.get('Conversion Rate', 0)))
                
                # Calculate basic score
                score = calculate_basic_score(cpm, ctr, conversion_rate, campaign.ctr_sensitivity)
                
                # Determine status
                if score >= 80:
                    status_enum = ScoreStatus.GOOD
                    status_str = "Good"
                elif score >= 60:
                    status_enum = ScoreStatus.MODERATE
                    status_str = "Moderate"
                else:
                    status_enum = ScoreStatus.POOR
                    status_str = "Poor"
                
                # Create ScoreRow object
                score_row = ScoreRow(
                    report_id=report_id,
                    domain=domain,
                    publisher=publisher,
                    cpm=cpm,
                    ctr=ctr,
                    conversion_rate=conversion_rate,
                    score=score,
                    status=status_enum,
                    explanation=f"Score {score:.1f} based on CPM: {cpm:.2f}, CTR: {ctr:.2f}%, Conversion: {conversion_rate:.2f}%"
                )
                score_rows.append(score_row)
                
            except Exception as row_error:
                logger.warning(f"Error processing row {index}: {row_error}")
                continue
        
        logger.info(f"✅ Generated {len(score_rows)} scores from {filename}")
        return score_rows
        
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        raise e

def calculate_basic_score(cpm: float, ctr: float, conversion_rate: float, ctr_sensitive: bool) -> float:
    """Calculate basic domain performance score"""
    # Base scoring weights
    cpm_weight = 0.3
    ctr_weight = 0.35 if ctr_sensitive else 0.25
    conversion_weight = 0.25
    volume_weight = 0.2 if not ctr_sensitive else 0.1
    
    # Normalize values (0-100 scale)
    # CPM: Lower is better (0-20 range, normalized to 0-100)
    cpm_score = max(0, 100 - (cpm * 5))
    
    # CTR: Higher is better (0-10 range, normalized to 0-100)
    ctr_score = min(100, ctr * 10)
    
    # Conversion Rate: Higher is better (0-5 range, normalized to 0-100)
    conversion_score = min(100, conversion_rate * 20)
    
    # Volume: Higher impressions get bonus (0-100 scale)
    volume_score = 50  # Default volume score
    
    # Calculate weighted score
    final_score = (
        cpm_score * cpm_weight +
        ctr_score * ctr_weight +
        conversion_score * conversion_weight +
        volume_score * volume_weight
    )
    
    # Ensure score is between 0-100
    return max(0, min(100, round(final_score, 1)))

# Health check endpoints
@app.get("/")
async def root():
    return {"message": "Caliber API - Multi-User Ready"}

@app.get("/api/")
async def root_api():
    return {"message": "Caliber API is running with multi-user support"}

@app.get("/api/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "caliber-backend", 
        "multi_user": True,
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserRegister):
    """Register a new user and create their first organization"""
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user
    user = User(
        name=user_data.full_name,
        email=user_data.email,
        password_hash=password_hash
    )
    await user.insert()
    
    # Create default organization for user
    org_name = f"{user_data.full_name}'s Organization"
    organization = Organization(name=org_name)
    await organization.insert()
    
    # Create membership with admin role
    membership = Membership(
        user_id=user.id,
        org_id=organization.id,
        role=UserRole.ADMIN
    )
    await membership.insert()
    
    # Create JWT token
    token = create_jwt_token(user.id, user.email)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "token": token,
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "role": "Admin"
        }
    }

@app.post("/api/auth/login")
async def login_user(user_data: UserLogin):
    """Authenticate user and return JWT token"""
    # Find user by email
    user = await User.find_one(User.email == user_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = create_jwt_token(user.id, user.email)
    
    # Get user organizations
    organizations = await get_user_organizations(user)
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "token": token,
        "organizations": organizations
    }

@app.post("/api/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify JWT token and return user info"""
    organizations = await get_user_organizations(current_user)
    
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },
        "organizations": organizations
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    organizations = await get_user_organizations(current_user)
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "organizations": organizations
    }

# Campaign routes
@app.get("/api/campaigns")
async def list_campaigns(current_user: User = Depends(get_current_user)):
    """List campaigns for the current user"""
    # Get user's organizations
    organizations = await get_user_organizations(current_user)
    org_ids = [org['id'] for org in organizations]
    
    # Get campaigns for user's organizations - Fix Beanie query
    if org_ids:
        campaigns = await Campaign.find(Campaign.org_id.in_(org_ids)).to_list()
    else:
        campaigns = []
    
    return [
        {
            "id": campaign.id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() + "Z",
            "created_by": campaign.created_by,
            "org_id": campaign.org_id
        }
        for campaign in campaigns
    ]

@app.post("/api/campaigns")
async def create_campaign(
    name: str = Form(...),
    campaign_type: str = Form(...),
    goal: str = Form(...),
    channel: str = Form(...),
    ctr_sensitivity: bool = Form(...),
    analysis_level: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Create campaign with file upload and scoring"""
    # Get user's first organization
    organizations = await get_user_organizations(current_user)
    if not organizations:
        raise HTTPException(status_code=400, detail="No organization found")
    
    org_id = organizations[0]['id']
    
    # Validate file type
    if not file.filename or not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Only CSV and Excel files are supported.")
    
    # Convert string values to enum values
    campaign_type_enum = CampaignType.TRADEDESK if campaign_type == "TradeDesk" else CampaignType.PULSEPOINT
    goal_enum = CampaignGoal.AWARENESS if goal == "Awareness" else CampaignGoal.ACTION
    analysis_level_enum = AnalysisLevel.DOMAIN if analysis_level == "DOMAIN" else AnalysisLevel.VENDOR
    
    # Create campaign
    campaign = Campaign(
        org_id=org_id,
        name=name,
        campaign_type=campaign_type_enum,
        goal=goal_enum,
        channel=channel,
        ctr_sensitivity=ctr_sensitivity,
        analysis_level=analysis_level_enum,
        created_by=current_user.id,
        status=CampaignStatus.ACTIVE
    )
    await campaign.insert()
    
    # Create report entry
    report = Report(
        campaign_id=campaign.id,
        filename=file.filename,
        storage_path=f"org_{org_id}/campaign_{campaign.id}/{file.filename}",
        status=ReportStatus.PROCESSING
    )
    await report.insert()
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process file and generate scores using the scoring engine
        scores = await process_file_and_generate_scores(
            file_content, 
            file.filename, 
            report.id, 
            campaign,
            campaign_id=str(campaign.id)
        )
        
        # Store scores in database
        if scores and len(scores) > 0:
            await ScoreRow.insert_many(scores)
            logger.info(f"✅ Successfully stored {len(scores)} scores in database")
            
            # Update report status to completed
            report.status = ReportStatus.COMPLETED
            await report.save()
            
        else:
            logger.warning("No scores generated, marking report as failed")
            report.status = ReportStatus.FAILED
            report.error_message = "No scoring results generated"
            await report.save()
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "ctr_sensitivity": campaign.ctr_sensitivity,
            "analysis_level": campaign.analysis_level,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() + "Z",
            "org_id": campaign.org_id,
            "created_by": campaign.created_by,
            "file_uploaded": {
                "filename": file.filename,
                "size": len(file_content),
                "type": file.content_type
            },
            "scores_generated": len(scores) if scores else 0,
            "report_id": report.id
        }
        
    except Exception as e:
        logger.error(f"Error processing file for campaign {campaign.id}: {str(e)}")
        # Mark report as failed
        report.status = ReportStatus.FAILED
        report.error_message = str(e)
        await report.save()
        
        # Return campaign with error
        return {
            "id": campaign.id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "channel": campaign.channel,
            "ctr_sensitivity": campaign.ctr_sensitivity,
            "analysis_level": campaign.analysis_level,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() + "Z",
            "org_id": campaign.org_id,
            "created_by": campaign.created_by,
            "file_uploaded": {
                "filename": file.filename,
                "type": file.content_type
            },
            "scores_generated": 0,
            "error": f"Scoring failed: {str(e)}"
        }

# Report routes
@app.get("/api/reports")
async def list_reports(current_user: User = Depends(get_current_user)):
    """List reports for the current user"""
    # Get user's organizations
    organizations = await get_user_organizations(current_user)
    org_ids = [org['id'] for org in organizations]
    
    # Get campaigns for user's organizations
    if org_ids:
        campaigns = await Campaign.find(Campaign.org_id.in_(org_ids)).to_list()
        campaign_ids = [c.id for c in campaigns]
    else:
        campaign_ids = []
    
    if not campaign_ids:
        return []
    
    # Get reports for these campaigns
    reports = []
    for campaign_id in campaign_ids:
        campaign_reports = await Report.find(Report.campaign_id == campaign_id).to_list()
        reports.extend(campaign_reports)
    
    return [
        {
            "id": report.id,
            "campaign_id": report.campaign_id,
            "filename": report.filename,
            "uploaded_at": report.uploaded_at.isoformat() + "Z",
            "status": report.status
        }
        for report in reports
    ]

@app.get("/api/reports/{report_id}/scores")
async def get_report_scores(
    report_id: str,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("score", description="Sort field: score, ctr, cpm, domain"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    status_filter: Optional[str] = Query(None, description="Filter by status: Good, Moderate, Poor"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score filter"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum score filter")
):
    """Get scores for a report"""
    # Get report and verify access
    report = await Report.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get campaign to check org access
    campaign = await Campaign.get(report.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify user has access to this campaign's organization
    user_organizations = await get_user_organizations(current_user)
    user_org_ids = [org['id'] for org in user_organizations]
    
    if campaign.org_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get scores from database
    scores = await ScoreRow.find(ScoreRow.report_id == report_id).to_list()
    
    if not scores:
        return {
            "data": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": 0,
                "pages": 0
            },
            "filters": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "status_filter": status_filter,
                "min_score": min_score,
                "max_score": max_score
            },
            "message": "No scores found for this report."
        }
    
    # Transform scores to API response format
    score_data = []
    for score in scores:
        score_data.append({
            "domain": score.domain,
            "publisher": score.publisher,
            "cpm": score.cpm,
            "ctr": score.ctr,
            "conversion_rate": score.conversion_rate,
            "score": score.score,
            "status": score.status.value if hasattr(score.status, 'value') else str(score.status),
            "explanation": score.explanation
        })
    
    return {
        "data": score_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(score_data),
            "pages": 1
        },
        "filters": {
            "sort_by": sort_by,
            "sort_order": sort_order,
            "status_filter": status_filter,
            "min_score": min_score,
            "max_score": max_score
        }
    }

# WebSocket endpoint for progress updates
@app.websocket("/ws/progress/{campaign_id}")
async def websocket_progress(websocket: WebSocket, campaign_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    try:
        while True:
            # Send progress updates
            await websocket.send_text(json.dumps({
                "type": "progress_update",
                "data": {
                    "campaign_id": campaign_id,
                    "progress_percentage": 100,
                    "current_step": "Completed",
                    "current_operation": "Scoring finished",
                    "processed_rows": 100,
                    "total_rows": 100,
                    "estimated_completion": None,
                    "errors": [],
                    "warnings": []
                }
            }))
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
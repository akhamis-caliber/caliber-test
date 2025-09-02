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
    
    # Get campaigns for user's organizations
    campaigns = await Campaign.find(Campaign.org_id.in_(org_ids)).to_list()
    
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
    """Create campaign with file upload"""
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
        status=ReportStatus.COMPLETED
    )
    await report.insert()
    
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
        "report_id": report.id
    }

# Report routes
@app.get("/api/reports")
async def list_reports(current_user: User = Depends(get_current_user)):
    """List reports for the current user"""
    # Get user's organizations
    organizations = await get_user_organizations(current_user)
    org_ids = [org['id'] for org in organizations]
    
    # Get campaigns for user's organizations
    campaigns = await Campaign.find(Campaign.org_id.in_(org_ids)).to_list()
    campaign_ids = [c.id for c in campaigns]
    
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from auth_service.dependencies import LoginRequest, LoginResponse, UserResponse, get_current_user
from auth_service.firebase_verify import verify_firebase_token
from db.models import User
from common.schemas import APIResponse

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login", response_model=APIResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Firebase token
    """
    # Verify Firebase token
    firebase_user = await verify_firebase_token(request.token)
    
    # Get or create user
    user = db.query(User).filter(User.firebase_uid == firebase_user['uid']).first()
    
    if not user:
        user = User(
            firebase_uid=firebase_user['uid'],
            email=firebase_user['email'],
            name=firebase_user['name'] or firebase_user['email'].split('@')[0]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="Login successful"
    )

@router.get("/profile", response_model=APIResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )

@router.put("/profile", response_model=APIResponse)
async def update_profile(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile
    """
    current_user.name = name
    db.commit()
    db.refresh(current_user)
    
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="Profile updated successfully"
    ) 
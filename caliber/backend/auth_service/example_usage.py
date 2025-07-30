"""
Example usage of the authentication service in FastAPI endpoints
"""

from fastapi import APIRouter, Depends
from auth_service.dependencies import (
    get_current_user, 
    get_current_user_optional,
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse
)
from common.schemas import APIResponse
from common.logging import logger

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """
    Login with Firebase token
    """
    # In a real implementation, you would:
    # 1. Verify the Firebase token
    # 2. Create or get user from database
    # 3. Return user data
    
    # Mock user data for example
    user_data = UserResponse(
        id="user-id-here",
        created_at="2025-07-30T00:00:00Z",
        updated_at="2025-07-30T00:00:00Z",
        firebase_uid="firebase-uid-here",
        email="user@example.com",
        name="Test User"
    )
    
    return LoginResponse(user=user_data)

@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate):
    """
    Register a new user
    """
    # In a real implementation, you would:
    # 1. Verify the Firebase token
    # 2. Create user in database
    # 3. Return user data
    
    # Mock user data for example
    user_data = UserResponse(
        id="new-user-id",
        created_at="2025-07-30T00:00:00Z",
        updated_at="2025-07-30T00:00:00Z",
        firebase_uid=user_create.firebase_uid,
        email=user_create.email,
        name=user_create.name,
        organization_id=user_create.organization_id
    )
    
    return user_data

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information (requires authentication)
    """
    # Convert dict to UserResponse
    user_data = UserResponse(
        id="user-id-here",
        created_at="2025-07-30T00:00:00Z",
        updated_at="2025-07-30T00:00:00Z",
        firebase_uid=current_user['uid'],
        email=current_user['email'],
        name=current_user['name']
    )
    
    return user_data

@router.get("/optional", response_model=APIResponse)
async def get_optional_user_info(current_user: dict = Depends(get_current_user_optional)):
    """
    Get user information if authenticated (optional authentication)
    """
    if current_user:
        return APIResponse(
            success=True,
            data=current_user,
            message="User information retrieved successfully"
        )
    else:
        return APIResponse(
            success=True,
            data=None,
            message="No user authenticated"
        )

@router.post("/verify", response_model=APIResponse)
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify that the current token is valid
    """
    logger.info(f"Token verified for user: {current_user['email']}")
    return APIResponse(
        success=True,
        data={"verified": True, "user_id": current_user['uid']},
        message="Token verified successfully"
    ) 
"""
Authentication routes for the Caliber application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from config.database import get_db
from auth_service.models.user import UserService
from auth_service.firebase_verify import verify_google_token
from auth_service.jwt_manager import create_user_tokens, verify_token
from auth_service.middleware import get_current_user, get_current_active_user
from common.schemas import (
    UserCreate, UserUpdate, User as UserSchema, LoginRequest, 
    GoogleLoginRequest, Token, ErrorResponse
)
from db.models import User
from db.utils import create_audit_log

# Create router
auth_router = APIRouter()

# Security scheme
security = HTTPBearer()


@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.
    """
    try:
        # Check if user already exists
        existing_user = UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user = UserService.create_user_with_password(db, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Create tokens
        tokens = create_user_tokens(user.id, user.email)
        
        # Log the registration
        create_audit_log(
            db=db,
            user_id=user.id,
            action="USER_REGISTER",
            resource_type="USER",
            resource_id=user.id,
            details={"email": user.email, "method": "email_password"},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@auth_router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    """
    try:
        # Verify credentials
        user = UserService.verify_password(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = create_user_tokens(user.id, user.email)
        
        # Log the login
        create_audit_log(
            db=db,
            user_id=user.id,
            action="USER_LOGIN",
            resource_type="USER",
            resource_id=user.id,
            details={"email": user.email, "method": "email_password"},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@auth_router.post("/google-login", response_model=Token)
async def google_login(
    google_data: GoogleLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with Google OAuth token.
    """
    try:
        # Verify Google token
        firebase_user = verify_google_token(google_data.id_token)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user exists
        user = UserService.get_user_by_firebase_uid(db, firebase_user['uid'])
        
        if not user:
            # Create new user with Firebase data
            user = UserService.create_user_with_firebase(
                db=db,
                email=firebase_user['email'],
                full_name=firebase_user.get('name', 'Unknown'),
                firebase_uid=firebase_user['uid']
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user from Google data"
                )
            
            # Log user creation
            create_audit_log(
                db=db,
                user_id=user.id,
                action="USER_REGISTER",
                resource_type="USER",
                resource_id=user.id,
                details={
                    "email": user.email,
                    "method": "google_oauth",
                    "firebase_uid": firebase_user['uid']
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("User-Agent", "")
            )
        else:
            # Log user login
            create_audit_log(
                db=db,
                user_id=user.id,
                action="USER_LOGIN",
                resource_type="USER",
                resource_id=user.id,
                details={
                    "email": user.email,
                    "method": "google_oauth",
                    "firebase_uid": firebase_user['uid']
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("User-Agent", "")
            )
        
        # Create tokens
        tokens = create_user_tokens(user.id, user.email)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google login failed: {str(e)}"
        )


@auth_router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return UserService.to_schema(current_user)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user (invalidate token on client side).
    """
    try:
        # Log the logout
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="USER_LOGOUT",
            resource_type="USER",
            resource_id=current_user.id,
            details={"email": current_user.email},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        from auth_service.jwt_manager import verify_refresh_token
        
        # Verify refresh token
        token_data = verify_refresh_token(refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = UserService.get_user_by_id(db, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        tokens = create_user_tokens(user.id, user.email)
        
        # Log token refresh
        create_audit_log(
            db=db,
            user_id=user.id,
            action="TOKEN_REFRESH",
            resource_type="USER",
            resource_id=user.id,
            details={"email": user.email},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@auth_router.put("/profile", response_model=UserSchema)
async def update_profile(
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    """
    try:
        # Update user
        updated_user = UserService.update_user(db, current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log profile update
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_UPDATE",
            resource_type="USER",
            resource_id=current_user.id,
            details={"updated_fields": list(user_data.dict(exclude_unset=True).keys())},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return UserService.to_schema(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@auth_router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account (soft delete).
    """
    try:
        # Deactivate user
        success = UserService.deactivate_user(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        # Log account deletion
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="ACCOUNT_DELETE",
            resource_type="USER",
            resource_id=current_user.id,
            details={"email": current_user.email},
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", "")
        )
        
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deletion failed: {str(e)}"
        )


@auth_router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify if the current token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

@auth_router.post("/verify", response_model=Token)
async def verify_token_endpoint(
    token_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify token (Firebase ID token or JWT token) and return backend JWT token.
    """
    try:
        # Extract token from request body
        token = token_data.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required"
            )
        
        # Try to verify as JWT token first
        try:
            jwt_payload = verify_token(token)
            if jwt_payload:
                # JWT token is valid, get user from database
                user = UserService.get_user_by_id(db, jwt_payload.user_id)
                if user:
                    # Log token verification
                    create_audit_log(
                        db=db,
                        user_id=user.id,
                        action="TOKEN_VERIFICATION",
                        resource_type="USER",
                        resource_id=user.id,
                        details={
                            "email": user.email,
                            "method": "jwt_token_verification"
                        },
                        ip_address=request.client.host,
                        user_agent=request.headers.get("User-Agent", "")
                    )
                    
                    # Return new tokens
                    return create_user_tokens(user.id, user.email)
        except Exception as jwt_error:
            print(f"JWT verification failed: {jwt_error}")
        
        # If JWT verification failed, try Firebase token
        firebase_user = verify_google_token(token)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user exists in our database
        user = UserService.get_user_by_firebase_uid(db, firebase_user['uid'])
        
        if not user:
            # Create new user with Firebase data
            user = UserService.create_user_with_firebase(
                db=db,
                email=firebase_user['email'],
                full_name=firebase_user.get('name', 'Unknown'),
                firebase_uid=firebase_user['uid']
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user from Firebase data"
                )
            
            # Log user creation
            create_audit_log(
                db=db,
                user_id=user.id,
                action="USER_REGISTER",
                resource_type="USER",
                resource_id=user.id,
                details={
                    "email": user.email,
                    "method": "firebase_token_verification",
                    "firebase_uid": firebase_user['uid']
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("User-Agent", "")
            )
        else:
            # Log user verification
            create_audit_log(
                db=db,
                user_id=user.id,
                action="TOKEN_VERIFICATION",
                resource_type="USER",
                resource_id=user.id,
                details={
                    "email": user.email,
                    "method": "firebase_token_verification",
                    "firebase_uid": firebase_user['uid']
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("User-Agent", "")
            )
        
        # Create backend JWT tokens
        tokens = create_user_tokens(user.id, user.email)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token verification failed: {str(e)}"
        ) 
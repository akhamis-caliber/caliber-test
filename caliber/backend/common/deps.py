"""
Dependency injection functions for FastAPI with MongoDB
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
import firebase_admin
from firebase_admin import auth, credentials
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from db.models import User, Organization, Membership, UserRole
from common.exceptions import AuthenticationError, AuthorizationError
from config.settings import settings


# Initialize Firebase Admin SDK
try:
    if not firebase_admin._apps:
        # Use the Firebase credentials from environment
        private_key = settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if settings.FIREBASE_PRIVATE_KEY else None
        
        if private_key and settings.FIREBASE_PROJECT_ID:
            cred_dict = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                "private_key": private_key,
                "client_email": f"firebase-adminsdk@{settings.FIREBASE_PROJECT_ID}.iam.gserviceaccount.com",
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Initialize without credentials for development
            firebase_admin.initialize_app()
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    pass


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current authenticated user from Firebase token or dev bypass
    """
    if not authorization:
        raise AuthenticationError("Authorization header missing")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("Invalid authorization scheme")
    except ValueError:
        raise AuthenticationError("Invalid authorization header format")
    
    # Development bypass
    if token == settings.DEV_BYPASS_TOKEN:
        # Return or create a development user
        dev_user = await User.find_one(User.email == "dev@caliber.com")
        if not dev_user:
            dev_user = User(
                email="dev@caliber.com",
                name="Development User",
                firebase_uid="dev-user"
            )
            await dev_user.insert()
        return dev_user
    
    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name", email.split("@")[0] if email else "User")
        
        # Get or create user
        user = await User.find_one(User.firebase_uid == firebase_uid)
        if not user:
            if not email:
                raise AuthenticationError("Email not found in token")
            
            user = User(
                email=email,
                name=name,
                firebase_uid=firebase_uid
            )
            await user.insert()
        
        return user
        
    except Exception as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")


async def get_current_org(
    org_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    current_user: User = Depends(get_current_user)
) -> Organization:
    """
    Get current organization and verify user membership
    """
    if not org_id:
        # Return user's first organization or create a default one
        membership = await Membership.find_one(Membership.user_id == current_user.id)
        
        if membership:
            org = await Organization.find_one(Organization.id == membership.org_id)
            return org
        
        # Create default organization for user
        org = Organization(name=f"{current_user.name}'s Organization")
        await org.insert()
        
        membership = Membership(
            user_id=current_user.id,
            org_id=org.id,
            role=UserRole.ADMIN
        )
        await membership.insert()
        
        return org
    
    # Verify user has access to the specified organization
    membership = await Membership.find_one(
        Membership.user_id == current_user.id,
        Membership.org_id == org_id
    )
    
    if not membership:
        raise AuthorizationError("Access denied to organization")
    
    org = await Organization.find_one(Organization.id == org_id)
    return org


async def require_admin_role(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
) -> User:
    """
    Require admin role for the current organization
    """
    membership = await Membership.find_one(
        Membership.user_id == current_user.id,
        Membership.org_id == current_org.id,
        Membership.role == UserRole.ADMIN
    )
    
    if not membership:
        raise AuthorizationError("Admin role required")
    
    return current_user
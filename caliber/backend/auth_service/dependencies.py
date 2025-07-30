from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from .firebase_verify import verify_firebase_token
from common.exceptions import AuthenticationError
from common.schemas import BaseSchema
from common.logging import logger

security = HTTPBearer()

# User Schemas
class UserCreate(BaseModel):
    firebase_uid: str
    email: EmailStr
    name: str
    organization_id: Optional[str] = None

class UserResponse(BaseSchema):
    firebase_uid: str
    email: str
    name: str
    organization_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    token: str  # Firebase ID token

class LoginResponse(BaseModel):
    user: UserResponse
    message: str = "Login successful"

# Authentication Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency to get current authenticated user
    """
    try:
        user_data = await verify_firebase_token(credentials.credentials)
        logger.info(f"User authenticated: {user_data['email']}")
        return user_data
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise AuthenticationError("Authentication failed")

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency to get current user (optional - doesn't raise error if no token)
    """
    try:
        user_data = await verify_firebase_token(credentials.credentials)
        logger.info(f"User authenticated: {user_data['email']}")
        return user_data
    except AuthenticationError:
        # Return None for optional authentication
        return None
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        return None 
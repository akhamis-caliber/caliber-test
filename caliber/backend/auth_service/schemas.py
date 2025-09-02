"""
Pydantic schemas for authentication service
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from db.models import UserRole


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: str
    name: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerifyTokenResponse(BaseModel):
    user: UserResponse
    organizations: List[OrganizationResponse]


class LoginRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
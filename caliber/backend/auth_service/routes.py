"""
Authentication routes for Firebase integration with MongoDB
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from common.deps import get_current_user
from auth_service.schemas import UserResponse, OrganizationResponse, VerifyTokenResponse
from db.models import User, Organization, Membership, UserRole

router = APIRouter()


@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify Firebase token and return user session info
    """
    # Get user's organizations
    memberships = await Membership.find(Membership.user_id == current_user.id).to_list()
    
    organizations = []
    for membership in memberships:
        org = await Organization.find_one(Organization.id == membership.org_id)
        if org:
            org_data = OrganizationResponse(
                id=org.id,
                name=org.name,
                role=membership.role,
                created_at=org.created_at
            )
            organizations.append(org_data)
    
    # If user has no organizations, create a default one
    if not organizations:
        org = Organization(name=f"{current_user.name}'s Organization")
        await org.insert()
        
        membership = Membership(
            user_id=current_user.id,
            org_id=org.id,
            role=UserRole.ADMIN
        )
        await membership.insert()
        
        org_data = OrganizationResponse(
            id=org.id,
            name=org.name,
            role=UserRole.ADMIN,
            created_at=org.created_at
        )
        organizations.append(org_data)
    
    user_data = UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at
    )
    
    return VerifyTokenResponse(
        user=user_data,
        organizations=organizations
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at
    )
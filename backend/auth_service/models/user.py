"""
User model operations for authentication service.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime, timedelta
import bcrypt

from db.models import User, Organization, UserOrganization, UserRole
from db.utils import get_user_by_email, get_user_by_firebase_uid, create_user, update_user
from common.schemas import UserCreate, UserUpdate, User as UserSchema


class UserService:
    """Service class for user operations"""
    
    @staticmethod
    def create_user_with_password(db: Session, user_data: UserCreate) -> Optional[User]:
        """Create a new user with password hashing"""
        try:
            # Check if user already exists
            existing_user = get_user_by_email(db, user_data.email)
            if existing_user:
                return None
            
            # Hash the password
            hashed_password = bcrypt.hashpw(
                user_data.password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create user
            user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                organization=user_data.organization,
                role=user_data.role,
                password_hash=hashed_password,
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except IntegrityError:
            db.rollback()
            return None
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def create_user_with_firebase(db: Session, email: str, full_name: str, firebase_uid: str, 
                                organization: str = None) -> Optional[User]:
        """Create a new user with Firebase authentication"""
        try:
            # Check if user already exists
            existing_user = get_user_by_email(db, email)
            if existing_user:
                return None
            
            # Create user
            user = User(
                email=email,
                full_name=full_name,
                firebase_uid=firebase_uid,
                organization=organization,
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except IntegrityError:
            db.rollback()
            return None
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def verify_password(db: Session, email: str, password: str) -> Optional[User]:
        """Verify user password and return user if valid"""
        user = get_user_by_email(db, email)
        if not user or not user.is_active:
            return None
        
        # Check if user has password authentication
        if not user.password_hash:
            return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        
        return None
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return get_user_by_email(db, email)
    
    @staticmethod
    def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID"""
        return get_user_by_firebase_uid(db, firebase_uid)
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        # Hash password if provided
        if 'password' in update_data:
            hashed_password = bcrypt.hashpw(
                update_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            update_data['password_hash'] = hashed_password
            del update_data['password']
        
        # Update user
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """Deactivate a user (soft delete)"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    @staticmethod
    def get_user_organizations(db: Session, user_id: int) -> List[UserOrganization]:
        """Get all organizations for a user"""
        return db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.is_active == True
        ).all()
    
    @staticmethod
    def add_user_to_organization(db: Session, user_id: int, org_id: int, 
                               role: UserRole = UserRole.USER) -> Optional[UserOrganization]:
        """Add a user to an organization"""
        # Check if user and organization exist
        user = UserService.get_user_by_id(db, user_id)
        org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
        
        if not user or not org:
            return None
        
        # Check if user is already in organization
        existing = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if existing:
            existing.role = role
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new user-organization relationship
        user_org = UserOrganization(
            user_id=user_id,
            organization_id=org_id,
            role=role,
            is_active=True
        )
        
        db.add(user_org)
        db.commit()
        db.refresh(user_org)
        
        return user_org
    
    @staticmethod
    def remove_user_from_organization(db: Session, user_id: int, org_id: int) -> bool:
        """Remove a user from an organization"""
        user_org = db.query(UserOrganization).filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id
        ).first()
        
        if not user_org:
            return False
        
        user_org.is_active = False
        user_org.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int, org_id: int = None) -> dict:
        """Get user permissions for an organization"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return {}
        
        # Get user's role in the organization
        if org_id:
            user_org = db.query(UserOrganization).filter(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == org_id,
                UserOrganization.is_active == True
            ).first()
            
            if not user_org:
                return {}
            
            role = user_org.role
        else:
            role = user.role
        
        # Define permissions based on role
        permissions = {
            'can_create_campaigns': role in [UserRole.ADMIN, UserRole.USER],
            'can_edit_campaigns': role in [UserRole.ADMIN, UserRole.USER],
            'can_delete_campaigns': role == UserRole.ADMIN,
            'can_view_reports': role in [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER],
            'can_upload_files': role in [UserRole.ADMIN, UserRole.USER],
            'can_manage_users': role == UserRole.ADMIN,
            'can_view_analytics': role in [UserRole.ADMIN, UserRole.USER],
            'can_export_data': role in [UserRole.ADMIN, UserRole.USER],
        }
        
        return permissions
    
    @staticmethod
    def to_schema(user: User) -> UserSchema:
        """Convert User model to UserSchema"""
        return UserSchema(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization=user.organization,
            role=user.role,
            firebase_uid=user.firebase_uid,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        ) 
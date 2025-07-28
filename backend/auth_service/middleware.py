"""
Authentication middleware for protecting routes.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from config.database import get_db
from auth_service.jwt_manager import verify_token
from auth_service.models.user import UserService
from db.models import User
from common.schemas import TokenData


# Security scheme for Bearer token
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for protecting routes"""
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """Get current authenticated user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Verify the token
            token_data = verify_token(credentials.credentials)
            if token_data is None:
                raise credentials_exception
            
            # Get user from database
            user = UserService.get_user_by_id(db, token_data.user_id)
            if user is None or not user.is_active:
                raise credentials_exception
            
            return user
            
        except Exception as e:
            print(f"Authentication error: {e}")
            raise credentials_exception
    
    @staticmethod
    def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
    
    @staticmethod
    def get_current_user_optional(
        request: Request,
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if authenticated, otherwise return None"""
        try:
            # Check if Authorization header exists
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify the token
            token_data = verify_token(token)
            if token_data is None:
                return None
            
            # Get user from database
            user = UserService.get_user_by_id(db, token_data.user_id)
            if user is None or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            print(f"Optional authentication error: {e}")
            return None
    
    @staticmethod
    def require_permission(permission: str):
        """Decorator to require specific permission"""
        def permission_checker(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ) -> User:
            # Get user permissions
            permissions = UserService.get_user_permissions(db, current_user.id)
            
            if not permissions.get(permission, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )
            
            return current_user
        
        return permission_checker
    
    @staticmethod
    def require_role(required_role: str):
        """Decorator to require specific role"""
        def role_checker(
            current_user: User = Depends(get_current_user)
        ) -> User:
            if current_user.role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {required_role}"
                )
            
            return current_user
        
        return role_checker
    
    @staticmethod
    def require_admin(current_user: User = Depends(get_current_user)) -> User:
        """Require admin role"""
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    @staticmethod
    def require_user_or_admin(current_user: User = Depends(get_current_user)) -> User:
        """Require user or admin role"""
        if current_user.role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User or admin access required"
            )
        return current_user


# Convenience functions for dependency injection
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    return AuthMiddleware.get_current_user(credentials, db)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    return AuthMiddleware.get_current_active_user(current_user)


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    return AuthMiddleware.get_current_user_optional(request, db)


def require_permission(permission: str):
    """Require specific permission"""
    return AuthMiddleware.require_permission(permission)


def require_role(required_role: str):
    """Require specific role"""
    return AuthMiddleware.require_role(required_role)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    return AuthMiddleware.require_admin(current_user)


def require_user_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require user or admin role"""
    return AuthMiddleware.require_user_or_admin(current_user)


# Rate limiting middleware
class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In production, use Redis for this
    
    def check_rate_limit(self, request: Request):
        """Check rate limit for the request"""
        client_ip = request.client.host
        current_time = datetime.utcnow()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if (current_time - req_time).seconds < 60
            ]
        else:
            self.requests[client_ip] = []
        
        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)


# Audit logging middleware
class AuditMiddleware:
    """Audit logging middleware"""
    
    @staticmethod
    def log_request(request: Request, user: Optional[User] = None):
        """Log request for audit purposes"""
        from db.utils import create_audit_log
        from config.database import get_db
        
        try:
            db = next(get_db())
            
            # Extract request details
            action = f"{request.method} {request.url.path}"
            resource_type = "API_REQUEST"
            ip_address = request.client.host
            user_agent = request.headers.get("User-Agent", "")
            
            # Create audit log
            create_audit_log(
                db=db,
                user_id=user.id if user else None,
                action=action,
                resource_type=resource_type,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            print(f"Error logging audit: {e}")
        finally:
            if 'db' in locals():
                db.close() 
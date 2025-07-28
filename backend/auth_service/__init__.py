"""
Authentication service package for Caliber application.
"""

from .routes import auth_router
from .middleware import (
    get_current_user,
    get_current_active_user,
    get_current_user_optional,
    require_permission,
    require_role,
    require_admin,
    require_user_or_admin
)
from .jwt_manager import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    create_user_tokens
)
from .firebase_verify import (
    verify_google_token,
    get_firebase_user_info,
    create_firebase_token,
    set_user_claims,
    delete_firebase_user
)

__all__ = [
    "auth_router",
    "get_current_user",
    "get_current_active_user", 
    "get_current_user_optional",
    "require_permission",
    "require_role",
    "require_admin",
    "require_user_or_admin",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "verify_refresh_token",
    "create_user_tokens",
    "verify_google_token",
    "get_firebase_user_info",
    "create_firebase_token",
    "set_user_claims",
    "delete_firebase_user"
] 
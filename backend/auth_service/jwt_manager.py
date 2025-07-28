"""
JWT token management for authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config.settings import settings
from common.schemas import TokenData


class JWTManager:
    """JWT token management service"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating access token: {str(e)}"
            )
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        
        # Refresh tokens have longer expiration
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating refresh token: {str(e)}"
            )
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if email is None:
                return None
            
            return TokenData(email=email, user_id=user_id)
            
        except JWTError:
            return None
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[TokenData]:
        """Verify and decode a JWT refresh token"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check if it's a refresh token
            token_type = payload.get("type")
            if token_type != "refresh":
                return None
            
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if email is None:
                return None
            
            return TokenData(email=email, user_id=user_id)
            
        except JWTError:
            return None
        except Exception as e:
            print(f"Error verifying refresh token: {e}")
            return None
    
    @staticmethod
    def decode_token_payload(token: str) -> Optional[Dict[str, Any]]:
        """Decode token payload without verification (for debugging)"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False}
            )
            return payload
        except JWTError:
            return None
        except Exception as e:
            print(f"Error decoding token payload: {e}")
            return None
    
    @staticmethod
    def get_token_expiration(token: str) -> Optional[datetime]:
        """Get token expiration time"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False}
            )
            
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            
            return None
            
        except JWTError:
            return None
        except Exception as e:
            print(f"Error getting token expiration: {e}")
            return None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if token is expired"""
        expiration = JWTManager.get_token_expiration(token)
        if expiration is None:
            return True
        
        return datetime.utcnow() > expiration
    
    @staticmethod
    def create_user_tokens(user_id: int, email: str, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """Create both access and refresh tokens for a user"""
        # Prepare token data
        token_data = {
            "sub": email,
            "user_id": user_id,
            "type": "access"
        }
        
        # Add additional claims if provided
        if additional_claims:
            token_data.update(additional_claims)
        
        # Create tokens
        access_token = JWTManager.create_access_token(token_data)
        refresh_token = JWTManager.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    return JWTManager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    return JWTManager.create_refresh_token(data)


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    return JWTManager.verify_token(token)


def verify_refresh_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT refresh token"""
    return JWTManager.verify_refresh_token(token)


def create_user_tokens(user_id: int, email: str, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
    """Create both access and refresh tokens for a user"""
    return JWTManager.create_user_tokens(user_id, email, additional_claims) 
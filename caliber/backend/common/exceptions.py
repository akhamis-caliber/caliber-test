from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class CaliberException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class AuthenticationError(CaliberException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(CaliberException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)

class NotFoundError(CaliberException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} not found", status_code=status.HTTP_404_NOT_FOUND)

class ValidationError(CaliberException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

class DatabaseError(CaliberException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExternalServiceError(CaliberException):
    def __init__(self, service: str, detail: str = "External service error"):
        super().__init__(detail=f"{service}: {detail}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

def handle_exception(error: Exception, context: Optional[str] = None) -> CaliberException:
    """Convert various exceptions to CaliberException."""
    if isinstance(error, CaliberException):
        return error
    
    if isinstance(error, ValueError):
        return ValidationError(str(error))
    
    if isinstance(error, KeyError):
        return NotFoundError(f"Required field: {error}")
    
    # Default to internal server error
    detail = str(error)
    if context:
        detail = f"{context}: {detail}"
    
    return CaliberException(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 
"""
Custom exceptions for the Caliber application
"""

from typing import Optional


class CaliberException(Exception):
    """Base exception class for Caliber application"""
    
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class AuthenticationError(CaliberException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail, status_code=401)


class AuthorizationError(CaliberException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail, status_code=403)


class NotFoundError(CaliberException):
    """Raised when a resource is not found"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status_code=404)


class ValidationError(CaliberException):
    """Raised when data validation fails"""
    
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail, status_code=422)


class FileProcessingError(CaliberException):
    """Raised when file processing fails"""
    
    def __init__(self, detail: str = "File processing failed"):
        super().__init__(detail, status_code=400)


class ScoringError(CaliberException):
    """Raised when scoring pipeline fails"""
    
    def __init__(self, detail: str = "Scoring failed"):
        super().__init__(detail, status_code=500)
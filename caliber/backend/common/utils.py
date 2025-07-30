import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from common.logging import logger

def generate_uuid() -> uuid.UUID:
    """Generate a new UUID."""
    return uuid.uuid4()

def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with a default fallback."""
    try:
        return data.get(key, default)
    except (KeyError, AttributeError, TypeError):
        logger.warning(f"Failed to get key '{key}' from data, returning default")
        return default

def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """Format an error message with optional context."""
    base_message = f"Error: {str(error)}"
    if context:
        return f"{context} - {base_message}"
    return base_message

def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False 
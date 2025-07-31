from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
import uuid

class BaseResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None

class APIResponse(BaseResponse):
    pass

class PaginatedResponse(APIResponse):
    data: List[Any]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    has_next: bool
    has_prev: bool

class BaseSchema(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 
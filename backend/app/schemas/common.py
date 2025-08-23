from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API endpoints"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class PaginationInfo(BaseModel):
    """Pagination information for responses"""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class ResponseModel(BaseModel, Generic[T]):
    """Generic response model with data and metadata"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    pagination: Optional[PaginationInfo] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    database: str
    redis: Optional[str] = None

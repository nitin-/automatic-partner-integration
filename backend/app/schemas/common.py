from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum


class DataType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"


class MasterSourceFieldBase(BaseModel):
    name: str = Field(..., description="Unique field name")
    display_name: str = Field(..., description="Human-readable display name")
    description: Optional[str] = Field(None, description="Field description")
    field_type: DataType = Field(DataType.STRING, description="Data type of the field")
    is_required: bool = Field(False, description="Whether this field is required")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    default_value: Optional[str] = Field(None, description="Default value for the field")
    sample_data: Optional[Dict[str, Any]] = Field(None, description="Sample data for testing")
    is_active: bool = Field(True, description="Whether this field is active")


class MasterSourceFieldCreate(MasterSourceFieldBase):
    pass


class MasterSourceFieldUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    field_type: Optional[DataType] = None
    is_required: Optional[bool] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_value: Optional[str] = None
    sample_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class MasterSourceFieldResponse(MasterSourceFieldBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomTargetFieldBase(BaseModel):
    name: str = Field(..., description="Field name")
    display_name: str = Field(..., description="Human-readable display name")
    description: Optional[str] = Field(None, description="Field description")
    field_type: DataType = Field(DataType.STRING, description="Data type of the field")
    field_path: Optional[str] = Field(None, description="Nested field path")
    default_value: Optional[str] = Field(None, description="Default value for the field")
    is_active: bool = Field(True, description="Whether this field is active")


class CustomTargetFieldCreate(CustomTargetFieldBase):
    lender_id: int = Field(..., description="Lender ID this field belongs to")


class CustomTargetFieldUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    field_type: Optional[DataType] = None
    field_path: Optional[str] = None
    default_value: Optional[str] = None
    is_active: Optional[bool] = None


class CustomTargetFieldResponse(CustomTargetFieldBase):
    id: int
    lender_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc or desc)")


class PaginationInfo(BaseModel):
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    pagination: Optional[PaginationInfo] = None
    timestamp: Optional[str] = None


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

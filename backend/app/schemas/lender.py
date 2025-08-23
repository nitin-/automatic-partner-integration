from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Dict, Any
from datetime import datetime


class LenderBase(BaseModel):
    """Base lender schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Lender name")
    description: Optional[str] = Field(None, description="Lender description")
    base_url: HttpUrl = Field(..., description="Base URL for the lender's API")
    api_version: Optional[str] = Field(None, max_length=50, description="API version")
    
    # Authentication configuration
    auth_type: str = Field(default="bearer", pattern="^(bearer|api_key|oauth2|basic)$", description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    
    # API Documentation
    openapi_spec_url: Optional[HttpUrl] = Field(None, description="OpenAPI specification URL")
    documentation_url: Optional[HttpUrl] = Field(None, description="Documentation URL")
    
    # Status and metadata
    is_active: bool = Field(default=True, description="Whether the lender is active")
    is_verified: bool = Field(default=False, description="Whether the lender is verified")
    rate_limit: Optional[int] = Field(None, ge=1, description="Rate limit (requests per minute)")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    
    # Contact information
    contact_email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Contact email")
    support_url: Optional[HttpUrl] = Field(None, description="Support URL")
    
    @validator('auth_config')
    def validate_auth_config(cls, v, values):
        """Validate auth_config based on auth_type"""
        if v is None:
            return v
            
        auth_type = values.get('auth_type')
        if auth_type == 'bearer':
            required_fields = ['token_url', 'client_id', 'client_secret']
        elif auth_type == 'api_key':
            required_fields = ['key_name', 'key_location']  # header, query, body
        elif auth_type == 'oauth2':
            required_fields = ['authorization_url', 'token_url', 'client_id', 'client_secret']
        elif auth_type == 'basic':
            required_fields = ['username', 'password']
        else:
            return v
            
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f"Missing required fields for {auth_type} auth: {missing_fields}")
        
        return v


class LenderCreate(LenderBase):
    """Schema for creating a new lender"""
    pass


class LenderUpdate(BaseModel):
    """Schema for updating a lender"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    api_version: Optional[str] = Field(None, max_length=50)
    auth_type: Optional[str] = Field(None, pattern="^(bearer|api_key|oauth2|basic)$")
    auth_config: Optional[Dict[str, Any]] = None
    openapi_spec_url: Optional[HttpUrl] = None
    documentation_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    rate_limit: Optional[int] = Field(None, ge=1)
    timeout: Optional[int] = Field(None, ge=1, le=300)
    contact_email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    support_url: Optional[HttpUrl] = None


class LenderResponse(LenderBase):
    """Schema for lender response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LenderList(BaseModel):
    """Schema for lender list response"""
    lenders: list[LenderResponse]
    total: int
    page: int
    size: int
    pages: int

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class APIConfig(Base):
    __tablename__ = "api_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    
    # Configuration name and description
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # API Configuration
    endpoint_path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False, default="GET")  # GET, POST, PUT, DELETE, PATCH
    
    # Request configuration
    headers = Column(JSON, nullable=True)  # Default headers
    query_params = Column(JSON, nullable=True)  # Default query parameters
    request_body_schema = Column(JSON, nullable=True)  # JSON schema for request body
    
    # Response configuration
    response_schema = Column(JSON, nullable=True)  # Expected response schema
    success_codes = Column(JSON, nullable=True)  # List of success HTTP codes
    
    # Authentication
    requires_auth = Column(Boolean, default=True)
    auth_parameters = Column(JSON, nullable=True)  # Required auth parameters
    
    # Rate limiting and retry
    rate_limit = Column(Integer, nullable=True)  # Override lender rate limit
    retry_config = Column(JSON, nullable=True)  # Retry configuration
    
    # Validation and transformation
    validation_rules = Column(JSON, nullable=True)  # Custom validation rules
    data_mapping = Column(JSON, nullable=True)  # Field mapping configuration
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    
    # Versioning
    version = Column(String(50), default="1.0.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lender = relationship("Lender", back_populates="api_configs")
    api_tests = relationship("APITest", back_populates="api_config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<APIConfig(id={self.id}, name='{self.name}', lender_id={self.lender_id})>"

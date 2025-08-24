from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Lender(Base):
    __tablename__ = "lenders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    base_url = Column(String(500), nullable=False)
    api_version = Column(String(50), nullable=True)
    
    # Authentication configuration
    auth_type = Column(String(50), nullable=False, default="bearer")  # bearer, api_key, oauth2, basic
    auth_config = Column(JSON, nullable=True)  # Store auth-specific configuration
    
    # API Documentation
    openapi_spec_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    rate_limit = Column(Integer, nullable=True)  # requests per minute
    timeout = Column(Integer, default=30)  # seconds
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    support_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_configs = relationship("APIConfig", back_populates="lender", cascade="all, delete-orphan")
    generated_apis = relationship("GeneratedAPI", back_populates="lender", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="lender", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="lender", cascade="all, delete-orphan")
    integration_sequences = relationship("IntegrationSequence", back_populates="lender", cascade="all, delete-orphan")
    deployed_apis = relationship("DeployedAPI", back_populates="lender", cascade="all, delete-orphan")
    deployed_integrations = relationship("DeployedIntegration", back_populates="lender", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lender(id={self.id}, name='{self.name}', base_url='{self.base_url}')>"

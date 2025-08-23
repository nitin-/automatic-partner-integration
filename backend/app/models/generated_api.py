from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class GeneratedAPI(Base):
    __tablename__ = "generated_apis"
    
    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    
    # Generation metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    
    # Generation configuration
    template_id = Column(Integer, ForeignKey("api_templates.id"), nullable=True)
    generation_config = Column(JSON, nullable=True)  # Configuration used for generation
    
    # Generated files
    file_path = Column(String(500), nullable=False)  # Path to generated file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_hash = Column(String(64), nullable=True)  # SHA256 hash for change detection
    
    # Code generation details
    language = Column(String(50), nullable=False)  # python, typescript, javascript, etc.
    framework = Column(String(100), nullable=True)  # fastapi, express, django, etc.
    dependencies = Column(JSON, nullable=True)  # Required dependencies
    
    # Status and validation
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)  # Any validation errors
    test_status = Column(String(50), default="pending")  # pending, running, passed, failed
    
    # Usage tracking
    is_deployed = Column(Boolean, default=False)
    deployment_url = Column(String(500), nullable=True)
    last_deployed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    generation_time = Column(Integer, nullable=True)  # Time taken to generate in seconds
    complexity_score = Column(Integer, nullable=True)  # Code complexity metric
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lender = relationship("Lender", back_populates="generated_apis")
    template = relationship("APITemplate")
    
    def __repr__(self):
        return f"<GeneratedAPI(id={self.id}, name='{self.name}', language='{self.language}')>"

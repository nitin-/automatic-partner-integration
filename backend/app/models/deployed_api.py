from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class DeployedAPI(Base):
    __tablename__ = "deployed_apis"
    
    id = Column(String, primary_key=True)  # UUID from deployment
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_config = Column(JSON, nullable=False)  # Full step configuration
    api_signature = Column(JSON, nullable=False)  # Generated API signature
    status = Column(String(50), default="active")  # active, inactive, error
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Relationships
    lender = relationship("Lender", back_populates="deployed_apis")
    
    def __repr__(self):
        return f"<DeployedAPI(id={self.id}, step_name='{self.step_name}', status='{self.status}')>"


class DeployedIntegration(Base):
    __tablename__ = "deployed_integrations"
    
    id = Column(String, primary_key=True)  # UUID from deployment
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    sequence_config = Column(JSON, nullable=False)  # Full sequence configuration
    field_mappings = Column(JSON, nullable=False)  # Field mapping configuration
    api_signature = Column(JSON, nullable=False)  # Generated API signature
    status = Column(String(50), default="active")  # active, inactive, error
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Relationships
    lender = relationship("Lender", back_populates="deployed_integrations")
    
    def __repr__(self):
        return f"<DeployedIntegration(id={self.id}, status='{self.status}')>"

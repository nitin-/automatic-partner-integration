from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class APITest(Base):
    __tablename__ = "api_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    api_config_id = Column(Integer, ForeignKey("api_configs.id"), nullable=False)
    
    # Test configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False)  # unit, integration, e2e, performance
    
    # Test parameters
    test_data = Column(JSON, nullable=True)  # Input data for the test
    expected_response = Column(JSON, nullable=True)  # Expected response structure
    validation_rules = Column(JSON, nullable=True)  # Custom validation rules
    
    # Test execution
    is_active = Column(Boolean, default=True)
    is_automated = Column(Boolean, default=True)
    execution_order = Column(Integer, default=0)
    
    # Test results
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_status = Column(String(50), nullable=True)  # passed, failed, error, skipped
    last_run_duration = Column(Integer, nullable=True)  # Duration in milliseconds
    last_run_error = Column(Text, nullable=True)  # Error message if failed
    
    # Performance metrics
    avg_response_time = Column(Integer, nullable=True)  # Average response time in ms
    success_rate = Column(Integer, nullable=True)  # Success rate percentage
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    
    # Test environment
    environment = Column(String(50), default="development")  # dev, staging, production
    timeout = Column(Integer, default=30)  # Test timeout in seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_config = relationship("APIConfig", back_populates="api_tests")
    
    def __repr__(self):
        return f"<APITest(id={self.id}, name='{self.name}', type='{self.test_type}')>"

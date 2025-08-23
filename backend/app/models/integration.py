from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class IntegrationType(str, enum.Enum):
    LEAD_SUBMISSION = "lead_submission"
    STATUS_CHECK = "status_check"
    BULK_UPLOAD = "bulk_upload"
    WEBHOOK = "webhook"
    POLLING = "polling"
    SEQUENCE = "sequence"  # Multi-step integration sequence


class AuthenticationType(str, enum.Enum):
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Integration type and configuration
    integration_type = Column(Enum(IntegrationType), nullable=False)
    api_endpoint = Column(String(500), nullable=False)
    http_method = Column(String(10), default="POST")  # GET, POST, PUT, PATCH, DELETE
    
    # Sequence configuration (for multi-step integrations)
    sequence_order = Column(Integer, default=1)  # Order in sequence
    parent_sequence_id = Column(Integer, ForeignKey("integration_sequences.id"), nullable=True)
    is_sequence_step = Column(Boolean, default=False)
    
    # Authentication
    auth_type = Column(Enum(AuthenticationType), nullable=False)
    auth_config = Column(JSON, nullable=True)  # Store auth-specific configuration
    
    # Request/Response configuration
    request_headers = Column(JSON, nullable=True)
    request_schema = Column(JSON, nullable=True)  # Expected request structure
    response_schema = Column(JSON, nullable=True)  # Expected response structure
    
    # Data dependencies (for sequences)
    depends_on_fields = Column(JSON, nullable=True)  # Fields from previous steps
    output_fields = Column(JSON, nullable=True)  # Fields to extract from response
    
    # Rate limiting and timeouts
    rate_limit_per_minute = Column(Integer, nullable=True)
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)
    
    # Error handling
    error_mapping = Column(JSON, nullable=True)  # Map error codes to user-friendly messages
    fallback_config = Column(JSON, nullable=True)  # Fallback behavior configuration
    
    # Status and monitoring
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.INACTIVE)
    last_test_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    lender = relationship("Lender", back_populates="integrations")
    # Link back to parent sequence for steps
    parent_sequence = relationship(
        "IntegrationSequence",
        back_populates="steps",
        foreign_keys=[parent_sequence_id]
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Integration(id={self.id}, name='{self.name}', type='{self.integration_type}')>"


class IntegrationSequence(Base):
    __tablename__ = "integration_sequences"

    id = Column(Integer, primary_key=True, index=True)
    
    # Sequence info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Sequence configuration
    sequence_type = Column(String(100), nullable=False)  # e.g., "lead_submission", "status_check"
    execution_mode = Column(String(50), default="sequential")  # sequential, parallel, conditional
    
    # Conditional logic
    condition_config = Column(JSON, nullable=True)  # Conditions for sequence execution
    
    # Error handling
    stop_on_error = Column(Boolean, default=True)  # Stop sequence on first error
    retry_failed_steps = Column(Boolean, default=False)  # Retry failed steps
    
    # Relationships
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    lender = relationship("Lender", back_populates="integration_sequences")
    steps = relationship("Integration", back_populates="parent_sequence")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<IntegrationSequence(id={self.id}, name='{self.name}', type='{self.sequence_type}')>"


class IntegrationLog(Base):
    __tablename__ = "integration_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Integration reference
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    integration = relationship("Integration")
    
    # Sequence reference (for multi-step integrations)
    sequence_id = Column(Integer, ForeignKey("integration_sequences.id"), nullable=True)
    sequence = relationship("IntegrationSequence")
    step_order = Column(Integer, nullable=True)  # Order in sequence
    
    # Request details
    request_id = Column(String(255), nullable=False, index=True)  # Unique request identifier
    request_data = Column(JSON, nullable=True)  # Transformed request data
    request_headers = Column(JSON, nullable=True)
    
    # Response details
    response_status = Column(Integer, nullable=True)
    response_data = Column(JSON, nullable=True)
    response_headers = Column(JSON, nullable=True)
    
    # Performance metrics
    request_time = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Request duration in milliseconds
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Business context
    lead_id = Column(String(255), nullable=True, index=True)  # Reference to the lead
    user_id = Column(Integer, nullable=True)  # User who triggered the integration
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<IntegrationLog(id={self.id}, integration_id={self.integration_id}, status={self.response_status})>"


class IntegrationTest(Base):
    __tablename__ = "integration_tests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Test configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Test data
    test_data = Column(JSON, nullable=False)  # Sample data for testing
    expected_response = Column(JSON, nullable=True)  # Expected response structure
    
    # Test results
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(50), nullable=True)  # success, failed, error
    last_response = Column(JSON, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Relationships
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    integration = relationship("Integration")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<IntegrationTest(id={self.id}, name='{self.name}', integration_id={self.integration_id})>"

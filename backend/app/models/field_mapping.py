from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class TransformationType(str, enum.Enum):
    NONE = "none"
    FORMAT_PHONE = "format_phone"
    FORMAT_DATE = "format_date"
    FORMAT_CURRENCY = "format_currency"
    SPLIT_NAME = "split_name"
    OBJECT_MAPPING = "object_mapping"
    ARRAY_FORMAT = "array_format"
    CONDITIONAL = "conditional"
    CUSTOM = "custom"


class DataType(str, enum.Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"


class MasterSourceField(Base):
    __tablename__ = "master_source_fields"

    id = Column(Integer, primary_key=True, index=True)
    
    # Field information
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    field_type = Column(Enum(DataType), default=DataType.STRING)
    
    # Validation and constraints
    is_required = Column(Boolean, default=False)
    validation_rules = Column(JSON, nullable=True)  # Store validation rules
    default_value = Column(String(500), nullable=True)
    
    # Sample data for testing
    sample_data = Column(JSON, nullable=True)  # Store sample values for testing
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<MasterSourceField(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class CustomTargetField(Base):
    __tablename__ = "custom_target_fields"

    id = Column(Integer, primary_key=True, index=True)
    
    # Field information
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    field_type = Column(Enum(DataType), default=DataType.STRING)
    
    # Field path for nested structures
    field_path = Column(String(500), nullable=True)  # For nested fields like "address.street"
    
    # Default values
    default_value = Column(String(500), nullable=True)
    
    # Relationships
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    lender = relationship("Lender", back_populates="custom_target_fields")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CustomTargetField(id={self.id}, name='{self.name}', lender_id={self.lender_id})>"


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic mapping info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Source field (your standard field)
    source_field = Column(String(255), nullable=False)
    source_field_type = Column(Enum(DataType), default=DataType.STRING)
    source_field_path = Column(String(500), nullable=True)  # For nested fields like "address.street"
    
    # Target field (lender's field)
    target_field = Column(String(255), nullable=False)
    target_field_type = Column(Enum(DataType), default=DataType.STRING)
    target_field_path = Column(String(500), nullable=True)  # For nested target fields
    
    # Transformation configuration
    transformation_type = Column(Enum(TransformationType), default=TransformationType.NONE)
    transformation_config = Column(JSON, nullable=True)  # Store transformation-specific config
    
    # Validation rules
    is_required = Column(Boolean, default=False)
    validation_rules = Column(JSON, nullable=True)  # Store validation rules
    
    # Default values
    default_value = Column(String(500), nullable=True)
    fallback_value = Column(String(500), nullable=True)
    
    # Relationships
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)
    lender = relationship("Lender", back_populates="field_mappings")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FieldMapping(id={self.id}, source='{self.source_field}', target='{self.target_field}')>"


class FieldMappingTemplate(Base):
    __tablename__ = "field_mapping_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g., "personal_loan", "mortgage", "auto_loan"
    
    # Template configuration
    template_config = Column(JSON, nullable=False)  # Store the complete mapping configuration
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_system_template = Column(Boolean, default=False)  # System-provided vs user-created
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FieldMappingTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"

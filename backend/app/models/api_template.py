from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class APITemplate(Base):
    __tablename__ = "api_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g., "authentication", "loan_application", "document_upload"
    
    # Template content
    template_type = Column(String(50), nullable=False)  # "jinja2", "jinja2_python", "jinja2_typescript"
    template_content = Column(Text, nullable=False)  # The actual template content
    
    # Template metadata
    variables = Column(JSON, nullable=True)  # Required variables for the template
    dependencies = Column(JSON, nullable=True)  # Required dependencies/packages
    file_extension = Column(String(20), nullable=True)  # .py, .ts, .js, etc.
    
    # Configuration
    is_system_template = Column(Boolean, default=False)  # System vs user-defined templates
    is_active = Column(Boolean, default=True)
    
    # Versioning
    version = Column(String(50), default="1.0.0")
    parent_template_id = Column(Integer, nullable=True)  # For template inheritance
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<APITemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"

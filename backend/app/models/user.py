from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role and permissions
    role = Column(String(50), default="user")  # admin, user, developer
    permissions = Column(JSON, nullable=True)  # Custom permissions
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(String(500), nullable=True)
    company = Column(String(255), nullable=True)
    
    # API usage tracking
    api_quota = Column(Integer, default=1000)  # Monthly API calls
    api_usage = Column(Integer, default=0)  # Current month usage
    
    # Preferences
    preferences = Column(JSON, nullable=True)  # User preferences
    
    # Security
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"

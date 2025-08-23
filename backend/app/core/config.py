from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Lender API Integration Framework"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5434/lender_framework"
    DATABASE_ECHO: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lender API Integration Framework"
    EXTERNAL_API_KEYS: List[str] = []  # comma-separated in .env supported by pydantic-settings
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:4200",
    ]
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    GENERATED_APIS_DIR: str = "generated_apis"
    TEMPLATES_DIR: str = "api_templates"
    
    # OpenAPI Generator
    OPENAPI_GENERATOR_VERSION: str = "6.6.0"
    OPENAPI_GENERATOR_JAR: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.GENERATED_APIS_DIR, exist_ok=True)
os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)

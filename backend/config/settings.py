from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Caliber Scoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./caliber.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Firebase Settings
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_CLIENT_ID: Optional[str] = None
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    FIREBASE_CLIENT_X509_CERT_URL: Optional[str] = None
    FIREBASE_SERVICE_ACCOUNT_FILE: Optional[str] = None
    
    # OpenAI Settings
    OPENAI_API_KEY: str = "your-openai-api-key"
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # File Storage Settings
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".csv", ".xlsx", ".xls", ".json"]
    UPLOAD_FOLDER: str = "uploads"
    PROCESSED_FOLDER: str = "processed"
    REPORTS_FOLDER: str = "reports"
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Email Settings (for future use)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Scoring Settings
    DEFAULT_SCORING_ALGORITHM: str = "weighted_average"
    MIN_SCORE: float = 0.0
    MAX_SCORE: float = 100.0
    SCORE_PRECISION: int = 2
    
    # AI Analysis Settings
    AI_ANALYSIS_ENABLED: bool = True
    AI_INSIGHT_MAX_LENGTH: int = 500
    AI_RECOMMENDATION_COUNT: int = 5
    
    # Report Settings
    REPORT_FORMATS: List[str] = ["pdf", "csv", "json"]
    DEFAULT_REPORT_FORMAT: str = "pdf"
    REPORT_RETENTION_DAYS: int = 90
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def get_database_url() -> str:
    """Get database URL from environment or settings."""
    return os.getenv("DATABASE_URL", settings.DATABASE_URL)


def get_redis_url() -> str:
    """Get Redis URL from environment or settings."""
    return os.getenv("REDIS_URL", settings.REDIS_URL)


def get_celery_broker_url() -> str:
    """Get Celery broker URL from environment or settings."""
    return os.getenv("CELERY_BROKER_URL", settings.CELERY_BROKER_URL)


def get_celery_result_backend() -> str:
    """Get Celery result backend URL from environment or settings."""
    return os.getenv("CELERY_RESULT_BACKEND", settings.CELERY_RESULT_BACKEND)


def get_firebase_credentials() -> dict:
    """Get Firebase credentials from settings or service account file."""
    import os
    import json
    
    # Check if service account file is specified
    service_account_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
    if service_account_file and os.path.exists(service_account_file):
        try:
            with open(service_account_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading service account file: {e}")
    
    # Fall back to environment variables
    return {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": settings.FIREBASE_AUTH_URI,
        "token_uri": settings.FIREBASE_TOKEN_URI,
        "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL,
    }


def get_openai_config() -> dict:
    """Get OpenAI configuration from settings."""
    return {
        "api_key": settings.OPENAI_API_KEY,
        "model": settings.OPENAI_MODEL,
        "max_tokens": settings.OPENAI_MAX_TOKENS,
        "temperature": settings.OPENAI_TEMPERATURE,
    }


def get_storage_paths() -> dict:
    """Get storage paths configuration."""
    base_path = settings.STORAGE_PATH
    return {
        "base": base_path,
        "uploads": os.path.join(base_path, settings.UPLOAD_FOLDER),
        "processed": os.path.join(base_path, settings.PROCESSED_FOLDER),
        "reports": os.path.join(base_path, settings.REPORTS_FOLDER),
    }


def validate_settings() -> bool:
    """Validate critical settings."""
    required_settings = [
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
    ]
    
    for setting in required_settings:
        if not getattr(settings, setting):
            raise ValueError(f"Required setting {setting} is not configured")
    
    return True 
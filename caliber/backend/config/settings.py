"""
Application settings and configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database - MongoDB
    MONGO_URL: str = "mongodb://localhost:27017/caliber" 
    DATABASE_URL: str = "mongodb://localhost:27017/caliber"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: str = "mok"
    
    # File Storage
    STORAGE_ROOT: str = "/app/caliber/storage"
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    
    # Firebase (for token validation)
    FIREBASE_PROJECT_ID: str = "caliber-auth"
    FIREBASE_PRIVATE_KEY_ID: str = "b167431db42f6c022c0499cbe8a67c0a5f6bbc38"
    FIREBASE_PRIVATE_KEY: str = ""
    
    # Development
    DEV_BYPASS_TOKEN: str = "dev-bypass-token-123"
    DEBUG: bool = False
    
    # Scoring Algorithm Parameters
    SCORE_WEIGHTS_AWARENESS: dict = {
        "ctr": 0.5,
        "cpm": 0.3,  # inverse weight
        "conversion_rate": 0.2
    }
    
    SCORE_WEIGHTS_ACTION: dict = {
        "conversion_rate": 0.5,
        "ctr": 0.3,
        "cpm": 0.2  # inverse weight
    }
    
    CTR_SENSITIVITY_BOOST: float = 0.1
    
    # Score thresholds
    SCORE_THRESHOLD_GOOD: float = 70.0
    SCORE_THRESHOLD_MODERATE: float = 40.0
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
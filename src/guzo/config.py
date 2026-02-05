"""Application configuration with environment variable validation."""

import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB - Required in production
    mongodb_url: str = "mongodb://localhost:27017/guzo_db"
    mongo_db: str = "guzo_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security - SECRET_KEY must be set via environment variable in production
    secret_key: str = "dev-only-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1 hour (reduced from 24 hours)
    
    # Application
    app_name: str = "Guzo Rideshare"
    debug: bool = False  # Default to False for security
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"  # Comma-separated
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is strong enough in production."""
        # In production (non-debug mode), require a strong secret key
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        if not debug_mode and v == "dev-only-change-in-production":
            raise ValueError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if not debug_mode and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        """Validate MongoDB URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URL must start with mongodb:// or mongodb+srv://")
        return v
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        # Map environment variables to settings
        env_prefix = ""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

"""Configuration settings for the FastAPI application.

This module contains all environment-based configuration using Pydantic settings.
All settings are loaded from environment variables with appropriate defaults.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Attributes:
        app_env: Application environment (dev, staging, prod).
        database_url: PostgreSQL connection string.
        frontend_embed_origin: Origin URL for the embed iframe.
        fub_client_id: Follow Up Boss OAuth client ID.
        fub_client_secret: Follow Up Boss OAuth client secret.
        fub_embed_secret: Secret for HMAC signature verification.
        jwt_secret: Secret key for JWT token signing.
        marketing_origin: Origin URL for the marketing site.
        openai_api_key: OpenAI API key for chat completions.
        redis_url: Redis connection string.
        stripe_price_id_monthly: Stripe monthly subscription price ID.
        stripe_secret_key: Stripe secret API key.
        stripe_webhook_secret: Stripe webhook endpoint secret.
    """
    
    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(..., alias="DATABASE_URL")
    frontend_embed_origin: str = Field(..., alias="FRONTEND_EMBED_ORIGIN")
    fub_client_id: str = Field(default="placeholder-client-id", alias="FUB_CLIENT_ID")
    fub_client_secret: str = Field(default="placeholder-client-secret", alias="FUB_CLIENT_SECRET")
    fub_embed_secret: str = Field(..., alias="FUB_EMBED_SECRET")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    marketing_origin: str = Field(..., alias="MARKETING_ORIGIN")
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    redis_url: str = Field(..., alias="REDIS_URL")
    stripe_price_id_monthly: str = Field(..., alias="STRIPE_PRICE_ID_MONTHLY")
    stripe_secret_key: str = Field(..., alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")
    
    # Optional settings with defaults
    cors_origins: list[str] = Field(default_factory=lambda: ["*.followupboss.com"])
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    rate_limit_requests_per_minute: int = Field(default=10, alias="RATE_LIMIT_RPM")
    rate_limit_requests_per_minute_ip: int = Field(default=100, alias="RATE_LIMIT_RPM_IP")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 
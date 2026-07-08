"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Event-Driven Stock Analysis API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/stock_analysis"

    # API
    api_prefix: str = "/api"
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Risk calculation defaults
    risk_free_rate: float = 0.05
    confidence_level: float = 0.95
    lookback_period: int = 252

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

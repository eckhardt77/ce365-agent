"""
CE365 Agent - Configuration
Settings Management mit Pydantic
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application Settings"""

    # Environment
    environment: str = Field(default="production", env="ENVIRONMENT")

    # Edition & License
    edition: str = Field(default="free", env="EDITION")
    license_key: Optional[str] = Field(default=None, env="LICENSE_KEY")
    license_server_url: Optional[str] = Field(
        default="https://license.ce365.local",
        env="LICENSE_SERVER_URL"
    )

    # Anthropic API
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        env="CLAUDE_MODEL"
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ce365:password@postgres:5432/ce365",
        env="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://:password@redis:6379/0",
        env="REDIS_URL"
    )

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost"],
        env="CORS_ORIGINS"
    )

    # Features
    pii_detection_enabled: bool = Field(default=True, env="PII_DETECTION_ENABLED")
    web_search_enabled: bool = Field(default=True, env="WEB_SEARCH_ENABLED")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

    # Data Directory
    data_dir: Path = Field(default=Path("/app/data"), env="DATA_DIR")

    # Edition Limits (per-seat licensing)
    @property
    def max_remediation_runs_per_month(self) -> Optional[int]:
        """Max remediation runs per month based on edition"""
        if self.edition == "free":
            return 5
        return None  # Unlimited for paid editions

    @property
    def max_concurrent_sessions(self) -> int:
        """Max concurrent repair sessions per seat (always 1)"""
        return 1

    @property
    def max_systems_per_month(self) -> Optional[int]:
        """Max active systems per 30-day window"""
        if self.edition == "pro":
            return 10
        return None  # Free: unlimited (eval), Business: unlimited

    @property
    def commercial_use_allowed(self) -> bool:
        """Commercial use requires Pro or Business"""
        return self.edition in ["pro", "business"]

    @property
    def shared_learning_enabled(self) -> bool:
        """Shared learning enabled for Business only"""
        return self.edition == "business"

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    @validator("edition")
    def validate_edition(cls, v):
        """Validate edition"""
        valid_editions = ["free", "pro", "business"]
        if v.lower() not in valid_editions:
            raise ValueError(f"Invalid edition: {v}")
        return v.lower()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global Settings Instance
settings = Settings()


# Create data directory if not exists
settings.data_dir.mkdir(parents=True, exist_ok=True)

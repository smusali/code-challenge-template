"""
Configuration settings for the Weather Data Engineering API.

This module provides centralized configuration management using Pydantic settings
with support for environment variables and default values.
"""


from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database connection configuration."""

    url: str = Field(
        default="postgresql://weather_user:weather_pass@localhost:5432/weather_db",  # pragma: allowlist secret
        description="Database connection URL",
    )
    pool_size: int = Field(
        default=10,
        description="Database connection pool size",
    )
    max_overflow: int = Field(
        default=20,
        description="Database connection pool max overflow",
    )
    pool_timeout: int = Field(
        default=30,
        description="Database connection pool timeout in seconds",
    )


class RedisSettings(BaseModel):
    """Redis cache configuration."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    enabled: bool = Field(
        default=True,
        description="Enable Redis caching",
    )
    ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds",
    )


class APISettings(BaseModel):
    """API server configuration."""

    host: str = Field(
        default="127.0.0.1",
        description="API host address",
    )
    port: int = Field(
        default=8000,
        description="API port number",
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes",
    )
    max_request_size: int = Field(
        default=16 * 1024 * 1024,  # 16MB
        description="Maximum request size in bytes",
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file_path: str = Field(
        default="logs/api.log",
        description="Log file path",
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum log file size in bytes",
    )
    backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )


class SecuritySettings(BaseModel):
    """Security configuration."""

    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens and other cryptographic operations",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )


class Settings(BaseSettings):
    """
    Main application settings.

    Configuration values are loaded from environment variables with fallback to defaults.
    Environment variables should be prefixed with 'WEATHER_API_' for this application.
    """

    # Application metadata
    app_name: str = Field(
        default="Weather Data Engineering API",
        description="Application name",
    )
    version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    description: str = Field(
        default="A comprehensive API for weather data management and analysis",
        description="Application description",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode",
    )

    # API server settings
    API_HOST: str = Field(
        default="127.0.0.1",
        description="API host address",
    )
    API_PORT: int = Field(
        default=8000,
        description="API port number",
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://weather_user:weather_pass@localhost:5432/weather_db",  # pragma: allowlist secret
        description="Database connection URL",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for cryptographic operations",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:5173",
        ],
        description="CORS allowed origins",
    )

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        description="Default page size for paginated responses",
    )
    MAX_PAGE_SIZE: int = Field(
        default=100,
        description="Maximum page size for paginated responses",
    )

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Number of requests allowed per minute",
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )

    # Data processing
    MAX_BULK_INSERT_SIZE: int = Field(
        default=1000,
        description="Maximum number of records for bulk insert operations",
    )
    QUERY_TIMEOUT: int = Field(
        default=30,
        description="Database query timeout in seconds",
    )

    # Caching
    CACHE_TTL_DEFAULT: int = Field(
        default=300,
        description="Default cache TTL in seconds",
    )
    CACHE_TTL_WEATHER_DATA: int = Field(
        default=1800,
        description="Weather data cache TTL in seconds",
    )
    CACHE_TTL_STATISTICS: int = Field(
        default=3600,
        description="Statistics cache TTL in seconds",
    )

    # File processing
    MAX_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file size for uploads in bytes",
    )
    ALLOWED_FILE_EXTENSIONS: list[str] = Field(
        default=[".txt", ".csv", ".json"],
        description="Allowed file extensions for uploads",
    )

    # Weather data specific settings
    WEATHER_DATA_RETENTION_DAYS: int = Field(
        default=10 * 365,  # 10 years
        description="Weather data retention period in days",
    )
    STATS_COMPUTATION_BATCH_SIZE: int = Field(
        default=10000,
        description="Batch size for statistics computation",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

        # Environment variable prefix
        env_prefix = "WEATHER_API_"

        # Allow extra fields from environment
        extra = "allow"


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.

    This function can be used as a dependency in FastAPI routes.
    """
    return settings


# Export commonly used settings
DEBUG = settings.debug
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
LOG_LEVEL = settings.LOG_LEVEL
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
SECRET_KEY = settings.SECRET_KEY
CORS_ORIGINS = settings.CORS_ORIGINS

from typing import Optional, List, Dict, Any, Union
from pydantic import field_validator, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database Configuration
    database_url: str = Field(description="Database connection URL")
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, description="Database pool recycle time in seconds")
    database_pool_pre_ping: bool = Field(default=True, description="Enable database pool pre-ping")
    database_max_overflow: int = Field(default=10, description="Database pool max overflow")
    database_echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")

    # Connection retry settings
    database_retry_attempts: int = Field(default=3, description="Database connection retry attempts")
    database_retry_delay: float = Field(default=1.0, description="Database retry delay in seconds")

    # Redis Configuration
    redis_url: str = Field(description="Redis connection URL")
    redis_pool_size: int = Field(default=20, description="Redis connection pool size")
    redis_retry_attempts: int = Field(default=3, description="Redis connection retry attempts")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")

    # OpenAI Configuration
    openai_api_key: str = Field(description="OpenAI API key")
    openai_org_id: Optional[str] = Field(default=None, description="OpenAI organization ID")
    openai_timeout: int = Field(default=120, description="OpenAI API timeout in seconds")
    openai_max_retries: int = Field(default=3, description="OpenAI API max retries")
    default_model: str = Field(default="gpt-4", description="Default OpenAI model")

    # Security Configuration
    jwt_secret: str = Field(description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")
    api_key_hash_salt: str = Field(description="API key hashing salt")

    # Security headers and HTTPS
    force_https: bool = Field(default=False, description="Force HTTPS redirects")
    secure_cookies: bool = Field(default=False, description="Use secure cookies")

    # Rate Limiting Configuration
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format: json or text")
    log_to_file: bool = Field(default=False, description="Enable file logging")
    log_file_path: str = Field(default="logs/app.log", description="Log file path")
    log_rotation_size: str = Field(default="100 MB", description="Log rotation size")
    log_retention_days: int = Field(default=30, description="Log retention in days")

    # Monitoring and Health Checks
    health_check_timeout: int = Field(default=10, description="Health check timeout in seconds")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")

    # CORS Configuration
    allowed_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins"
    )
    allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods"
    )
    allowed_headers: List[str] = Field(
        default=["*"],
        description="CORS allowed headers"
    )

    # Production-specific settings
    worker_processes: int = Field(default=1, description="Number of worker processes")
    worker_connections: int = Field(default=1000, description="Worker connections")
    keepalive_timeout: int = Field(default=65, description="Keep-alive timeout")

    # Backup and maintenance
    backup_enabled: bool = Field(default=False, description="Enable automated backups")
    backup_schedule: str = Field(default="0 2 * * *", description="Backup cron schedule")
    maintenance_mode: bool = Field(default=False, description="Enable maintenance mode")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # Handle comma-separated string
            if v.strip():
                return [origin.strip() for origin in v.split(",")]
            else:
                return []
        elif isinstance(v, list):
            return v
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_environments = {"development", "staging", "production"}
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("Database URL is required")
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must use PostgreSQL with asyncpg driver")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v_upper

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration overrides."""
        if self.environment == "production":
            return {
                "debug": False,
                "database_echo": False,
                "log_level": "WARNING",
                "force_https": True,
                "secure_cookies": True,
                "rate_limit_enabled": True,
                "metrics_enabled": True,
                "log_to_file": True,
            }
        elif self.environment == "staging":
            return {
                "debug": False,
                "database_echo": False,
                "log_level": "INFO",
                "force_https": True,
                "secure_cookies": True,
                "rate_limit_enabled": True,
                "metrics_enabled": True,
                "log_to_file": True,
            }
        else:  # development
            return {
                "debug": True,
                "database_echo": self.debug,
                "log_level": "DEBUG",
                "force_https": False,
                "secure_cookies": False,
                "rate_limit_enabled": False,
                "metrics_enabled": False,
                "log_to_file": False,
            }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_parse_none_str="None",
        extra="ignore"
    )


# Global settings instance
settings = Settings()
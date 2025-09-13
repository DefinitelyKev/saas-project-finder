from typing import Optional, List, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database
    database_url: str = ""
    database_pool_size: int = 20

    # Redis
    redis_url: str = ""
    cache_ttl: int = 3600

    # OpenAI
    openai_api_key: str = ""
    openai_org_id: Optional[str] = None
    default_model: str = "gpt-4"

    # Security
    jwt_secret: str = ""
    api_key_hash_salt: str = ""

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Environment
    environment: str = "development"
    debug: bool = False

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()
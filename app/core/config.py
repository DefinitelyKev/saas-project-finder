from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SaaS AI Backend"
    VERSION: str = "0.1.0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000"
    ])
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_POOL_OVERFLOW: int = Field(default=20, env="DATABASE_POOL_OVERFLOW")
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # MCP
    MCP_ENABLED: bool = Field(default=True, env="MCP_ENABLED")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Multi-tenancy
    DEFAULT_TENANT_DB_PREFIX: str = "tenant_"
    MAX_TENANTS_PER_HOST: int = Field(default=1000, env="MAX_TENANTS_PER_HOST")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")


settings = Settings()
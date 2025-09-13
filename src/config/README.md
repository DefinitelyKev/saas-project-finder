# Configuration Module

This directory contains all application configuration, constants, and environment-based settings. The configuration system uses Pydantic for type-safe settings management with automatic validation and environment variable integration.

## Structure

```
config/
├── settings.py         # Environment-based application settings
└── constants.py        # Application constants and enums
```

## Settings Management (`settings.py`)

### Purpose
Centralized configuration management using Pydantic Settings for type safety, validation, and environment variable integration.

### Configuration Categories

#### Database Configuration
```python
database_url: str                 # PostgreSQL connection string
database_pool_size: int = 20     # Connection pool size
```
- **Purpose**: Database connection and performance settings
- **Environment Variables**: `DATABASE_URL`, `DATABASE_POOL_SIZE`
- **Validation**: URL format validation, positive integer for pool size
- **Usage**: Used by SQLAlchemy engine initialization

#### Redis Configuration
```python
redis_url: str                    # Redis connection string
cache_ttl: int = 3600            # Default cache TTL in seconds
```
- **Purpose**: Caching and rate limiting configuration
- **Environment Variables**: `REDIS_URL`, `CACHE_TTL`
- **Validation**: URL format validation, positive integer for TTL
- **Usage**: Used by Redis client and caching middleware

#### OpenAI Configuration
```python
openai_api_key: str              # OpenAI API key (required)
openai_org_id: Optional[str]     # OpenAI organization ID
default_model: str = "gpt-4"     # Default AI model
```
- **Purpose**: AI service integration settings
- **Environment Variables**: `OPENAI_API_KEY`, `OPENAI_ORG_ID`, `DEFAULT_MODEL`
- **Security**: API key is sensitive and should never be logged
- **Validation**: Non-empty string for API key

#### Security Configuration
```python
jwt_secret: str                  # JWT signing secret
api_key_hash_salt: str          # Salt for API key hashing
```
- **Purpose**: Cryptographic operations and authentication
- **Environment Variables**: `JWT_SECRET`, `API_KEY_HASH_SALT`
- **Security**: Both values are sensitive and should be long, random strings
- **Usage**: Used by ApiKey value object and JWT operations

#### Rate Limiting Configuration
```python
rate_limit_requests: int = 100   # Requests per minute
rate_limit_window: int = 60      # Rate limit window in seconds
```
- **Purpose**: API protection and fair usage enforcement
- **Environment Variables**: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`
- **Defaults**: Conservative limits for production safety
- **Override**: Per-tenant limits defined in constants.py

#### Logging Configuration
```python
log_level: str = "INFO"          # Logging level
log_format: str = "json"         # Log format (json/text)
```
- **Purpose**: Application logging behavior
- **Environment Variables**: `LOG_LEVEL`, `LOG_FORMAT`
- **Options**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Production**: Use INFO level and JSON format for structured logging

#### Environment Configuration
```python
environment: str = "development" # Environment name
debug: bool = False             # Debug mode flag
```
- **Purpose**: Environment-specific behavior control
- **Environment Variables**: `ENVIRONMENT`, `DEBUG`
- **Values**: development, staging, production
- **Debug Mode**: Enables detailed error messages and auto-reload

#### CORS Configuration
```python
allowed_origins: List[str]       # CORS allowed origins
```
- **Purpose**: Cross-origin request configuration for Next.js frontends
- **Environment Variables**: `ALLOWED_ORIGINS` (comma-separated)
- **Validation**: Automatic parsing of comma-separated values
- **Security**: Restrict to known frontend domains in production

### Configuration Loading

#### Environment File Support
```python
class Config:
    env_file = ".env"
    case_sensitive = False
```
- Automatically loads from `.env` file
- Environment variables override file settings
- Case-insensitive variable names
- Supports `.env.local`, `.env.production` variants

#### Custom Validators
```python
@validator("allowed_origins", pre=True)
def parse_origins(cls, v: Any) -> List[str]:
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    return v

@validator("debug", pre=True)
def parse_debug(cls, v: Any) -> bool:
    if isinstance(v, str):
        return v.lower() in ("true", "1", "yes", "on")
    return v
```

#### Global Settings Instance
```python
settings = Settings()  # Singleton instance
```
- Loaded once at application startup
- Available throughout the application
- Validates all settings during initialization
- Fails fast if required settings are missing

## Application Constants (`constants.py`)

### Purpose
Defines application-wide constants, enums, and configuration values that don't change between environments.

### Enums and Constants

#### Execution Status
```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```
- **Purpose**: Standardize execution state tracking
- **Usage**: Used in Execution entity and API responses
- **Type**: String enum for database compatibility

#### Tenant Tiers
```python
class TenantTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
```
- **Purpose**: Define subscription tiers with different capabilities
- **Usage**: Used in Tenant entity and billing logic
- **Expansion**: Easy to add new tiers

#### Agent Types
```python
class AgentType(str, Enum):
    CUSTOMER_SUPPORT = "customer-support"
    DATA_ANALYST = "data-analyst"
    CONTENT_WRITER = "content-writer"
    CODE_REVIEWER = "code-reviewer"
```
- **Purpose**: Enumerate available agent types
- **Usage**: Used in agent configuration and validation
- **Maintenance**: Updated when new agents are added

### Tier-Based Limits
```python
TIER_LIMITS = {
    TenantTier.FREE: {
        "monthly_tokens": 10000,
        "requests_per_minute": 10,
        "max_sessions": 5,
    },
    TenantTier.PRO: {
        "monthly_tokens": 100000,
        "requests_per_minute": 50,
        "max_sessions": 25,
    },
    TenantTier.ENTERPRISE: {
        "monthly_tokens": 1000000,
        "requests_per_minute": 200,
        "max_sessions": 100,
    },
}
```
- **Purpose**: Define resource limits per subscription tier
- **Usage**: Used by Tenant entity for limit enforcement
- **Flexibility**: Easy to adjust limits or add new resources

### API Configuration
```python
API_V1_PREFIX = "/api/v1"
API_TITLE = "AI Backend API"
API_DESCRIPTION = "Central AI Multi-Tenant Backend for SaaS Projects"
API_VERSION = "1.0.0"
```
- **Purpose**: API metadata and versioning
- **Usage**: Used by FastAPI app configuration
- **Versioning**: Supports multiple API versions

### Cache Key Patterns
```python
CACHE_KEY_TENANT = "tenant:{tenant_id}"
CACHE_KEY_AGENT = "agent:{agent_id}"
CACHE_KEY_RATE_LIMIT = "rate_limit:{tenant_id}"
CACHE_KEY_USAGE = "usage:{tenant_id}:{period}"
```
- **Purpose**: Standardize Redis cache key formats
- **Usage**: Used throughout caching layer
- **Consistency**: Prevents cache key conflicts
- **Namespacing**: Groups related cache entries

## Configuration Usage Patterns

### In Application Code
```python
from src.config.settings import settings

# Database connection
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    echo=settings.debug,
)

# OpenAI client
client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    organization=settings.openai_org_id,
)
```

### In Test Code
```python
from src.config.settings import settings

@pytest.fixture
def test_settings():
    original_debug = settings.debug
    settings.debug = True
    yield settings
    settings.debug = original_debug
```

### Environment-Specific Configuration
```bash
# Development (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_backend_dev
DEBUG=true
LOG_LEVEL=DEBUG

# Production (.env.production)
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/ai_backend
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## Configuration Validation

### Type Safety
- All settings have explicit type hints
- Pydantic validates types at runtime
- IDE support for autocomplete and type checking
- Automatic serialization/deserialization

### Required vs Optional
- Required settings raise errors if missing
- Optional settings have sensible defaults
- Environment variables override defaults
- Validation occurs at application startup

### Security Validation
- Sensitive settings are marked appropriately
- No default values for secrets
- Validation for URL formats and connection strings
- Length requirements for cryptographic secrets

## Environment Management

### Development Environment
```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
vim .env

# Settings loaded automatically
make dev
```

### Production Environment
```bash
# Set environment variables
export OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql://..."

# Or use environment-specific file
docker-compose -f docker-compose.prod.yml up
```

### Docker Configuration
```yaml
# docker-compose.yml
environment:
  - DATABASE_URL=postgresql+asyncpg://ai_user:ai_password@postgres:5432/ai_backend
  - REDIS_URL=redis://redis:6379/0
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - ENVIRONMENT=development
```

## Configuration Security

### Secret Management
- Never commit secrets to version control
- Use environment variables or secret managers
- Rotate secrets regularly
- Different secrets per environment

### Access Control
- Limit who can view production configuration
- Use IAM roles for cloud secret access
- Audit configuration changes
- Monitor for unauthorized access

### Validation and Monitoring
- Validate configuration on startup
- Monitor for configuration drift
- Alert on invalid configuration
- Regular security audits

The configuration system provides type-safe, validated settings management while supporting multiple environments and maintaining security best practices.
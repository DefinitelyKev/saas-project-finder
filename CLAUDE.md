# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-tenant AI-powered SaaS backend built with FastAPI, designed for micro-SaaS applications. It uses PostgreSQL with schema-per-tenant isolation, Redis for caching, and integrates with OpenAI and Model Context Protocol (MCP) for AI features.

## Development Commands

### Environment Setup
```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your configuration (DATABASE_URL, REDIS_URL, OPENAI_API_KEY, SECRET_KEY)

# Install dependencies
poetry install

# Start services with Docker Compose
docker-compose up -d

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Database Operations
```bash
# Run database migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "Description of changes"
```

### Testing and Quality
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Code formatting and linting
black app/
isort app/
flake8 app/

# Type checking (ALWAYS run both before committing)
mypy app/
pyright app/

# Run all quality checks in sequence
black app/ && isort app/ && flake8 app/ && mypy app/ && pyright app/

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

### Docker Development
```bash
# Start all services
docker-compose up -d

# Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f api

# Rebuild API container
docker-compose build api
```

## Architecture Overview

### Multi-Tenant Design
- **Database Strategy**: Schema-per-tenant with shared application infrastructure
- **Tenant Identification**: Handled by `TenantMiddleware` in `app/api/middleware/tenant_middleware.py`
- **Isolation**: Each tenant gets their own database schema and cached resources

### Core Components
- **Dependency Injection**: Uses `dependency-injector` with configuration in `app/core/container.py`
- **Database**: Async SQLAlchemy 2.0 with PostgreSQL, connection managed via `app/infrastructure/database/connection.py`
- **Caching**: Redis client in `app/infrastructure/cache/redis_client.py`
- **AI Integration**: OpenAI client and MCP client in `app/infrastructure/external/`

### Domain Structure
The codebase follows Domain-Driven Design (DDD) principles:
- `app/domains/tenant/`: Tenant management and multi-tenancy
- `app/domains/user/`: User management and authentication
- `app/domains/project/`: Project and AI session models
- `app/domains/ai_agent/`: AI agent functionality

### Service Layer
Business logic is contained in `app/services/`:
- `tenant_service.py`: Tenant operations and schema management
- `ai_service.py`: AI integration and MCP tool coordination
- `auth_service.py`: Authentication and authorization

### API Layer
- API endpoints in `app/api/v1/endpoints/`
- Custom middleware for tenant resolution, logging, and metrics
- Dependency injection wired through container configuration

## Key Configuration

### Environment Variables
All configuration is handled through `app/core/config.py` using Pydantic settings:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key
- `SECRET_KEY`: JWT signing key (must be secure in production)
- `MCP_ENABLED`: Enable Model Context Protocol features

### Multi-Tenant Settings
- `DEFAULT_TENANT_DB_PREFIX`: Prefix for tenant schemas (default: "tenant_")
- `MAX_TENANTS_PER_HOST`: Maximum tenants per deployment (default: 1000)

## Type Checking Requirements

### Strict Type Checking Rules
This project enforces strict type checking via both mypy and Pylance/Pyright. **ALWAYS** run type checking before committing:

```bash
# Both commands must pass without errors
mypy app/
pyright app/
```

### Type Checking Configuration
- `pyproject.toml`: Contains mypy configuration with strict rules
- `pyrightconfig.json`: Contains Pylance/Pyright configuration with comprehensive checks
- **typeCheckingMode**: Set to "strict" - all type issues must be resolved

### Required Type Annotations
- All function parameters and return types must be annotated
- All class attributes must have type annotations
- No `Any` types allowed without explicit justification
- Generic types must be fully specified

## Development Patterns

### Adding New Domains
1. Create domain models in `app/domains/{domain}/`
2. Add service layer in `app/services/`
3. Create API endpoints in `app/api/v1/endpoints/`
4. Register dependencies in `app/core/container.py`
5. Wire endpoints in container configuration

### Database Schema Changes
Always use Alembic for database migrations. The application supports multiple tenant schemas, so migrations must account for this architecture.

### AI Integration
- OpenAI integration uses the Assistants API with streaming support
- MCP (Model Context Protocol) provides standardized tool interfaces
- AI services handle both OpenAI and MCP tool coordination

## Health Checks

- Basic health: `GET /api/v1/health`
- Detailed health (with dependencies): `GET /api/v1/health/detailed`

## Monitoring

- Prometheus metrics via `MetricsMiddleware`
- Structured logging with `structlog`
- Request tracing with correlation IDs
- Tenant-aware logging context
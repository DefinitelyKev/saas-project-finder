# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a centralized AI Python multi-tenant backend that serves multiple Next.js SaaS projects through pre-configured AI agents. The backend handles all AI agent logic while frontends make simple API calls.

## Development Environment

This project uses a Python virtual environment with all required packages pre-installed. The codebase enforces strict type checking with Pylance/Pyright.

### Environment Setup

```cmd
# Copy environment file and configure
copy .env.example .env

# Start all services (builds and starts containers)
docker-compose up --build

# Register a test tenant
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "tier": "free",
    "allowed_agents": ["customer-support", "data-analyst"]
  }'
```

### Type Checking Requirements

- **All code must pass strict type checking with pyright/Pylance**
- Use proper type hints for all function parameters and return types
- Import types from `typing` module when needed
- Use `Optional[T]` for nullable types
- Avoid `Any` type unless absolutely necessary

Pyright for local type checking:

```cmd
./venv-python -m pyright src/
```

### Development Workflow

```cmd
# Start development server
docker-compose up --build

# Testing
./venv-python -m pytest tests/ -v

# Code formatting and linting
./venv-python -m black src/
./venv-python -m isort src/

# Type checking
./venv-python -m pyright src/
```

### Docker Operations

```cmd
# Start all services (builds and starts containers)
docker-compose up --build

# View application logs
docker-compose logs -f ai-backend

# Open shell in container
docker-compose exec ai-backend bash

# Stop all services
docker-compose down
```

### Database Management

#### Database Connection

The application uses PostgreSQL with asyncpg driver. Database runs in Docker with all services.

#### Connecting to the Database

There are multiple ways to connect and view your database:

**pgAdmin Web Interface**

```cmd
# Access pgAdmin at: http://localhost:5050
# Login: admin@ai-backend.com / admin
```

**Connection details:**
- Host: `postgres`
- Port: `5432`
- Database: `ai_backend`
- Username: `ai_user`
- Password: `ai_password`

**Command Line Access**

```cmd
# Connect to PostgreSQL directly
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend

# List all databases
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "\l"

# List all tables
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "\dt"

# Describe table structure
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "\d table_name"

# Query specific table
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "SELECT * FROM tenants LIMIT 5;"
```

#### Testing API Endpoints

**Test tenant registration:**

```cmd
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "tier": "free",
    "allowed_agents": ["customer-support", "data-analyst"]
  }'
```

#### Running Migrations

**Method 1: Direct SQL Execution (Recommended)**

```cmd
# Create SQL file with your schema changes
# Execute SQL script directly
docker exec -i saas-project-finder-postgres-1 psql -U ai_user -d ai_backend < your_migration.sql

# Example: Create basic tables
docker exec -i saas-project-finder-postgres-1 psql -U ai_user -d ai_backend < create_tables.sql
```

**Method 2: Alembic Migrations**

```cmd
# Create new migration
./venv-python -m alembic revision --autogenerate -m "description of changes"

# Run migrations (if alembic connection works)
./venv-python -m alembic upgrade head

# View current migration status
./venv-python -m alembic current

# View migration history
./venv-python -m alembic history
```

#### Database Operations

**Reset database (destroys all data!)**

```cmd
docker-compose down -v
docker-compose up --build
```

**Backup database**

```cmd
# Create backup
docker exec saas-project-finder-postgres-1 pg_dump -U ai_user -d ai_backend > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i saas-project-finder-postgres-1 psql -U ai_user -d ai_backend < backup_file.sql
```

**Insert sample data**

```cmd
# Add test tenant
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "
INSERT INTO tenants (name, api_key_hash, current_month)
VALUES ('Test Tenant', 'test123hash', '2025-09')
ON CONFLICT DO NOTHING;"

# Verify data
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "SELECT id, name, tier FROM tenants;"
```

#### Viewing Database Contents

**Check table contents**

```cmd
# Count records in each table
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "
SELECT 'tenants' as table_name, count(*) as count FROM tenants
UNION ALL
SELECT 'agents' as table_name, count(*) as count FROM agents
UNION ALL
SELECT 'executions' as table_name, count(*) as count FROM executions
UNION ALL
SELECT 'sessions' as table_name, count(*) as count FROM sessions
UNION ALL
SELECT 'usage_logs' as table_name, count(*) as count FROM usage_logs;"

# View recent executions
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "
SELECT e.id, t.name as tenant, e.agent_id, e.status, e.created_at
FROM executions e
JOIN tenants t ON e.tenant_id = t.id
ORDER BY e.created_at DESC
LIMIT 10;"
```

#### Database Health Checks

**Monitor database status**

```cmd
# Check if database is running
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "SELECT version();"

# Check database size
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;"

# Check table sizes
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(tablename::text)) as size
FROM pg_tables
WHERE schemaname='public';"
```

## Architecture Overview

### Clean Architecture Layers

- **Domain Layer** (`src/domain/`): Core business entities, value objects, and domain exceptions
- **Application Layer** (`src/application/`): CQRS commands, queries, and handlers
- **Infrastructure Layer** (`src/infrastructure/`): External services (database, AI, caching)
- **API Layer** (`src/api/`): FastAPI routes, middleware, and request/response schemas

### Detailed Module Documentation

Each major directory contains a `README.md` file with comprehensive details:

- **`src/domain/README.md`**: Domain entities, business rules, and value objects
- **`src/infrastructure/README.md`**: External service integrations and data persistence
- **`src/api/README.md`**: HTTP interface, middleware stack, and route handlers
- **`src/agents/README.md`**: AI agent configurations and tool definitions
- **`src/application/README.md`**: CQRS implementation and business use cases
- **`src/services/README.md`**: Domain services and business logic coordination
- **`src/config/README.md`**: Configuration management and application constants

**When working on specific modules, always read the corresponding README.md first for detailed context.**

### Multi-Tenancy Design

The system uses API key-based multi-tenancy where:

1. Each SaaS project is a "tenant" with unique API key
2. Tenants have different tiers (Free/Pro/Enterprise) with usage limits
3. Middleware resolves tenant from `X-API-Key` header on every request
4. All data is isolated by tenant_id

### Agent System Architecture

Agents are pre-configured in `src/agents/config.py` with:

- **System prompts**: Define agent behavior and personality
- **Tools**: Built-in functions the agent can call
- **Parameter schemas**: Define expected input parameters
- **Execution limits**: Token limits, temperature, etc.

The agent execution flow:

1. API request → `AgentExecutor` → `OpenAIClientWrapper` → OpenAI API
2. If tools are called → `ToolExecutor` handles function execution
3. Response returned to client (sync, streaming, or async)

### Database Design

- **TenantModel**: Stores tenant info, API keys, usage limits
- **AgentModel**: Agent configurations (though primarily in code)
- **ExecutionModel**: Tracks all agent executions for billing/monitoring
- **SessionModel**: Manages stateful conversations
- **UsageLogModel**: Detailed usage tracking for billing

### Key Components

#### Middleware Stack (Order Matters)

1. **CORS**: Handles cross-origin requests for Next.js frontends
2. **TenantMiddleware**: Resolves tenant from API key, stores in request.state
3. **AuthMiddleware**: Validates API key presence
4. **RateLimitMiddleware**: Enforces per-tenant rate limits

#### Agent Execution Patterns

- **Synchronous**: Direct API call, immediate response
- **Streaming**: Server-sent events for real-time responses
- **Asynchronous**: Background jobs with job ID polling

## Key Files and Their Purposes

### Core Configuration

- `src/config/settings.py`: Environment-based configuration using Pydantic
- `src/config/constants.py`: Enums, tier limits, cache keys
- `src/agents/config.py`: All agent definitions and configurations

### Domain Entities

- `src/domain/entities/tenant.py`: Tenant business logic and usage tracking
- `src/domain/entities/agent.py`: Agent configuration and validation
- `src/domain/entities/execution.py`: Agent execution state management
- `src/domain/entities/session.py`: Conversation session management

### Infrastructure Services

- `src/infrastructure/ai/agent_executor.py`: Main agent execution orchestrator
- `src/infrastructure/ai/openai_client.py`: OpenAI API wrapper with streaming
- `src/infrastructure/ai/tool_executor.py`: Handles agent tool function calls
- `src/infrastructure/persistence/database.py`: Async SQLAlchemy setup

### API Layer

- `src/api/v1/routes/agents.py`: Agent discovery and execution endpoints
- `src/api/v1/routes/auth.py`: Tenant registration and validation
- `src/api/v1/dependencies.py`: FastAPI dependency injection setup

## Working with Agents

### Adding New Agents

1. Add configuration to `AGENT_CONFIGS` in `src/agents/config.py`
2. Define tools in `src/infrastructure/ai/tool_executor.py`
3. Test with `POST /api/v1/agents/{agent_id}/execute`

### Agent Configuration Structure

```python
"agent-id": {
    "name": "Human-readable name",
    "description": "What this agent does",
    "model": "gpt-4",
    "system_prompt": "Detailed instructions...",
    "tools": [{"type": "function", "name": "tool_name", ...}],
    "parameters_schema": {"type": "object", "properties": {...}},
    "max_tokens": 1000,
    "temperature": 0.7
}
```

### Available Pre-configured Agents

- `customer-support`: Ticket analysis, knowledge base search, escalation
- `data-analyst`: SQL queries, data visualization, business insights
- `content-writer`: SEO content creation, keyword research
- `code-reviewer`: Static analysis, security audits, improvement suggestions

## Database Operations

### Running Migrations

Use Alembic for database schema changes:

```bash
./venv-python -m alembic revision --autogenerate -m "Description"
./venv-python -m alembic upgrade head
```

### Repository Pattern

All database access goes through repositories in `src/infrastructure/persistence/repositories/`

- Repositories convert between SQLAlchemy models and domain entities
- Use async/await throughout
- Handle database transactions in the repository layer

## Error Handling

### Domain Exceptions

Custom exceptions in `src/domain/exceptions.py`:

- `TenantNotFound`: Invalid API key or inactive tenant
- `AgentNotFound`: Requested agent doesn't exist
- `RateLimitExceeded`: Tenant exceeded rate limits
- `UsageLimitExceeded`: Monthly token limit reached

### Error Response Format

All API errors return consistent JSON:

```json
{
  "error": "ErrorType",
  "detail": "Human-readable description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Testing and Quality

### Test Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for database operations
- `tests/e2e/`: End-to-end API tests

### Code Quality Tools

- **Black**: Code formatting (120 character line length)
- **isort**: Import sorting
- **pyright**: Strict type checking (required - matches Pylance)
- **pytest**: Testing framework with async support

### Virtual Environment Usage

**IMPORTANT**: Always use the virtual environment Python wrapper when running Python commands:

```bash
./venv-python          # Linux/WSL
./venv-python.bat      # Windows Command Prompt
./venv-python.ps1      # Windows PowerShell
```

These wrapper scripts ensure the virtual environment is used correctly without needing the full path.

### Code Quality Standards

When making any code changes:

1. Always use the virtual environment Python wrapper: `./venv-python`
2. Add proper type hints to all new functions and methods
3. Use `from typing import` for complex types like `Dict`, `List`, `Optional`, `Union`
4. Run `./venv-python -m pyright src/` before submitting changes
5. Fix all type errors - no `# type: ignore` comments without justification
6. **Keep code simple and clean - don't overcomplicate things**

## Environment Variables

Required for development:

- `OPENAI_API_KEY`: OpenAI API key for agent execution
- `JWT_SECRET`: Secret for JWT token signing
- `API_KEY_HASH_SALT`: Salt for API key hashing
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## Security Considerations

- API keys are hashed with salt before database storage
- Rate limiting prevents abuse per tenant tier
- Input validation on all agent parameters
- No secrets in logs or error messages
- CORS properly configured for Next.js frontends

## Monitoring and Debugging

### Application Logs

```bash
docker-compose logs -f ai-backend
```

### Database Admin

pgAdmin: http://localhost:5050 (admin@ai-backend.com / admin)

### API Documentation

Swagger UI: http://localhost:8000/docs

### Health Checks

```bash
curl http://localhost:8000/health
```

## Integration with Next.js Frontends

Frontends call the backend with tenant API keys:

```javascript
const response = await fetch("/api/v1/agents/customer-support/execute", {
  method: "POST",
  headers: {
    "X-API-Key": "tenant-api-key",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    parameters: { customer_message: "Help me" },
  }),
});
```

Each Next.js SaaS project gets isolated access based on their tenant configuration and allowed agents.

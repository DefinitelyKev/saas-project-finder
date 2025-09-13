# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a centralized AI Python multi-tenant backend that serves multiple Next.js SaaS projects through pre-configured AI agents. The backend handles all AI agent logic while frontends make simple API calls.

## Development Environment

This project uses a Python virtual environment with all required packages pre-installed. The codebase enforces strict type checking with Pylance/Pyright.

### Environment Setup
```bash
cp .env.example .env  # Configure OpenAI API key and secrets
source .venv/bin/activate  # Activate virtual environment (Linux/Mac)
# OR
.venv\Scripts\activate  # Activate virtual environment (Windows)
make docker-up        # Start all services (PostgreSQL, Redis, FastAPI)
make create-tenant    # Create test tenant and get API key
```

### Type Checking Requirements
- **All code must pass strict type checking with pyright/Pylance**
- Use proper type hints for all function parameters and return types
- Import types from `typing` module when needed
- Use `Optional[T]` for nullable types
- Avoid `Any` type unless absolutely necessary

Install pyright for local type checking:
```bash
pip install pyright
pyright src/  # Check all source files
```

### Development Workflow
```bash
make dev              # Run development server with hot reload
make test             # Run all tests
make test-cov         # Run tests with coverage report
make format           # Format code with black and isort
make lint             # Run linting (black, isort, mypy, pyright)
make typecheck        # Run type checking only (pyright)
```

### Docker Operations
```bash
make docker-build     # Build Docker image
make docker-logs      # View application logs
make docker-shell     # Open shell in container
make docker-down      # Stop all services
```

### Database Management
```bash
make db-upgrade       # Run Alembic migrations
make db-reset         # Reset database (destroys data!)
```

## Architecture Overview

### Clean Architecture Layers
- **Domain Layer** (`src/domain/`): Core business entities, value objects, and domain exceptions
- **Application Layer** (`src/application/`): CQRS commands, queries, and handlers
- **Infrastructure Layer** (`src/infrastructure/`): External services (database, AI, caching)
- **API Layer** (`src/api/`): FastAPI routes, middleware, and request/response schemas

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
alembic revision --autogenerate -m "Description"
alembic upgrade head
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
- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting
- **mypy**: Type checking (strict mode enabled)
- **pyright**: Strict type checking (required - matches Pylance)
- **pytest**: Testing framework with async support

### Strict Typing Standards
When making any code changes:
1. Always activate the virtual environment first
2. Add proper type hints to all new functions and methods
3. Use `from typing import` for complex types like `Dict`, `List`, `Optional`, `Union`
4. Run `pyright src/` before submitting changes
5. Fix all type errors - no `# type: ignore` comments without justification

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
Structured logging with correlation IDs:
```bash
make docker-logs  # View application logs
```

### Database Admin
Access PostgreSQL admin interface:
```bash
open http://localhost:5050  # pgAdmin (admin@ai-backend.com / admin)
```

### API Documentation
Auto-generated OpenAPI docs:
```bash
open http://localhost:8000/docs  # Swagger UI
```

### Health Checks
```bash
curl http://localhost:8000/health
```

## Integration with Next.js Frontends

Frontends call the backend with tenant API keys:
```javascript
const response = await fetch('/api/v1/agents/customer-support/execute', {
  method: 'POST',
  headers: {
    'X-API-Key': 'tenant-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    parameters: { customer_message: "Help me" }
  })
});
```

Each Next.js SaaS project gets isolated access based on their tenant configuration and allowed agents.
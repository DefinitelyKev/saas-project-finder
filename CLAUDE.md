# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

This is a centralized AI Python multi-tenant backend that serves multiple Next.js SaaS projects through pre-configured AI agents. The backend handles all AI agent logic while frontends make simple API calls.

## Quick Start

```bash
# Setup and start (includes MCP server)
copy .env.example .env
docker-compose up --build

# Register test tenant
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company", "tier": "free", "allowed_agents": ["customer-support"]}'
```

## Development Commands

```bash
# Type checking (REQUIRED before commits)
./venv-python -m pyright src/

# Testing
./venv-python -m pytest tests/ -v

# Code quality
./venv-python -m black src/
./venv-python -m isort src/

# Docker operations
docker-compose up --build
docker-compose logs -f ai-backend
docker-compose down
```

## Database Operations

**Connection:**

- pgAdmin: http://localhost:5050 (admin@ai-backend.com / admin)
- Direct: `docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend`

**Common queries:**

```bash
# List tables
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "\dt"

# View tenants
docker exec saas-project-finder-postgres-1 psql -U ai_user -d ai_backend -c "SELECT id, name, tier FROM tenants;"
```

**Migrations:**

```bash
# Direct SQL (recommended)
docker exec -i saas-project-finder-postgres-1 psql -U ai_user -d ai_backend < migration.sql

# Alembic
./venv-python -m alembic revision --autogenerate -m "description"
./venv-python -m alembic upgrade head
```

## Architecture

**Clean Architecture Layers:**

- `src/domain/`: Business entities and exceptions
- `src/application/`: CQRS commands/queries
- `src/infrastructure/`: External services (DB, AI, cache)
- `src/api/`: FastAPI routes and middleware

**Key Files:**

- `src/config/settings.py`: Environment configuration
- `src/agents/config.py`: Agent definitions
- `src/infrastructure/ai/agent_executor.py`: Agent execution
- `src/infrastructure/persistence/database.py`: Database setup
- `src/main.py`: FastAPI application

## MCP Server (SaaS Discovery Tools)

MCP server starts automatically with `docker-compose up --build` on port 8080.

```bash
# Test tools
./venv-python tests/test_mcp_tools.py

# Manual start (if needed for development)
./venv-python scripts/simple_mcp_server.py
```

**Available tools:** search_producthunt, search_reddit_startups, search_hackernews, analyze_market_size, analyze_competition, check_domain_availability, analyze_google_trends

## Multi-Tenancy

- API key-based tenant isolation
- Middleware resolves tenant from `X-API-Key` header
- All data isolated by tenant_id
- Tiers: Free/Pro/Enterprise with usage limits

## Agent System

Agents configured in `src/agents/config.py`:

- System prompts define behavior
- Tools provide function calling
- Parameter schemas validate input
- Execution limits control usage

**Execution patterns:** Sync, streaming (SSE), async (job polling)

## Code Standards

**IMPORTANT: Keep code simple and clean - don't overcomplicate things**

**Before writing new code:**
1. **Check if functionality already exists** - Search codebase first
2. **Use existing patterns** - Follow established conventions
3. **Prefer editing over creating** - Modify existing files when possible
4. **Keep it simple** - Avoid complex solutions when simple ones work

**Type Checking (REQUIRED):**
- All code must pass `./venv-python -m pyright src/`
- Use proper type hints for all functions
- Import from `typing` module for complex types
- Avoid `Any` type

**Virtual Environment:**
Always use `./venv-python` wrapper script.

## Environment Variables

**Required:**

- `OPENAI_API_KEY`: OpenAI API access
- `JWT_SECRET`: JWT signing
- `API_KEY_HASH_SALT`: API key hashing
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection

**MCP/External APIs:**

- `MCP_SERVER_URL`: MCP server (default: http://localhost:8080)
- `PRODUCTHUNT_API_TOKEN`: ProductHunt access
- `REDDIT_CLIENT_ID/SECRET`: Reddit API
- `TWITTER_BEARER_TOKEN`: Twitter API

## API Testing

```bash
# Health check
curl http://localhost:8000/health

# API docs
http://localhost:8000/docs

# Agent execution
curl -X POST http://localhost:8000/api/v1/agents/customer-support/execute \
  -H "X-API-Key: tenant-key" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"customer_message": "Help me"}}'
```

## Frontend Integration

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

## Error Handling

Custom exceptions in `src/domain/exceptions.py`:

- `TenantNotFound`: Invalid API key
- `AgentNotFound`: Invalid agent ID
- `RateLimitExceeded`: Rate limit hit
- `UsageLimitExceeded`: Monthly limit reached

All errors return consistent JSON format with error type, detail, and timestamp.

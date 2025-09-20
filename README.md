# AI Backend - Multi-Tenant SaaS Agent Platform

Centralized Python backend serving multiple Next.js SaaS projects with pre-configured AI agents and MCP integration.

## Features

- **Multi-tenant Architecture** - API key-based isolation per SaaS project
- **Pre-configured AI Agents** - Customer support, data analysis, content writing, code review
- **MCP Server** - Standalone SaaS discovery tools with ProductHunt integration
- **Production Ready** - Docker, rate limiting, monitoring, clean architecture

## Quick Start

```bash
# Setup (includes MCP server)
cp .env.example .env
docker-compose up --build
```

```python
# Register tenant
import httpx

async def register_tenant():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/register",
            headers={"Content-Type": "application/json"},
            json={
                "name": "Test Company",
                "tier": "free",
                "allowed_agents": ["customer-support"]
            }
        )
        return response.json()
```

## Architecture

```
src/
├── domain/         # Business entities and rules
├── application/    # CQRS commands and queries
├── infrastructure/ # External services (DB, AI, Cache)
├── api/           # FastAPI routes and middleware
├── agents/        # Agent configurations
└── config/        # Settings and environment
```

## API Endpoints

**Core:**
- `POST /api/v1/auth/register` - Register tenant
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents/{id}/execute` - Execute agent
- `POST /api/v1/agents/{id}/execute-stream` - Streaming execution

**MCP Server:**
- `GET http://localhost:8080/health` - Health check
- `POST http://localhost:8080/search_producthunt` - ProductHunt search
- `POST http://localhost:8080/execute` - Generic tool execution

## Available Agents

- **customer-support** - Ticket analysis, knowledge base search
- **data-analyst** - SQL queries, business insights
- **content-writer** - SEO content, keyword research
- **code-reviewer** - Static analysis, security audits

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

## Development

```bash
# Type checking (required)
./venv-python -m pyright src/

# Testing
./venv-python -m pytest tests/ -v

# Code quality
./venv-python -m black src/
./venv-python -m isort src/

# Database admin
http://localhost:5050 (admin@ai-backend.com / admin)
```

## Environment Variables

**Required:**
- `OPENAI_API_KEY` - OpenAI API access
- `JWT_SECRET` - JWT signing
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `API_KEY_HASH_SALT` - API key hashing

**Optional:**
- `MCP_SERVER_URL` - MCP server URL
- `PRODUCTHUNT_API_TOKEN` - ProductHunt API access

## Monitoring

```python
# Health check
import httpx

async def health_check():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        return response.json()
```

- API docs: http://localhost:8000/docs
- Logs: `docker-compose logs -f ai-backend`
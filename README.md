# SaaS AI Backend

A scalable, multi-tenant AI-powered backend for micro-SaaS applications built with FastAPI, OpenAI Agent SDK, and MCP (Model Context Protocol).

## 🏗️ Architecture

### Multi-Tenant Design
- **Database Strategy**: Schema-per-tenant with shared application infrastructure
- **Isolation**: Each tenant gets their own database schema and cached resources
- **Scalability**: Supports thousands of tenants on a single deployment

### Tech Stack
- **Framework**: FastAPI with dependency injection (dependency-injector)
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Cache**: Redis for session management and caching
- **AI Integration**: OpenAI Agent SDK + MCP for standardized tool access
- **Monitoring**: Prometheus metrics + structured logging
- **Deployment**: Docker containers with health checks

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <your-repo>
cd saas-ai-backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start with Docker Compose
```bash
# Start core services
docker-compose up -d

# Or with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### 3. Local Development
```bash
# Install dependencies
poetry install

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

## 📁 Project Structure

```
app/
├── core/                   # Core application configuration
│   ├── config.py          # Settings and environment variables
│   ├── container.py       # Dependency injection container
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py         # Logging configuration
├── domains/               # Domain models (DDD approach)
│   ├── tenant/           # Tenant management
│   ├── user/             # User management
│   └── project/          # Project and AI session models
├── infrastructure/       # External integrations
│   ├── database/         # Database connections and models
│   ├── cache/           # Redis client
│   └── external/        # OpenAI and MCP clients
├── services/            # Business logic services
├── api/                # API layer
│   ├── v1/endpoints/   # API endpoints
│   └── middleware/     # Custom middleware
└── main.py            # FastAPI application factory
```

## 🔧 Configuration

### Environment Variables
See `.env.example` for all configuration options.

Key configurations:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string  
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT signing key (generate secure key)
- `MCP_ENABLED`: Enable Model Context Protocol features

### Multi-Tenant Configuration
- **Tenant Identification**: Supports subdomain, header, or path-based tenant identification
- **Database Isolation**: Each tenant gets a separate schema
- **Resource Limits**: Configurable per-tenant rate limits and quotas

## 🤖 AI & MCP Integration

### OpenAI Agent SDK
- Full support for OpenAI Assistants API
- Streaming responses
- Tool calling and function execution
- Thread management for conversations

### Model Context Protocol (MCP)
Standardized interface for AI tools:
- File system operations
- Database queries  
- Web scraping
- Custom tool registration
- Resource management

Example MCP tool usage:
```python
# Register custom tool
await mcp_client.register_tool(
    name="analyze_data",
    description="Analyze dataset",
    input_schema={...},
    handler=analyze_data_handler
)

# Call tool from AI
result = await mcp_client.call_tool("analyze_data", {"dataset_id": "123"})
```

## 📊 Monitoring & Observability

### Metrics (Prometheus)
- HTTP request metrics (duration, count, status)
- Tenant-specific metrics
- Database connection pool metrics
- AI API usage metrics

### Logging
- Structured logging with `structlog`
- Request tracing with correlation IDs
- Tenant-aware logging context
- JSON format for production

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed health check (with dependencies)
curl http://localhost:8000/api/v1/health/detailed
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Tenant-scoped authorization
- Role-based access control (RBAC)
- API key management for service-to-service

### Multi-Tenant Security
- Database-level tenant isolation
- Resource access controls
- Rate limiting per tenant
- Audit logging

## 🚀 Deployment

### Recommended Hosting Options

#### Option 1: Railway (Simplest)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway up
```

#### Option 2: AWS ECS (Production)
- Use included `Dockerfile`
- Deploy with ECS Fargate
- RDS PostgreSQL + ElastiCache Redis
- Application Load Balancer

#### Option 3: Kubernetes
```bash
# Build and push image
docker build -t your-registry/saas-backend .
docker push your-registry/saas-backend

# Deploy with Helm or kubectl
```

### Database Scaling
- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: PgBouncer recommended
- **Sharding**: For massive scale (thousands of tenants)

## 📈 Scaling Considerations

### Horizontal Scaling
- Stateless application design
- Redis for shared state
- Load balancer with session affinity

### Database Scaling
- Schema-per-tenant supports up to ~1000 tenants per database
- Database-per-tenant for larger scale
- Automated tenant provisioning

### Monitoring at Scale
- Tenant-specific metrics and alerting
- Resource usage tracking
- Auto-scaling triggers

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app

# Load testing
locust -f tests/load_test.py
```

## 🔄 Development Workflow

### Adding New Domains
1. Create domain models in `app/domains/{domain}/`
2. Add service layer in `app/services/`  
3. Create API endpoints in `app/api/v1/endpoints/`
4. Register in dependency container
5. Add tests

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.
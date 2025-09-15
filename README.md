# AI Backend - Central Multi-Tenant Backend for SaaS Projects

A centralized Python backend that serves multiple Next.js SaaS projects with pre-configured AI agents using OpenAI SDK and MCP integration.

## 🚀 Features

- **Multi-tenant Architecture**: Isolated access per SaaS project with API key authentication
- **Pre-configured AI Agents**: Backend manages all agent logic and capabilities
- **OpenAI Integration**: Full OpenAI SDK support with streaming and async execution
- **MCP Support**: Model Context Protocol for tool integration
- **Rate Limiting**: Per-tenant rate limiting and usage tracking
- **Clean Architecture**: CQRS pattern with domain-driven design
- **Production Ready**: Docker, monitoring, and comprehensive error handling

## 🏗️ Architecture

```
├── Domain Layer      # Business entities and rules
├── Application Layer # CQRS commands and queries
├── Infrastructure    # External services (DB, AI, Cache)
├── API Layer         # FastAPI routes and middleware
└── Agents           # Pre-configured agent definitions
```

## 🔧 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <repository>
cd ai-backend
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
JWT_SECRET=your_jwt_secret_here
API_KEY_HASH_SALT=your_salt_here
```

### 3. Start Services

```cmd
docker-compose up --build
```

### 4. Create a Test Tenant

```cmd
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "tier": "free",
    "allowed_agents": ["customer-support", "data-analyst"]
  }'
```

## 📚 API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new tenant
- `GET /api/v1/auth/validate` - Validate API key
- `GET /api/v1/auth/usage` - Get usage statistics

### Agents

- `GET /api/v1/agents` - List available agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `POST /api/v1/agents/{agent_id}/execute` - Execute agent (sync)
- `POST /api/v1/agents/{agent_id}/execute-stream` - Execute agent (streaming)
- `POST /api/v1/agents/{agent_id}/execute-async` - Execute agent (async)

### Sessions

- `POST /api/v1/sessions` - Create conversation session
- `GET /api/v1/sessions/{session_id}` - Get session info
- `DELETE /api/v1/sessions/{session_id}` - Delete session

### Jobs

- `GET /api/v1/jobs/{job_id}` - Get async job status

## 🤖 Available Agents

### Customer Support Agent (`customer-support`)

- Analyzes customer inquiries and provides solutions
- Tools: Knowledge base search, escalation to human agents
- Best for: Support ticket automation, FAQ responses

### Data Analyst Agent (`data-analyst`)

- Performs data analysis and generates insights
- Tools: SQL queries, visualization creation
- Best for: Business intelligence, reporting dashboards

### Content Writer Agent (`content-writer`)

- Creates SEO-optimized content for marketing
- Tools: Keyword research, competitor analysis
- Best for: Blog posts, landing pages, product descriptions

### Code Reviewer Agent (`code-reviewer`)

- Reviews code for quality, security, and best practices
- Tools: Static analysis, improvement suggestions
- Best for: Code quality automation, security audits

## 💻 Usage Examples

### From Next.js Frontend

```javascript
// Customer Support SaaS
const response = await fetch("https://ai-backend.com/api/v1/agents/customer-support/execute", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "your-tenant-api-key",
  },
  body: JSON.stringify({
    parameters: {
      customer_message: "I can't log into my account",
      customer_tier: "pro",
    },
  }),
});
```

```javascript
// Content Generation SaaS
const response = await fetch("https://ai-backend.com/api/v1/agents/content-writer/execute", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "your-tenant-api-key",
  },
  body: JSON.stringify({
    parameters: {
      content_type: "blog_post",
      topic: "AI in Healthcare",
      target_keywords: ["medical AI", "healthcare automation"],
      word_count: 1500,
    },
  }),
});
```

### Streaming Response

```javascript
const response = await fetch("/api/v1/agents/content-writer/execute-stream", {
  method: "POST",
  headers: {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ parameters: { topic: "AI Trends" } }),
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = new TextDecoder().decode(value);
  // Process streaming data
  console.log(chunk);
}
```

## 🔧 Development

### Local Development

```cmd
# Start development server
docker-compose up --build

# Run tests
./venv-python -m pytest tests/ -v

# Format code
./venv-python -m black src/
./venv-python -m isort src/

# Type checking
./venv-python -m pyright src/
```

### Database Management

```cmd
# Reset database
docker-compose down -v
docker-compose up --build

# Access database admin
http://localhost:5050 (admin@ai-backend.com / admin)
```

## 🚀 Deployment

### Production Build

```cmd
# Build production image
docker build -f docker/Dockerfile -t ai-backend:prod .

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

| Variable            | Description                          | Required |
| ------------------- | ------------------------------------ | -------- |
| `DATABASE_URL`      | PostgreSQL connection string         | Yes      |
| `REDIS_URL`         | Redis connection string              | Yes      |
| `OPENAI_API_KEY`    | OpenAI API key                       | Yes      |
| `JWT_SECRET`        | JWT signing secret                   | Yes      |
| `API_KEY_HASH_SALT` | Salt for API key hashing             | Yes      |
| `ENVIRONMENT`       | Environment (development/production) | No       |
| `DEBUG`             | Enable debug mode                    | No       |
| `ALLOWED_ORIGINS`   | CORS allowed origins                 | No       |

## 📊 Monitoring

### Health Check

```cmd
curl http://localhost:8000/health
```

### Metrics

- Request rate per tenant
- Token usage tracking
- Agent execution metrics
- Error rates and latency

## 🔒 Security

- API key authentication with secure hashing
- Rate limiting per tenant tier
- Input validation and sanitization
- Structured logging for audit trails
- No secrets in logs or responses

## 🤝 Adding New Agents

1. Define agent configuration in `src/agents/config.py`
2. Add required tools to `src/infrastructure/ai/tool_executor.py`
3. Update agent permissions for tenants
4. Test agent execution
5. Update documentation

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Check logs: `docker-compose logs -f ai-backend`
- Database admin: http://localhost:5050
- API docs: http://localhost:8000/docs

---

Built with ❤️ for scalable SaaS development

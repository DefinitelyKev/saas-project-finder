# API Layer

This directory contains the FastAPI application's HTTP interface, including routes, middleware, request/response schemas, and dependency injection. The API layer handles all HTTP concerns and translates between web requests and domain operations.

## Structure

```
api/
├── v1/                 # API version 1
│   ├── routes/        # HTTP route handlers
│   ├── schemas.py     # Pydantic request/response models
│   └── dependencies.py # FastAPI dependency injection
└── middleware/        # Custom middleware stack
```

## Middleware Stack (`middleware/`)

The middleware stack processes requests in a specific order. **Order matters** - middleware is applied in reverse order of registration.

### `auth.py` - Authentication Middleware
**Purpose**: Validates API key presence in request headers.

**Process**:
1. Extracts API key from `X-API-Key` or `Authorization` header
2. Handles `Bearer` token format by removing prefix
3. Stores API key in `request.state.api_key` for downstream middleware
4. Skips public paths (`/health`, `/docs`, `/redoc`, `/openapi.json`)

**Error Responses**:
- 401 Unauthorized if API key is missing
- Passes through for tenant middleware to validate key

### `tenant.py` - Tenant Resolution Middleware
**Purpose**: Resolves tenant from API key and stores in request state.

**Process**:
1. Uses stored API key from auth middleware
2. Calls `TenantService.get_tenant_by_api_key()`
3. Validates tenant is active and valid
4. Stores tenant in `request.state.tenant`
5. Logs tenant resolution with correlation IDs

**Database Integration**:
- Creates database session for tenant lookup
- Uses repository pattern through TenantService
- Handles database connection errors gracefully

**Error Responses**:
- 401 Unauthorized for invalid API keys
- 401 Unauthorized for inactive tenants
- 500 Internal Server Error for database issues

### `rate_limit.py` - Rate Limiting Middleware
**Purpose**: Enforces per-tenant rate limits based on tier.

**Algorithm**: Sliding window rate limiting using in-memory storage
- Tracks requests per tenant in time windows
- Different limits per tier (Free: 10/min, Pro: 50/min, Enterprise: 200/min)
- Automatic cleanup of old request records

**Features**:
- Returns rate limit headers in responses
- Handles concurrent requests safely with asyncio.Lock
- Exempts monitoring and documentation endpoints

**Response Headers**:
- `X-RateLimit-Limit`: Requests allowed per minute
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Timestamp when window resets
- `Retry-After`: Seconds to wait when rate limited

## API Version 1 (`v1/`)

### `schemas.py` - Request/Response Models
**Purpose**: Pydantic models for API contract definition and validation.

**Request Schemas**:
- `CreateTenantRequest`: Tenant registration data
- `ExecuteAgentRequest`: Agent execution parameters with optional session
- `CreateSessionRequest`: Session creation with agent ID and metadata

**Response Schemas**:
- `TenantResponse`: Tenant information without sensitive data
- `AgentResponse`: Complete agent configuration and statistics
- `ExecutionResponse`: Agent execution results and metadata
- `SessionResponse`: Session summary with activity tracking
- `UsageResponse`: Tenant usage statistics and limits

**Features**:
- Automatic validation with descriptive error messages
- Field descriptions for API documentation
- Default values and optional fields
- Enum validation for controlled vocabularies

### `dependencies.py` - Dependency Injection
**Purpose**: FastAPI dependency providers for service injection.

**Dependencies**:
- `get_current_tenant()`: Extracts tenant from request state
- `get_tenant_service()`: Creates TenantService with database session
- `get_openai_client()`: OpenAI client wrapper instance
- `get_tool_executor()`: Tool execution service
- `get_agent_executor()`: Complete agent execution orchestrator

**Pattern**: Constructor injection for loose coupling and testability

### Routes (`routes/`)

#### `auth.py` - Authentication & Tenant Management
**Endpoints**:
- `POST /auth/register`: Create new tenant and return API key
- `GET /auth/validate`: Validate API key and return tenant info
- `GET /auth/usage`: Get current tenant usage statistics
- `POST /auth/regenerate-key`: Generate new API key for tenant

**Features**:
- Secure API key generation and hashing
- Usage statistics with tier-based limits
- API key rotation for security

#### `agents.py` - Agent Discovery & Execution
**Endpoints**:
- `GET /agents`: List agents accessible to tenant
- `GET /agents/{agent_id}`: Get detailed agent information
- `POST /agents/{agent_id}/execute`: Synchronous agent execution
- `POST /agents/{agent_id}/execute-stream`: Streaming agent execution
- `POST /agents/{agent_id}/execute-async`: Background agent execution

**Execution Patterns**:
- **Sync**: Immediate response with complete results
- **Streaming**: Server-sent events with real-time chunks
- **Async**: Background job with job ID for polling

**Access Control**:
- Validates tenant can access requested agent
- Checks agent exists in configuration
- Enforces parameter schema validation

#### `sessions.py` - Conversation Management
**Endpoints**:
- `POST /sessions`: Create new conversation session
- `GET /sessions/{session_id}`: Get session information and history
- `DELETE /sessions/{session_id}`: Delete session and clear context

**Features**:
- Stateful conversation management
- Automatic session expiration (24 hours)
- Context window management with message trimming

#### `jobs.py` - Background Job Status
**Endpoints**:
- `GET /jobs/{job_id}`: Get status of async agent execution

**Job States**: pending, processing, completed, failed

#### `usage.py` - Usage Monitoring
**Endpoints**:
- `GET /usage`: Get detailed tenant usage statistics

**Metrics**:
- Token usage by time period
- Request counts by agent
- Success rates and error statistics
- Cost tracking and billing information

## Error Handling Strategy

### Global Exception Handlers
Registered in `src/main.py` for consistent error responses:

```python
@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "detail": str(exc)}
    )
```

### HTTP Status Code Mapping
- **400 Bad Request**: Domain validation errors, invalid parameters
- **401 Unauthorized**: Invalid API key, inactive tenant
- **403 Forbidden**: Agent access denied
- **404 Not Found**: Agent not found, session not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected system errors

### Error Response Format
```json
{
  "error": "ErrorTypeName",
  "detail": "Human-readable error description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Streaming Implementation

### Server-Sent Events (SSE)
Used for real-time agent responses:

```python
async def generate_stream():
    async for chunk in agent_executor.execute_streaming(...):
        yield f"data: {json.dumps(chunk)}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**Chunk Types**:
- `content`: Text content from agent
- `tool_call`: Tool invocation data
- `error`: Error messages
- `done`: Stream completion signal

## CORS Configuration

Configured for Next.js frontend integration:
- Allowed origins from environment configuration
- Credentials support for authenticated requests
- All HTTP methods allowed for API flexibility
- Wildcard headers for development ease

## API Documentation

### OpenAPI Integration
- Automatic schema generation from Pydantic models
- Interactive documentation at `/docs` (Swagger UI)
- Alternative documentation at `/redoc` (ReDoc)
- OpenAPI spec at `/openapi.json`

### Documentation Features
- Request/response examples
- Parameter descriptions
- Error response documentation
- Authentication requirements
- Rate limiting information

## Testing Patterns

### Route Testing
```python
def test_execute_agent(client, auth_headers):
    response = client.post(
        "/api/v1/agents/customer-support/execute",
        headers=auth_headers,
        json={"parameters": {"customer_message": "test"}}
    )
    assert response.status_code == 200
```

### Middleware Testing
```python
async def test_rate_limit_middleware():
    # Test rate limiting logic
    # Test different tenant tiers
    # Test concurrent request handling
```

## Performance Optimizations

### Async Operations
- All route handlers use `async def`
- Database operations are non-blocking
- OpenAI API calls use async client
- Streaming responses for large payloads

### Caching Strategy
- Tenant data cached after first lookup
- Agent configurations cached in memory
- Response caching for expensive operations
- ETags for conditional requests

### Connection Management
- Database connection pooling
- HTTP client connection reuse
- Graceful shutdown handling

## Security Measures

### Input Validation
- Pydantic schema validation on all inputs
- Parameter sanitization for agent execution
- File upload restrictions (if implemented)
- SQL injection prevention through ORM

### Authentication Security
- API key hashing with salt
- Secure random key generation
- No plain text key storage
- Key rotation capabilities

### Rate Limiting
- Per-tenant request limits
- Different tiers with different limits
- Sliding window algorithm
- Protection against DoS attacks

## Integration with Frontend

### Next.js Integration Pattern
```javascript
const response = await fetch('/api/v1/agents/customer-support/execute', {
  method: 'POST',
  headers: {
    'X-API-Key': process.env.BACKEND_API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    parameters: { customer_message: "Help me" }
  })
});
```

### Streaming Integration
```javascript
const response = await fetch('/api/v1/agents/content-writer/execute-stream', {
  method: 'POST',
  headers: { 'X-API-Key': apiKey },
  body: JSON.stringify({ parameters: { topic: "AI" } })
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = new TextDecoder().decode(value);
  // Process streaming data
}
```

The API layer provides a clean, RESTful interface for all SaaS frontends while handling authentication, rate limiting, and proper error responses.
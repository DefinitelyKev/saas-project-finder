# Domain Layer

This directory contains the core business logic and domain entities following Domain-Driven Design principles. The domain layer is independent of external concerns and contains the essential business rules.

## Structure

```
domain/
├── entities/           # Domain entities with business logic
├── value_objects/      # Immutable value objects
├── events/            # Domain events (future expansion)
└── exceptions.py      # Domain-specific exceptions
```

## Key Files

### `exceptions.py`
Domain-specific exceptions that represent business rule violations:
- `DomainException`: Base exception for all domain errors
- `TenantNotFound`: Invalid or missing tenant
- `AgentNotFound`: Requested agent doesn't exist
- `RateLimitExceeded`: Tenant exceeded rate limits
- `UsageLimitExceeded`: Monthly token quota exceeded
- `InvalidApiKey`: API key validation failed
- `AgentExecutionError`: Agent execution failed
- `SessionNotFound`: Session not found or expired
- `InvalidAgentParameters`: Agent parameters don't match schema

## Entities

### `tenant.py` - Tenant Entity
**Purpose**: Represents a SaaS project with usage tracking and access control.

**Key Methods**:
- `can_access_agent(agent_id)`: Check if tenant can use specific agent
- `has_tokens_remaining()`: Verify monthly token quota
- `add_token_usage(tokens)`: Track token consumption
- Properties for tier-based limits (token limits, rate limits, max sessions)

**Business Rules**:
- Token usage resets monthly automatically
- Different tiers (Free/Pro/Enterprise) have different limits
- Access control via allowed_agents list (empty = access all)

### `agent.py` - Agent Entity
**Purpose**: Represents a pre-configured AI agent with tools and validation.

**Key Methods**:
- `validate_parameters(params)`: Validate input against schema
- `get_tool_by_name(name)`: Find specific tool
- `get_mcp_tools()` / `get_function_tools()`: Filter tools by type
- `update_usage_stats(tokens, success)`: Track performance metrics

**Components**:
- `AgentTool`: Represents individual tools (MCP or function-based)
- Tool validation and parameter schema enforcement
- Usage statistics and success rate tracking

### `execution.py` - Execution Entity
**Purpose**: Tracks the lifecycle of an agent execution from start to completion.

**State Management**:
- `start()`: Mark execution as processing
- `complete(result, tokens)`: Mark successful completion
- `fail(error)`: Mark as failed with error message
- Properties: `is_completed`, `is_successful`

**Data Tracked**:
- Input parameters and results
- Token usage and execution time
- Error messages and status transitions
- Timestamps for all state changes

### `session.py` - Session Entity
**Purpose**: Manages stateful conversations with automatic memory management.

**Key Features**:
- `add_message(role, content, tokens)`: Add to conversation
- `get_context_messages()`: Format for OpenAI API
- Automatic message trimming when limits exceeded
- Session expiration (24 hours default)
- Token and message count limits

**Memory Management**:
- Keeps system messages always
- Trims oldest non-system messages when over limits
- Sliding window approach for token management

## Value Objects

### `api_key.py` - ApiKey Value Object
**Purpose**: Secure API key handling with hashing.

**Features**:
- `generate()`: Create cryptographically secure API key
- `hash()`: Create salted hash for storage
- `hash_key(key)`: Static method for hash verification
- Immutable design prevents key modification
- Safe string representation (masks key in logs)

## Design Principles

1. **Business Logic Centralization**: All business rules are in domain entities
2. **Framework Independence**: No dependencies on FastAPI, SQLAlchemy, etc.
3. **Rich Domain Model**: Entities contain behavior, not just data
4. **Immutable Value Objects**: ApiKey and other values cannot be modified
5. **Explicit Business Rules**: Clear methods for validation and state changes

## Usage Patterns

### Creating Entities
```python
# Tenant with usage tracking
tenant = Tenant(
    name="My SaaS Project",
    tier=TenantTier.PRO,
    allowed_agents=["customer-support", "data-analyst"]
)

# Check business rules
if tenant.has_tokens_remaining() and tenant.can_access_agent("customer-support"):
    # Execute agent logic
```

### Execution Lifecycle
```python
execution = Execution(tenant_id=tenant.id, agent_id="customer-support")
execution.start()
try:
    # Agent execution logic
    execution.complete(result_data, token_count)
except Exception as e:
    execution.fail(str(e))
```

### Session Management
```python
session = Session(tenant_id=tenant.id, agent_id="customer-support")
session.add_message("user", "Hello")
session.add_message("assistant", "Hi there!", token_count=10)

# Get formatted messages for API
messages = session.get_context_messages()
```

## Integration Points

- **Application Layer**: Commands and queries use these entities
- **Infrastructure Layer**: Repositories persist and retrieve entities
- **API Layer**: Converts between entities and HTTP responses

The domain layer should never import from other layers - all dependencies flow inward to maintain clean architecture.
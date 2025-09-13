# Infrastructure Layer

This directory contains all external service integrations and technical implementations. The infrastructure layer provides concrete implementations for domain services and handles all I/O operations.

## Structure

```
infrastructure/
├── ai/                 # AI service integrations (OpenAI, tools)
├── persistence/        # Database access and repositories
├── cache/             # Redis caching implementation
└── queue/             # Background job processing
```

## AI Integration (`ai/`)

### `openai_client.py` - OpenAI API Wrapper
**Purpose**: Wraps OpenAI SDK with custom functionality for agents.

**Key Methods**:
- `create_completion(agent, user_input, session, stream)`: Main completion method
- `create_streaming_completion()`: Server-sent events for real-time responses
- `count_tokens(text)`: Estimate token usage for billing
- `validate_model(model)`: Check if model is available

**Features**:
- Automatic message building from agent config and session context
- Tool preparation in OpenAI function calling format
- Error handling with domain exceptions
- Streaming support with async generators

### `agent_executor.py` - Main Execution Orchestrator
**Purpose**: Coordinates agent execution with OpenAI and tool calling.

**Execution Flow**:
1. Parameter validation against agent schema
2. Usage limit checking (tokens, rate limits)
3. OpenAI API call with agent configuration
4. Tool execution if tools are called
5. Session context management
6. Usage tracking and statistics

**Methods**:
- `execute_sync()`: Complete execution with result
- `execute_streaming()`: Real-time streaming execution
- `_handle_tool_calls()`: Process agent tool invocations
- `_extract_user_input()`: Smart parameter extraction

### `tool_executor.py` - Tool Function Handler
**Purpose**: Executes agent tools (both built-in functions and MCP).

**Built-in Tools**:
- `search_knowledge_base()`: Mock knowledge base search
- `escalate_to_human()`: Support ticket escalation
- `execute_sql_query()`: Database query simulation
- `create_visualization()`: Chart generation mock
- `keyword_research()`: SEO keyword analysis
- `analyze_competitors()`: Competitor content analysis
- `static_analysis()`: Code quality checking
- `suggest_improvements()`: Code improvement recommendations

**Tool Types**:
- **Function Tools**: Built-in Python functions registered in the executor
- **MCP Tools**: Model Context Protocol integrations (future expansion)

## Persistence (`persistence/`)

### `database.py` - Database Connection Management
**Purpose**: Async SQLAlchemy setup with connection pooling.

**Components**:
- `Base`: Declarative base class for all models
- `engine`: Async database engine with pooling
- `AsyncSessionLocal`: Session factory for database operations
- `get_db_session()`: Context manager for transactions
- `get_db()`: FastAPI dependency for route injection

### `models.py` - SQLAlchemy Models
**Purpose**: Database table definitions using SQLAlchemy 2.0.

**Models**:
- `TenantModel`: Tenant data with API keys and usage tracking
- `AgentModel`: Agent configurations (though primarily in code)
- `ExecutionModel`: All agent execution records for billing/monitoring
- `SessionModel`: Conversation session persistence
- `UsageLogModel`: Detailed usage logs for analytics

**Design Patterns**:
- UUID primary keys for all entities
- JSON columns for flexible data (tools, parameters, metadata)
- Proper indexes on frequently queried columns
- Timestamp tracking for all operations

### `repositories/` - Data Access Layer

#### `tenant_repository.py` - Tenant Data Access
**Purpose**: Repository pattern for tenant entity persistence.

**Key Methods**:
- `create(tenant)`: Insert new tenant with error handling
- `get_by_id(tenant_id)`: Retrieve tenant by UUID
- `get_by_api_key_hash(hash)`: Find tenant by API key hash
- `update(tenant)`: Update tenant information and usage
- `list_tenants()`: Paginated tenant listing
- `_model_to_entity()`: Convert SQLAlchemy model to domain entity

**Features**:
- Automatic model-to-entity conversion
- Proper error handling with domain exceptions
- Async/await throughout for performance
- Transaction management within repository

## Cache (`cache/`)

### Redis Integration
**Purpose**: Caching layer for responses and rate limiting.

**Use Cases**:
- Agent response caching for repeated queries
- Rate limiting sliding windows per tenant
- Session context caching for performance
- Usage statistics aggregation

**Implementation Strategy**:
- TTL-based cache expiration
- Tenant-specific cache keys
- Sliding window rate limiting algorithm
- Cache invalidation on data changes

## Queue (`queue/`)

### Background Job Processing
**Purpose**: Async job execution for long-running agent tasks.

**Job Types**:
- Long-running agent executions
- Bulk data processing
- Report generation
- Email notifications

**Implementation Options**:
- Redis-based job queue
- Celery integration
- FastAPI BackgroundTasks for simple jobs

## Configuration and Dependencies

### Service Initialization
All infrastructure services are initialized through dependency injection:

```python
# Example service dependencies
def get_openai_client() -> OpenAIClientWrapper:
    return OpenAIClientWrapper()

def get_agent_executor(
    openai_client: OpenAIClientWrapper = Depends(get_openai_client),
    tool_executor: ToolExecutor = Depends(get_tool_executor),
) -> AgentExecutor:
    return AgentExecutor(openai_client, tool_executor)
```

### Environment Configuration
Infrastructure services read configuration from `src/config/settings.py`:
- Database connection strings
- Redis configuration
- OpenAI API keys and organization
- Rate limiting parameters
- Caching TTL values

## Error Handling Patterns

### Database Errors
```python
try:
    await self.session.flush()
except IntegrityError as e:
    await self.session.rollback()
    raise ValueError(f"Creation failed: {str(e)}")
```

### AI Service Errors
```python
try:
    response = await self.client.chat.completions.create(...)
except Exception as e:
    logger.error("OpenAI API error", error=str(e))
    raise AgentExecutionError(f"Failed to execute agent: {str(e)}")
```

## Performance Considerations

### Database
- Connection pooling for concurrent requests
- Async operations to prevent blocking
- Proper indexing on frequently queried columns
- Repository pattern for consistent data access

### AI Services
- Token counting for accurate billing
- Streaming responses for user experience
- Error retry with exponential backoff
- Response caching for repeated queries

### Caching Strategy
- Cache frequently accessed tenant data
- Cache agent configurations
- Sliding window rate limiting
- TTL-based cache expiration

## Integration Points

- **Domain Layer**: Implements domain service interfaces
- **Application Layer**: Provides concrete implementations for commands/queries
- **API Layer**: Injected as dependencies into route handlers

The infrastructure layer is the only layer allowed to have external dependencies (databases, APIs, etc.).
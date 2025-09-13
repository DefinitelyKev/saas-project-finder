# Application Layer

This directory implements the Command Query Responsibility Segregation (CQRS) pattern, separating read operations (queries) from write operations (commands). The application layer coordinates domain entities and infrastructure services to fulfill business use cases.

## Structure

```
application/
├── commands/           # Write operations that change system state
├── queries/           # Read operations that retrieve data
└── handlers/          # Command and query handlers
```

## CQRS Pattern Implementation

### Commands vs Queries

**Commands (Write Operations)**:
- Modify system state
- Execute business logic
- Have side effects
- Return execution status, not data
- Examples: Create tenant, execute agent, update usage

**Queries (Read Operations)**:
- Retrieve data without modifications
- No side effects
- Return data or projections
- Optimized for specific read scenarios
- Examples: Get agent list, fetch usage statistics

## Commands (`commands/`)

### Command Structure
Each command represents a single business operation that changes state:

```python
@dataclass
class CreateAgentCommand:
    tenant_id: str
    agent_id: str
    parameters: Dict[str, Any]
    session_id: Optional[str] = None
    stream: bool = False
```

### Planned Commands

#### `execute_agent.py` - Agent Execution Command
**Purpose**: Execute an AI agent with given parameters.

**Command Data**:
- Tenant ID for access control
- Agent ID and execution parameters
- Optional session for context
- Execution mode (sync/async/stream)

**Business Logic**:
1. Validate tenant can access agent
2. Check usage limits and rate limiting
3. Validate parameters against agent schema
4. Execute agent through infrastructure
5. Update usage statistics
6. Create execution record

#### `create_session.py` - Session Creation Command
**Purpose**: Create a new conversation session.

**Command Data**:
- Tenant ID and agent ID
- Session metadata and configuration
- Initial context or system message

**Business Logic**:
1. Validate agent exists and tenant has access
2. Check session limits for tenant tier
3. Create session entity with proper configuration
4. Initialize conversation context
5. Persist session state

#### `register_tenant.py` - Tenant Registration Command
**Purpose**: Register a new tenant with API key generation.

**Command Data**:
- Tenant name and tier
- Allowed agents list
- Contact and billing information

**Business Logic**:
1. Generate secure API key
2. Create tenant entity with hashed key
3. Set up tier-based limits and permissions
4. Initialize usage tracking
5. Send welcome communications

## Queries (`queries/`)

### Query Structure
Each query represents a data retrieval operation:

```python
@dataclass
class GetAgentQuery:
    agent_id: str
    tenant_id: str
    include_statistics: bool = False
```

### Planned Queries

#### `get_agents.py` - Agent Discovery Query
**Purpose**: Retrieve agents available to a tenant.

**Query Data**:
- Tenant ID for access filtering
- Optional category or capability filters
- Pagination parameters

**Data Projection**:
- Agent basic information
- Tool capabilities summary
- Usage statistics (if requested)
- Access permissions

#### `list_agents.py` - Agent Listing Query
**Purpose**: List all agents with filtering and pagination.

**Query Data**:
- Tenant ID for access control
- Search criteria and filters
- Sorting and pagination options

**Optimization**:
- Cached agent configurations
- Minimal data transfer
- Efficient access control checks

#### `get_execution.py` - Execution Status Query
**Purpose**: Retrieve execution details and status.

**Query Data**:
- Execution ID and tenant ID
- Include full results or summary only

**Data Projection**:
- Execution status and timing
- Input parameters and results
- Error information if failed
- Usage and cost information

#### `get_usage.py` - Usage Statistics Query
**Purpose**: Retrieve tenant usage statistics and limits.

**Query Data**:
- Tenant ID and time period
- Grouping options (by agent, day, etc.)
- Include cost breakdown

**Data Aggregation**:
- Token usage by time period
- Request counts by agent
- Success/failure rates
- Cost analysis and projections

## Handlers (`handlers/`)

### Command Handler Pattern

#### `command_handler.py` - Command Processing
**Purpose**: Coordinate command execution with infrastructure services.

**Handler Structure**:
```python
class CommandHandler:
    def __init__(
        self,
        tenant_service: TenantService,
        agent_executor: AgentExecutor,
        session_service: SessionService,
    ):
        self.tenant_service = tenant_service
        self.agent_executor = agent_executor
        self.session_service = session_service

    async def handle_execute_agent(self, command: ExecuteAgentCommand) -> ExecutionResult:
        # 1. Load and validate tenant
        tenant = await self.tenant_service.get_by_id(command.tenant_id)

        # 2. Load agent configuration
        agent = create_agent_from_config(command.agent_id)

        # 3. Validate business rules
        self._validate_agent_access(tenant, agent)
        self._validate_usage_limits(tenant)

        # 4. Execute through infrastructure
        execution = await self.agent_executor.execute_sync(
            agent, command.parameters, tenant, command.session
        )

        # 5. Update tenant usage
        await self.tenant_service.update_usage(
            tenant.id, execution.token_usage
        )

        return execution
```

**Error Handling**:
- Domain exception translation
- Transaction management
- Compensation logic for failures

### Query Handler Pattern

#### `query_handler.py` - Query Processing
**Purpose**: Optimize data retrieval with caching and projections.

**Handler Structure**:
```python
class QueryHandler:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        cache_service: CacheService,
        agent_registry: AgentRegistry,
    ):
        self.tenant_repository = tenant_repository
        self.cache_service = cache_service
        self.agent_registry = agent_registry

    async def handle_get_agents(self, query: GetAgentsQuery) -> AgentListProjection:
        # 1. Check cache first
        cache_key = f"agents:{query.tenant_id}:{hash(query)}"
        cached = await self.cache_service.get(cache_key)
        if cached:
            return cached

        # 2. Load tenant for access control
        tenant = await self.tenant_repository.get_by_id(query.tenant_id)

        # 3. Filter agents by access permissions
        all_agents = self.agent_registry.get_all()
        accessible_agents = [
            agent for agent in all_agents
            if tenant.can_access_agent(agent.id)
        ]

        # 4. Create projection with minimal data
        projection = AgentListProjection.from_agents(accessible_agents)

        # 5. Cache result
        await self.cache_service.set(cache_key, projection, ttl=300)

        return projection
```

**Optimization Strategies**:
- Result caching with TTL
- Minimal data projections
- Efficient database queries
- Background data refresh

## Data Flow Patterns

### Command Flow
```
API Request → Command → Command Handler → Domain Services → Infrastructure → Database
                                      ↓
                                   Domain Events → Event Handlers
```

### Query Flow
```
API Request → Query → Query Handler → Cache Check → Data Projection → Response
                                          ↓
                                   Database → Cache Update
```

## Transaction Management

### Command Transactions
Commands that modify multiple entities use database transactions:

```python
async def handle_execute_agent(self, command: ExecuteAgentCommand):
    async with self.db_session.begin():
        try:
            # 1. Create execution record
            execution = await self.execution_repository.create(...)

            # 2. Update tenant usage
            await self.tenant_repository.update_usage(...)

            # 3. Execute agent (external call)
            result = await self.agent_executor.execute(...)

            # 4. Update execution with results
            await self.execution_repository.update(execution.id, result)

            # Transaction commits automatically
        except Exception:
            # Transaction rolls back automatically
            raise
```

### Query Isolation
Queries use read-only transactions for consistency:

```python
async def handle_get_usage(self, query: GetUsageQuery):
    async with self.db_session.begin_readonly():
        # Multiple read operations with consistent view
        tenant = await self.tenant_repository.get_by_id(query.tenant_id)
        executions = await self.execution_repository.get_by_tenant(...)
        return UsageProjection.from_data(tenant, executions)
```

## Event-Driven Architecture (Future)

### Domain Events
Commands will emit domain events for loose coupling:

```python
class AgentExecutedEvent:
    execution_id: str
    tenant_id: str
    agent_id: str
    token_usage: int
    success: bool
    timestamp: datetime

# Event handlers for cross-cutting concerns
class UsageTrackingHandler:
    async def handle(self, event: AgentExecutedEvent):
        await self.analytics_service.record_usage(event)

class BillingHandler:
    async def handle(self, event: AgentExecutedEvent):
        await self.billing_service.charge_tokens(event)
```

## Caching Strategy

### Command Caching
Commands typically don't use caching but may cache:
- Agent configurations (rarely change)
- Tenant permissions (with invalidation)
- Rate limiting windows

### Query Caching
Queries use multi-level caching:
- **L1 (In-Memory)**: Agent configurations, tenant basic data
- **L2 (Redis)**: Query results, computed projections
- **L3 (Database)**: Materialized views, aggregated data

**Cache Keys Pattern**:
```
agents:{tenant_id}:{filters_hash}
usage:{tenant_id}:{period}:{metrics}
execution:{execution_id}
```

## Error Handling

### Command Error Handling
```python
try:
    result = await self.handle_command(command)
    return CommandResult.success(result)
except DomainException as e:
    logger.warning("Domain rule violation", error=str(e))
    return CommandResult.domain_error(e)
except InfrastructureException as e:
    logger.error("Infrastructure failure", error=str(e))
    return CommandResult.infrastructure_error(e)
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    return CommandResult.system_error(e)
```

### Query Error Handling
```python
try:
    result = await self.handle_query(query)
    return QueryResult.success(result)
except CacheException:
    # Fallback to database
    result = await self.handle_query_from_db(query)
    return QueryResult.success(result)
except Exception as e:
    logger.error("Query failed", error=str(e))
    return QueryResult.error(e)
```

## Testing Strategies

### Command Testing
```python
async def test_execute_agent_command():
    # Arrange
    command = ExecuteAgentCommand(
        tenant_id="123",
        agent_id="customer-support",
        parameters={"message": "test"}
    )

    # Mock dependencies
    mock_tenant_service = Mock()
    mock_agent_executor = Mock()

    handler = CommandHandler(mock_tenant_service, mock_agent_executor)

    # Act
    result = await handler.handle_execute_agent(command)

    # Assert
    assert result.is_success
    mock_agent_executor.execute_sync.assert_called_once()
```

### Query Testing
```python
async def test_get_agents_query():
    # Arrange
    query = GetAgentsQuery(tenant_id="123")
    mock_cache = Mock()
    mock_cache.get.return_value = None  # Cache miss

    handler = QueryHandler(cache_service=mock_cache)

    # Act
    result = await handler.handle_get_agents(query)

    # Assert
    assert len(result.agents) > 0
    mock_cache.set.assert_called_once()  # Verify caching
```

## Integration Points

### With Domain Layer
- Uses domain entities and services
- Enforces domain business rules
- Translates domain exceptions

### With Infrastructure Layer
- Delegates to infrastructure services
- Manages transactions and persistence
- Handles external service calls

### With API Layer
- Provides handlers for route endpoints
- Translates between HTTP and application concerns
- Returns structured results for API responses

The application layer orchestrates the business use cases while maintaining clean separation between domain logic and infrastructure concerns.
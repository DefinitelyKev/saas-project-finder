# Services Layer

This directory contains domain services that encapsulate business logic spanning multiple entities or requiring external integrations. Services bridge the gap between domain entities and infrastructure concerns while maintaining business rule encapsulation.

## Structure

```
services/
├── tenant_service.py      # Tenant management and usage tracking
├── agent_service.py       # Agent lifecycle and configuration (future)
├── session_service.py     # Session management and context (future)
├── billing_service.py     # Usage billing and cost tracking (future)
└── mcp_service.py        # MCP server coordination (future)
```

## Current Services

### `tenant_service.py` - Tenant Management Service
**Purpose**: Manages tenant lifecycle, API key operations, and usage tracking.

**Key Responsibilities**:
- Tenant registration with secure API key generation
- API key validation and rotation
- Usage tracking and quota enforcement
- Tier management and permission updates
- Agent access control management

**Core Methods**:

#### Tenant Registration
```python
async def create_tenant(
    name: str,
    tier: TenantTier = TenantTier.FREE,
    allowed_agents: Optional[List[str]] = None,
) -> tuple[Tenant, str]:
```
- Generates cryptographically secure API key
- Creates tenant entity with hashed key
- Sets up tier-based limits and permissions
- Returns tenant entity and plain-text API key

#### Authentication
```python
async def get_tenant_by_api_key(api_key: str) -> Tenant:
```
- Hashes provided API key for lookup
- Validates tenant exists and is active
- Returns tenant entity for request processing
- Raises domain exceptions for invalid keys

#### Usage Management
```python
async def update_tenant_usage(tenant_id: str, tokens_used: int) -> None:
```
- Updates monthly token consumption
- Handles month rollover automatically
- Maintains usage statistics for billing
- Enforces usage limits per tier

#### Access Control
```python
async def add_agent_access(tenant_id: str, agent_id: str) -> Tenant:
async def remove_agent_access(tenant_id: str, agent_id: str) -> Tenant:
```
- Manages per-tenant agent permissions
- Updates allowed agents list
- Logs access changes for audit trail

#### Security Operations
```python
async def generate_new_api_key(tenant_id: str) -> str:
async def deactivate_tenant(tenant_id: str) -> Tenant:
```
- API key rotation for security
- Tenant account suspension
- Maintains security audit trail

**Business Rules Enforced**:
- API keys are always hashed before storage
- Usage tracking automatically handles month boundaries
- Tier changes affect limits immediately
- Agent access is additive (can only grant/revoke specific agents)
- Deactivated tenants cannot authenticate

**Integration Points**:
- Uses `TenantRepository` for data persistence
- Integrates with `ApiKey` value object for secure key handling
- Enforces tier limits defined in `config/constants.py`
- Logs all operations with structured logging

## Planned Services

### `agent_service.py` - Agent Lifecycle Management (Future)
**Purpose**: Manage agent configurations, versioning, and deployment.

**Planned Responsibilities**:
- Agent configuration validation
- Agent deployment and rollback
- Performance monitoring and analytics
- A/B testing for agent variations
- Agent health checks and diagnostics

**Planned Methods**:
```python
async def deploy_agent_config(agent_id: str, config: AgentConfig) -> None:
async def rollback_agent(agent_id: str, version: str) -> None:
async def get_agent_metrics(agent_id: str, period: str) -> AgentMetrics:
async def validate_agent_config(config: AgentConfig) -> ValidationResult:
```

### `session_service.py` - Session Management Service (Future)
**Purpose**: Advanced session management with persistence and optimization.

**Planned Responsibilities**:
- Session creation and lifecycle management
- Context window optimization
- Session sharing and collaboration
- Session templates and presets
- Memory management and cleanup

**Planned Methods**:
```python
async def create_session(tenant_id: str, agent_id: str, config: SessionConfig) -> Session:
async def persist_session(session_id: str) -> None:
async def optimize_session_context(session_id: str) -> None:
async def cleanup_expired_sessions() -> int:
```

### `billing_service.py` - Usage Billing Service (Future)
**Purpose**: Handle usage-based billing and cost tracking.

**Planned Responsibilities**:
- Token usage cost calculation
- Invoice generation and management
- Payment processing integration
- Usage forecasting and alerts
- Cost optimization recommendations

**Planned Methods**:
```python
async def calculate_usage_cost(tenant_id: str, period: str) -> CostBreakdown:
async def generate_invoice(tenant_id: str, period: str) -> Invoice:
async def track_agent_costs(execution_id: str, cost: Decimal) -> None:
async def get_cost_forecast(tenant_id: str) -> CostForecast:
```

### `mcp_service.py` - MCP Coordination Service (Future)
**Purpose**: Manage Model Context Protocol server connections and tool discovery.

**Planned Responsibilities**:
- MCP server registration and health monitoring
- Tool discovery and capability mapping
- Load balancing across MCP servers
- Error handling and fallback strategies
- Security and access control for external tools

**Planned Methods**:
```python
async def register_mcp_server(server_config: MCPServerConfig) -> None:
async def discover_tools(server_id: str) -> List[ToolDefinition]:
async def execute_mcp_tool(tool_name: str, parameters: dict) -> ToolResult:
async def health_check_servers() -> Dict[str, ServerHealth]:
```

## Service Design Patterns

### Dependency Injection
Services receive their dependencies through constructor injection:

```python
class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository
```

This enables:
- Easy testing with mock repositories
- Loose coupling between layers
- Configuration flexibility
- Transaction management

### Error Handling Strategy
Services translate infrastructure errors to domain exceptions:

```python
async def get_tenant_by_api_key(self, api_key: str) -> Tenant:
    try:
        api_key_hash = ApiKey.hash_key(api_key)
        tenant = await self.tenant_repository.get_by_api_key_hash(api_key_hash)

        if not tenant:
            raise TenantNotFound("Invalid API key")

        if not tenant.is_active:
            raise InvalidApiKey("Tenant account is inactive")

        return tenant
    except RepositoryException as e:
        logger.error("Repository error during tenant lookup", error=str(e))
        raise InfrastructureException("Tenant lookup failed")
```

### Transaction Management
Services coordinate transactions across multiple repositories:

```python
async def create_tenant_with_initial_setup(self, tenant_data: TenantData) -> Tenant:
    async with self.unit_of_work.begin():
        # Create tenant
        tenant = await self.tenant_repository.create(tenant_data.to_tenant())

        # Set up initial agent permissions
        for agent_id in tenant_data.initial_agents:
            await self.permission_repository.grant_access(tenant.id, agent_id)

        # Create initial usage record
        await self.usage_repository.initialize(tenant.id)

        # Send welcome email
        await self.notification_service.send_welcome(tenant)

        return tenant
```

### Caching Integration
Services implement caching for frequently accessed data:

```python
async def get_tenant_by_api_key(self, api_key: str) -> Tenant:
    # Check cache first
    cache_key = f"tenant:key:{hash(api_key)}"
    cached_tenant = await self.cache.get(cache_key)
    if cached_tenant:
        return cached_tenant

    # Load from repository
    tenant = await self._load_tenant_by_api_key(api_key)

    # Cache for future requests
    await self.cache.set(cache_key, tenant, ttl=300)

    return tenant
```

## Service Integration Patterns

### With Domain Layer
Services use domain entities and enforce business rules:

```python
async def update_tenant_usage(self, tenant_id: str, tokens_used: int) -> None:
    tenant = await self.tenant_repository.get_by_id(tenant_id)

    # Use domain entity method for business logic
    tenant.add_token_usage(tokens_used)

    # Persist through repository
    await self.tenant_repository.update(tenant)
```

### With Infrastructure Layer
Services delegate to infrastructure for external concerns:

```python
async def send_usage_alert(self, tenant: Tenant) -> None:
    if tenant.usage_percentage > 80:
        await self.email_service.send_usage_warning(
            tenant.email,
            usage_percentage=tenant.usage_percentage,
            tier=tenant.tier
        )
```

### With Application Layer
Application handlers coordinate multiple services:

```python
class ExecuteAgentHandler:
    async def handle(self, command: ExecuteAgentCommand) -> ExecutionResult:
        # Use tenant service for validation
        tenant = await self.tenant_service.get_by_id(command.tenant_id)

        # Use agent service for execution
        result = await self.agent_service.execute(command.agent_id, command.parameters)

        # Use billing service for cost tracking
        await self.billing_service.record_usage(tenant.id, result.token_usage)

        return result
```

## Testing Strategies

### Unit Testing
Test services in isolation with mocked dependencies:

```python
class TestTenantService:
    async def test_create_tenant_success(self):
        # Arrange
        mock_repository = Mock(spec=TenantRepository)
        service = TenantService(mock_repository)

        # Act
        tenant, api_key = await service.create_tenant("Test Tenant")

        # Assert
        assert tenant.name == "Test Tenant"
        assert len(api_key) > 20  # Secure key length
        mock_repository.create.assert_called_once()

    async def test_get_tenant_by_invalid_key(self):
        # Arrange
        mock_repository = Mock(spec=TenantRepository)
        mock_repository.get_by_api_key_hash.return_value = None
        service = TenantService(mock_repository)

        # Act & Assert
        with pytest.raises(TenantNotFound):
            await service.get_tenant_by_api_key("invalid-key")
```

### Integration Testing
Test services with real database connections:

```python
class TestTenantServiceIntegration:
    async def test_tenant_lifecycle(self, db_session):
        # Arrange
        repository = TenantRepository(db_session)
        service = TenantService(repository)

        # Act
        tenant, api_key = await service.create_tenant("Integration Test")
        retrieved_tenant = await service.get_tenant_by_api_key(api_key)

        # Assert
        assert retrieved_tenant.id == tenant.id
        assert retrieved_tenant.name == "Integration Test"
```

## Performance Considerations

### Caching Strategy
- Tenant data cached after first lookup
- API key hash lookups cached for authentication
- Usage statistics cached with short TTL
- Agent configurations cached indefinitely

### Database Optimization
- Connection pooling for concurrent requests
- Read replicas for query-heavy operations
- Proper indexing on frequently accessed columns
- Batch operations for bulk updates

### Monitoring and Metrics
- Service call latency tracking
- Error rate monitoring per service method
- Cache hit/miss ratio tracking
- Database query performance analysis

## Security Considerations

### API Key Security
- Keys are hashed with salt before storage
- Plain-text keys never logged or persisted
- Secure random generation using cryptographic libraries
- Key rotation capabilities for security incidents

### Access Control
- All operations validate tenant ownership
- Agent access lists enforced consistently
- Rate limiting per tenant tier
- Audit logging for all sensitive operations

### Data Protection
- No sensitive data in log messages
- PII handling according to compliance requirements
- Secure data transmission and storage
- Regular security audits and updates

Services provide the business logic coordination layer while maintaining clean separation between domain rules and infrastructure implementation details.
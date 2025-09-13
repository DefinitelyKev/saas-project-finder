-- Basic tables for AI backend

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    allowed_agents JSON NOT NULL DEFAULT '[]'::json,
    monthly_tokens_used INTEGER NOT NULL DEFAULT 0,
    current_month VARCHAR(7) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    model VARCHAR(50) NOT NULL,
    system_prompt TEXT NOT NULL,
    tools JSON NOT NULL DEFAULT '[]'::json,
    parameters_schema JSON NOT NULL DEFAULT '{}'::json,
    max_tokens INTEGER NOT NULL DEFAULT 1000,
    temperature FLOAT NOT NULL DEFAULT 0.7,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    total_executions INTEGER NOT NULL DEFAULT 0,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    success_rate FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create executions table
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    agent_id VARCHAR(100) NOT NULL REFERENCES agents(id),
    session_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_parameters JSON NOT NULL DEFAULT '{}'::json,
    result JSON NOT NULL DEFAULT '{}'::json,
    error_message TEXT,
    token_usage INTEGER NOT NULL DEFAULT 0,
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    agent_id VARCHAR(100) NOT NULL REFERENCES agents(id),
    messages JSON NOT NULL DEFAULT '[]'::json,
    session_metadata JSON NOT NULL DEFAULT '{}'::json,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create usage_logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    agent_id VARCHAR(100) NOT NULL REFERENCES agents(id),
    execution_id UUID REFERENCES executions(id),
    tokens_used INTEGER NOT NULL DEFAULT 0,
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_type VARCHAR(100),
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tenants_api_key ON tenants(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_executions_tenant_agent ON executions(tenant_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_status_created ON executions(status, created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_active ON sessions(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_usage_logs_tenant_timestamp ON usage_logs(tenant_id, timestamp);
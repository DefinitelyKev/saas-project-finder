from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from src.config.constants import TenantTier, ExecutionStatus


# Request Schemas

class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tier: TenantTier = TenantTier.FREE
    allowed_agents: Optional[List[str]] = None


class ExecuteAgentRequest(BaseModel):
    parameters: Dict[str, Any] = Field(..., description="Parameters for agent execution")
    session_id: Optional[str] = Field(None, description="Session ID for stateful conversation")
    stream: bool = Field(False, description="Whether to stream the response")


class CreateSessionRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID for the session")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


# Response Schemas

class TenantResponse(BaseModel):
    id: str
    name: str
    tier: str
    allowed_agents: List[str]
    is_active: bool
    created_at: datetime


class CreateTenantResponse(BaseModel):
    tenant: TenantResponse
    api_key: str


class AgentToolResponse(BaseModel):
    type: str
    name: str
    description: str
    parameters: Dict[str, Any]


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    model: str
    tools: List[AgentToolResponse]
    parameters_schema: Dict[str, Any]
    max_tokens: int
    temperature: float
    total_executions: int
    success_rate: float


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int


class ExecutionResponse(BaseModel):
    id: str
    tenant_id: str
    agent_id: str
    session_id: Optional[str]
    status: str
    input_parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    token_usage: int
    execution_time_ms: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ExecuteAgentResponse(BaseModel):
    execution: ExecutionResponse


class AsyncExecuteResponse(BaseModel):
    job_id: str
    status: str
    message: str


class SessionResponse(BaseModel):
    id: str
    tenant_id: str
    agent_id: str
    message_count: int
    total_tokens_used: int
    created_at: datetime
    last_activity: datetime
    is_active: bool
    metadata: Dict[str, Any]


class CreateSessionResponse(BaseModel):
    session: SessionResponse


class UsageResponse(BaseModel):
    tenant_id: str
    name: str
    tier: str
    current_month: str
    tokens_used: int
    token_limit: int
    tokens_remaining: int
    usage_percentage: float
    rate_limit_per_minute: int
    max_sessions: int
    allowed_agents: List[str]


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    progress_percentage: Optional[int]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
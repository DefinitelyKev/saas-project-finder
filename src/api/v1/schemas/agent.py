from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from uuid import UUID


class ToolSchema(BaseModel):
    """Schema for agent tools."""

    type: str
    name: str
    description: str
    parameters: Dict[str, Any]


# Alias for backwards compatibility
AgentToolResponse = ToolSchema


class AgentResponse(BaseModel):
    """Response schema for agent details."""

    id: str
    name: str
    description: str
    model: str
    max_tokens: int
    temperature: float
    tools: List[ToolSchema]
    parameters_schema: Dict[str, Any]
    is_active: bool
    total_executions: int
    success_rate: float


class AgentListResponse(BaseModel):
    """Response schema for list of agents."""

    agents: List[AgentResponse]
    total: int


class ExecuteAgentRequest(BaseModel):
    """Request schema for agent execution."""

    parameters: Dict[str, Any]
    session_id: Optional[UUID] = None
    stream: bool = False


class ExecutionResponse(BaseModel):
    """Response schema for execution status."""

    id: str
    tenant_id: str
    agent_id: str
    session_id: Optional[str] = None
    status: str
    input_parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    token_usage: int
    execution_time_ms: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ExecuteAgentResponse(BaseModel):
    """Response schema for agent execution."""

    execution: ExecutionResponse


class AsyncExecuteResponse(BaseModel):
    """Response schema for async agent execution."""

    job_id: str
    status: str
    message: str
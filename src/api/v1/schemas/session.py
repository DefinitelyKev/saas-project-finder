from typing import Dict, Any, List
from pydantic import BaseModel
from uuid import UUID


class CreateSessionRequest(BaseModel):
    """Request schema for creating a session."""

    agent_id: str
    metadata: Dict[str, Any] = {}


class SessionResponse(BaseModel):
    """Response schema for session details."""

    id: str
    tenant_id: str
    agent_id: str
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    message_count: int
    total_tokens_used: int
    is_active: bool
    created_at: str
    last_activity: str


class CreateSessionResponse(BaseModel):
    """Response schema for creating a session."""

    session: SessionResponse
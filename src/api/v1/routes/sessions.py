from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.api.v1.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionResponse,
)
from src.api.v1.dependencies import get_current_tenant
from src.domain.entities.tenant import Tenant
from src.domain.entities.session import Session
from src.agents.config import get_agent_ids

router = APIRouter()
logger = structlog.get_logger()


@router.post("", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> CreateSessionResponse:
    """Create a new conversation session."""

    try:
        # Check if agent exists
        if request.agent_id not in get_agent_ids():
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

        # Check if tenant has access
        if not tenant.can_access_agent(request.agent_id):
            raise HTTPException(status_code=403, detail="Access denied to this agent")

        # Create session
        session = Session(
            tenant_id=tenant.id,
            agent_id=request.agent_id,
            metadata=request.metadata or {},
        )

        # TODO: Save session to database

        session_response = SessionResponse(
            id=str(session.id),
            tenant_id=str(session.tenant_id),
            agent_id=session.agent_id,
            messages=[],  # Empty for new session
            metadata=session.metadata,
            message_count=len(session.messages),
            total_tokens_used=session.total_tokens_used,
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            is_active=session.is_active and not session.is_expired(),
        )

        logger.info("Session created",
                   session_id=str(session.id),
                   agent_id=request.agent_id,
                   tenant_id=str(tenant.id))

        return CreateSessionResponse(session=session_response)

    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> SessionResponse:
    """Get session information."""

    try:
        # TODO: Get session from database
        # For now, return a mock response

        logger.info("Session retrieved",
                   session_id=session_id,
                   tenant_id=str(tenant.id))

        return SessionResponse(
            id=session_id,
            tenant_id=str(tenant.id),
            agent_id="customer-support",
            messages=[],  # Empty mock messages
            metadata={},
            message_count=0,
            total_tokens_used=0,
            created_at=tenant.created_at.isoformat(),
            last_activity=tenant.created_at.isoformat(),
            is_active=True,
        )

    except Exception as e:
        logger.error("Failed to get session", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    """Delete a session."""

    try:
        # TODO: Delete session from database

        logger.info("Session deleted",
                   session_id=session_id,
                   tenant_id=str(tenant.id))

        return {"message": "Session deleted successfully"}

    except Exception as e:
        logger.error("Failed to delete session", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
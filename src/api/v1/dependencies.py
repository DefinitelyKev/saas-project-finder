from fastapi import Depends, Request, HTTPException
from typing import AsyncGenerator

from src.domain.entities.tenant import Tenant
from src.infrastructure.persistence.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.persistence.repositories.tenant_repository import TenantRepository
from src.services.tenant_service import TenantService
from src.infrastructure.ai.openai_client import OpenAIClientWrapper
from src.infrastructure.ai.tool_executor import ToolExecutor
from src.infrastructure.ai.agent_executor import AgentExecutor


async def get_current_tenant(request: Request) -> Tenant:
    """Dependency to get current tenant from request state."""
    if not hasattr(request.state, "tenant"):
        raise HTTPException(status_code=401, detail="Tenant not found in request")
    return request.state.tenant


async def get_tenant_service(session: AsyncSession = Depends(get_db)) -> TenantService:
    """Dependency to get tenant service."""
    tenant_repository = TenantRepository(session)
    return TenantService(tenant_repository)


def get_openai_client() -> OpenAIClientWrapper:
    """Dependency to get OpenAI client."""
    return OpenAIClientWrapper()


def get_tool_executor() -> ToolExecutor:
    """Dependency to get tool executor."""
    return ToolExecutor()


def get_agent_executor(
    openai_client: OpenAIClientWrapper = Depends(get_openai_client),
    tool_executor: ToolExecutor = Depends(get_tool_executor),
) -> AgentExecutor:
    """Dependency to get agent executor."""
    return AgentExecutor(openai_client, tool_executor)
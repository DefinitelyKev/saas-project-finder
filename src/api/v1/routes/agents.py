from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import structlog
import json
from typing import AsyncGenerator, List, Dict, Any

from src.api.v1.schemas import (
    AgentResponse,
    AgentListResponse,
    AgentToolResponse,
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    AsyncExecuteResponse,
    ExecutionResponse,
)
from src.api.v1.dependencies import get_current_tenant, get_agent_executor
from src.domain.entities.tenant import Tenant
from src.domain.exceptions import DomainException, AgentNotFound
from src.infrastructure.ai.agent_executor import AgentExecutor
from src.agents.config import get_all_agent_configs, create_agent_from_config, get_agent_ids

router = APIRouter()
logger = structlog.get_logger()


@router.get("", response_model=AgentListResponse)
async def list_agents(
    tenant: Tenant = Depends(get_current_tenant),
) -> AgentListResponse:
    """List all agents available to the tenant."""

    try:
        agent_configs = get_all_agent_configs()
        available_agents: List[AgentResponse] = []

        for agent_id, config in agent_configs.items():
            # Check if tenant has access to this agent
            if tenant.can_access_agent(agent_id):
                agent = create_agent_from_config(agent_id)

                # Convert tools to response format
                tools = [
                    AgentToolResponse(
                        type=tool.type,
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.parameters,
                    )
                    for tool in agent.tools
                ]

                agent_response = AgentResponse(
                    id=agent.id,
                    name=agent.name,
                    description=agent.description,
                    model=agent.model,
                    tools=tools,
                    parameters_schema=agent.parameters_schema,
                    max_tokens=agent.max_tokens,
                    temperature=agent.temperature,
                    is_active=agent.is_active,
                    total_executions=agent.total_executions,
                    success_rate=agent.success_rate,
                )

                available_agents.append(agent_response)

        logger.info("Listed agents for tenant",
                   tenant_id=str(tenant.id),
                   agent_count=len(available_agents))

        return AgentListResponse(
            agents=available_agents,
            total=len(available_agents),
        )

    except Exception as e:
        logger.error("Failed to list agents", error=str(e), tenant_id=str(tenant.id))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> AgentResponse:
    """Get detailed information about a specific agent."""

    try:
        # Check if agent exists
        if agent_id not in get_agent_ids():
            raise AgentNotFound(f"Agent {agent_id} not found")

        # Check if tenant has access
        if not tenant.can_access_agent(agent_id):
            raise HTTPException(status_code=403, detail="Access denied to this agent")

        agent = create_agent_from_config(agent_id)

        # Convert tools to response format
        tools = [
            AgentToolResponse(
                type=tool.type,
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
            for tool in agent.tools
        ]

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            model=agent.model,
            tools=tools,
            parameters_schema=agent.parameters_schema,
            max_tokens=agent.max_tokens,
            temperature=agent.temperature,
            is_active=agent.is_active,
            total_executions=agent.total_executions,
            success_rate=agent.success_rate,
        )

    except AgentNotFound:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    except Exception as e:
        logger.error("Failed to get agent", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/execute", response_model=ExecuteAgentResponse)
async def execute_agent(
    agent_id: str,
    request: ExecuteAgentRequest,
    tenant: Tenant = Depends(get_current_tenant),
    agent_executor: AgentExecutor = Depends(get_agent_executor),
) -> ExecuteAgentResponse:
    """Execute an agent synchronously."""

    try:
        # Check if agent exists
        if agent_id not in get_agent_ids():
            raise AgentNotFound(f"Agent {agent_id} not found")

        # Check if tenant has access
        if not tenant.can_access_agent(agent_id):
            raise HTTPException(status_code=403, detail="Access denied to this agent")

        # Handle streaming response
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Use /execute-stream endpoint for streaming responses"
            )

        # Create agent
        agent = create_agent_from_config(agent_id)

        # Execute agent
        execution = await agent_executor.execute_sync(
            agent=agent,
            parameters=request.parameters,
            tenant=tenant,
            session=None,  # TODO: Handle session if provided
        )

        # Convert execution to response
        execution_response = ExecutionResponse(
            id=str(execution.id),
            tenant_id=str(execution.tenant_id),
            agent_id=execution.agent_id,
            session_id=str(execution.session_id) if execution.session_id else None,
            status=execution.status.value,
            input_parameters=execution.input_parameters,
            result=execution.result if execution.is_successful else None,
            error_message=execution.error_message,
            token_usage=execution.token_usage,
            execution_time_ms=execution.execution_time_ms,
            created_at=execution.created_at.isoformat(),
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        )

        logger.info("Agent executed successfully",
                   agent_id=agent_id,
                   execution_id=str(execution.id),
                   tenant_id=str(tenant.id))

        return ExecuteAgentResponse(execution=execution_response)

    except DomainException as e:
        logger.error("Agent execution failed", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during agent execution", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/execute-stream")
async def execute_agent_stream(
    agent_id: str,
    request: ExecuteAgentRequest,
    tenant: Tenant = Depends(get_current_tenant),
    agent_executor: AgentExecutor = Depends(get_agent_executor),
) -> StreamingResponse:
    """Execute an agent with streaming response."""

    try:
        # Check if agent exists
        if agent_id not in get_agent_ids():
            raise AgentNotFound(f"Agent {agent_id} not found")

        # Check if tenant has access
        if not tenant.can_access_agent(agent_id):
            raise HTTPException(status_code=403, detail="Access denied to this agent")

        # Create agent
        agent = create_agent_from_config(agent_id)

        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate streaming response."""
            try:
                async for chunk in agent_executor.execute_streaming(
                    agent=agent,
                    parameters=request.parameters,
                    tenant=tenant,
                    session=None,  # TODO: Handle session if provided
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"

                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                error_chunk = {"type": "error", "data": str(e)}
                yield f"data: {json.dumps(error_chunk)}\n\n"

        logger.info("Starting streaming agent execution",
                   agent_id=agent_id,
                   tenant_id=str(tenant.id))

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except DomainException as e:
        logger.error("Streaming agent execution failed", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during streaming execution", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/execute-async", response_model=AsyncExecuteResponse)
async def execute_agent_async(
    agent_id: str,
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    agent_executor: AgentExecutor = Depends(get_agent_executor),
) -> AsyncExecuteResponse:
    """Execute an agent asynchronously and return job ID."""

    try:
        # Check if agent exists
        if agent_id not in get_agent_ids():
            raise AgentNotFound(f"Agent {agent_id} not found")

        # Check if tenant has access
        if not tenant.can_access_agent(agent_id):
            raise HTTPException(status_code=403, detail="Access denied to this agent")

        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())

        # Create agent
        agent = create_agent_from_config(agent_id)

        # Add background task
        background_tasks.add_task(
            _execute_agent_background,
            job_id,
            agent,
            request.parameters,
            tenant,
            agent_executor,
        )

        logger.info("Async agent execution started",
                   agent_id=agent_id,
                   job_id=job_id,
                   tenant_id=str(tenant.id))

        return AsyncExecuteResponse(
            job_id=job_id,
            status="pending",
            message="Agent execution started in background",
        )

    except DomainException as e:
        logger.error("Async agent execution failed", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during async execution", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def _execute_agent_background(
    job_id: str,
    agent: Any,
    parameters: Dict[str, Any],
    tenant: Any,
    agent_executor: AgentExecutor,
) -> None:
    """Background task for agent execution."""

    try:
        execution = await agent_executor.execute_sync(
            agent=agent,
            parameters=parameters,
            tenant=tenant,
            session=None,
        )

        # TODO: Store job result in database or cache
        logger.info("Background agent execution completed",
                   job_id=job_id,
                   execution_id=str(execution.id))

    except Exception as e:
        logger.error("Background agent execution failed",
                    job_id=job_id,
                    error=str(e))
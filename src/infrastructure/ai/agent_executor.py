from typing import Dict, Any, Optional, AsyncGenerator
import json
import structlog
from datetime import datetime

from src.domain.entities.agent import Agent
from src.domain.entities.execution import Execution
from src.domain.entities.session import Session
from src.domain.entities.tenant import Tenant
from src.domain.exceptions import (
    AgentExecutionError,
    InvalidAgentParameters,
    UsageLimitExceeded,
)
from src.infrastructure.ai.openai_client import OpenAIClientWrapper
from src.infrastructure.ai.tool_executor import ToolExecutor

logger = structlog.get_logger()


class AgentExecutor:
    """Main service for executing AI agents."""

    def __init__(self, openai_client: OpenAIClientWrapper, tool_executor: ToolExecutor):
        self.openai_client = openai_client
        self.tool_executor = tool_executor

    async def execute_sync(
        self,
        agent: Agent,
        parameters: Dict[str, Any],
        tenant: Tenant,
        session: Optional[Session] = None,
    ) -> Execution:
        """Execute agent synchronously and return complete result."""

        # Create execution record
        execution = Execution(
            tenant_id=tenant.id,
            agent_id=agent.id,
            session_id=session.id if session else None,
            input_parameters=parameters,
        )

        try:
            # Validate parameters
            if not agent.validate_parameters(parameters):
                raise InvalidAgentParameters(f"Invalid parameters for agent {agent.id}")

            # Check usage limits
            if not tenant.has_tokens_remaining():
                raise UsageLimitExceeded(f"Token limit exceeded for tenant {tenant.id}")

            # Start execution
            execution.start()
            logger.info("Starting agent execution",
                       execution_id=str(execution.id),
                       agent_id=agent.id,
                       tenant_id=str(tenant.id))

            # Extract user input
            user_input = self._extract_user_input(parameters)

            # Execute with OpenAI
            response = await self.openai_client.create_completion(
                agent=agent,
                user_input=user_input,
                session=session,
                stream=False,
            )

            # Handle tool calls if present
            if response.get("tool_calls"):
                response = await self._handle_tool_calls(
                    agent, response, session
                )

            # Calculate token usage
            token_usage = response["usage"]["total_tokens"]

            # Update session if present
            if session:
                session.add_message("user", user_input)
                session.add_message(
                    "assistant",
                    response["content"],
                    token_count=token_usage,
                    tool_calls=response.get("tool_calls", [])
                )

            # Complete execution
            result = {
                "content": response["content"],
                "model": response["model"],
                "usage": response["usage"],
                "tool_calls": response.get("tool_calls", []),
            }

            execution.complete(result, token_usage)

            # Update agent stats
            agent.update_usage_stats(token_usage, True)

            # Update tenant usage
            tenant.add_token_usage(token_usage)

            logger.info("Agent execution completed successfully",
                       execution_id=str(execution.id),
                       tokens_used=token_usage)

            return execution

        except Exception as e:
            execution.fail(str(e))
            agent.update_usage_stats(0, False)

            logger.error("Agent execution failed",
                        execution_id=str(execution.id),
                        error=str(e))

            return execution

    async def execute_streaming(
        self,
        agent: Agent,
        parameters: Dict[str, Any],
        tenant: Tenant,
        session: Optional[Session] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute agent with streaming response."""

        # Validate parameters
        if not agent.validate_parameters(parameters):
            yield {"type": "error", "data": "Invalid parameters"}
            return

        # Check usage limits
        if not tenant.has_tokens_remaining():
            yield {"type": "error", "data": "Token limit exceeded"}
            return

        user_input = self._extract_user_input(parameters)

        logger.info("Starting streaming execution",
                   agent_id=agent.id,
                   tenant_id=str(tenant.id))

        try:
            async for chunk in self.openai_client.create_streaming_completion(
                agent=agent,
                user_input=user_input,
                session=session,
            ):
                yield chunk

        except Exception as e:
            logger.error("Streaming execution failed", error=str(e))
            yield {"type": "error", "data": str(e)}

    async def _handle_tool_calls(
        self,
        agent: Agent,
        response: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Handle tool calls in agent response."""

        tool_calls = response.get("tool_calls", [])
        tool_results = []

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])

            logger.info("Executing tool",
                       tool_name=function_name,
                       args=function_args)

            try:
                # Find the tool in agent configuration
                tool = agent.get_tool_by_name(function_name)
                if not tool:
                    raise AgentExecutionError(f"Tool {function_name} not found")

                # Execute the tool
                result = await self.tool_executor.execute_tool(
                    tool, function_args
                )

                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result),
                })

            except Exception as e:
                logger.error("Tool execution failed",
                           tool_name=function_name,
                           error=str(e))

                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": str(e)}),
                })

        # If we have tool results, make another API call to get final response
        if tool_results:
            messages = []
            if session:
                messages.extend(session.get_context_messages())

            messages.append({"role": "assistant", "content": response["content"], "tool_calls": tool_calls})
            messages.extend(tool_results)

            # Make follow-up API call
            final_response = await self.openai_client.client.chat.completions.create(
                model=agent.model,
                messages=messages,
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
            )

            # Update response with final result
            final_message = final_response.choices[0].message
            response.update({
                "content": final_message.content,
                "usage": {
                    "prompt_tokens": response["usage"]["prompt_tokens"] + final_response.usage.prompt_tokens,
                    "completion_tokens": response["usage"]["completion_tokens"] + final_response.usage.completion_tokens,
                    "total_tokens": response["usage"]["total_tokens"] + final_response.usage.total_tokens,
                },
                "tool_results": tool_results,
            })

        return response

    def _extract_user_input(self, parameters: Dict[str, Any]) -> str:
        """Extract user input from parameters."""
        # Try common parameter names for user input
        for key in ["user_input", "message", "query", "text", "content"]:
            if key in parameters:
                return str(parameters[key])

        # If no standard key found, use the first string parameter
        for value in parameters.values():
            if isinstance(value, str):
                return value

        # Fallback: stringify the parameters
        return json.dumps(parameters)
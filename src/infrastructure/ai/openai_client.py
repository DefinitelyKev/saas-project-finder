from typing import Dict, Any, List, Optional, AsyncGenerator, cast
import json
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage, ChatCompletion
from openai.types import CompletionUsage
import structlog

from src.config.settings import settings
from src.domain.entities.agent import Agent
from src.domain.entities.session import Session
from src.domain.exceptions import AgentExecutionError

logger = structlog.get_logger()


class OpenAIClientWrapper:
    """Wrapper around OpenAI client with custom functionality."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id,
        )

    async def create_completion(
        self,
        agent: Agent,
        user_input: str,
        session: Optional[Session] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Create a completion using the agent configuration."""

        try:
            # Build messages
            messages = self._build_messages(agent, user_input, session)

            # Prepare tools for OpenAI format
            tools = self._prepare_tools(agent)

            # Make API call
            call_params = {
                "model": agent.model,
                "messages": cast(Any, messages),  # Cast to handle type compatibility
                "max_tokens": agent.max_tokens,
                "temperature": agent.temperature,
                "stream": stream,
            }
            if tools:
                call_params["tools"] = cast(Any, tools)

            response = await self.client.chat.completions.create(**call_params)

            if stream:
                return {"response": response, "streaming": True}
            else:
                # Cast to regular completion for non-streaming
                completion = cast(ChatCompletion, response)
                # Extract response data
                message = completion.choices[0].message
                usage = completion.usage or CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

                result = {
                    "content": message.content,
                    "tool_calls": self._extract_tool_calls(message),
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                    "model": completion.model,
                    "streaming": False,
                }

                return result

        except Exception as e:
            logger.error("OpenAI API error", error=str(e), agent_id=agent.id)
            raise AgentExecutionError(f"Failed to execute agent: {str(e)}")

    async def create_streaming_completion(
        self,
        agent: Agent,
        user_input: str,
        session: Optional[Session] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Create a streaming completion."""

        messages = self._build_messages(agent, user_input, session)
        tools = self._prepare_tools(agent)

        try:
            call_params = {
                "model": agent.model,
                "messages": cast(Any, messages),  # Cast to handle type compatibility
                "max_tokens": agent.max_tokens,
                "temperature": agent.temperature,
                "stream": True,
            }
            if tools:
                call_params["tools"] = cast(Any, tools)

            stream = await self.client.chat.completions.create(**call_params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "data": chunk.choices[0].delta.content,
                    }

                if chunk.choices[0].delta.tool_calls:
                    yield {
                        "type": "tool_call",
                        "data": chunk.choices[0].delta.tool_calls,
                    }

                if chunk.choices[0].finish_reason:
                    yield {
                        "type": "finish",
                        "data": chunk.choices[0].finish_reason,
                    }

        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e), agent_id=agent.id)
            yield {
                "type": "error",
                "data": f"Streaming failed: {str(e)}",
            }

    def _build_messages(
        self,
        agent: Agent,
        user_input: str,
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Build message array for OpenAI API."""

        messages = [
            {"role": "system", "content": agent.system_prompt}
        ]

        # Add session context if available
        if session:
            messages.extend(session.get_context_messages())

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def _prepare_tools(self, agent: Agent) -> Optional[List[Dict[str, Any]]]:
        """Prepare tools in OpenAI function calling format."""

        if not agent.tools:
            return None

        tools = []
        for tool in agent.get_function_tools():
            tool_spec = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            tools.append(tool_spec)

        return tools if tools else None

    def _extract_tool_calls(self, message) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI response message."""

        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            return []

        tool_calls = []
        for tool_call in message.tool_calls:
            tool_calls.append({
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                }
            })

        return tool_calls

    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate token count for text."""
        # Simple estimation - in production would use tiktoken
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // 4

    async def validate_model(self, model: str) -> bool:
        """Validate if model is available."""
        try:
            models = await self.client.models.list()
            available_models = [model.id for model in models.data]
            return model in available_models
        except Exception:
            return False
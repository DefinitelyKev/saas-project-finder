from typing import Any, Dict, List, Optional, AsyncGenerator
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
import json
import structlog

logger = structlog.get_logger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion | AsyncGenerator[ChatCompletionChunk, None]:
        """Create a chat completion"""
        try:
            completion_args = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs,
            }
            
            if max_tokens:
                completion_args["max_tokens"] = max_tokens
            
            if tools:
                completion_args["tools"] = tools
            
            if tool_choice:
                completion_args["tool_choice"] = tool_choice
            
            logger.info(
                "Creating OpenAI completion",
                model=completion_args["model"],
                message_count=len(messages),
                stream=stream,
                has_tools=bool(tools),
            )
            
            response = await self.client.chat.completions.create(**completion_args)
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return response
                
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def _handle_stream_response(
        self, response: AsyncGenerator[ChatCompletionChunk, None]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Handle streaming response"""
        try:
            async for chunk in response:
                yield chunk
        except Exception as e:
            logger.error("Error in streaming response", error=str(e))
            raise
    
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create an OpenAI Assistant"""
        try:
            assistant_args = {
                "name": name,
                "instructions": instructions,
                "model": model or self.model,
            }
            
            if tools:
                assistant_args["tools"] = tools
            
            if file_ids:
                assistant_args["file_ids"] = file_ids
            
            if metadata:
                assistant_args["metadata"] = metadata
            
            logger.info("Creating OpenAI assistant", name=name, model=assistant_args["model"])
            
            assistant = await self.client.beta.assistants.create(**assistant_args)
            return assistant.model_dump()
            
        except Exception as e:
            logger.error("Error creating assistant", error=str(e))
            raise
    
    async def create_thread(self, messages: Optional[List[Dict[str, Any]]] = None) -> str:
        """Create a conversation thread"""
        try:
            thread_args = {}
            if messages:
                thread_args["messages"] = messages
            
            thread = await self.client.beta.threads.create(**thread_args)
            logger.info("Created thread", thread_id=thread.id)
            return thread.id
            
        except Exception as e:
            logger.error("Error creating thread", error=str(e))
            raise
    
    async def add_message_to_thread(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        file_ids: Optional[List[str]] = None,
    ) -> str:
        """Add a message to a thread"""
        try:
            message_args = {
                "thread_id": thread_id,
                "role": role,
                "content": content,
            }
            
            if file_ids:
                message_args["file_ids"] = file_ids
            
            message = await self.client.beta.threads.messages.create(**message_args)
            logger.info("Added message to thread", thread_id=thread_id, message_id=message.id)
            return message.id
            
        except Exception as e:
            logger.error("Error adding message to thread", error=str(e))
            raise
    
    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Run an assistant on a thread"""
        try:
            run_args = {
                "thread_id": thread_id,
                "assistant_id": assistant_id,
            }
            
            if instructions:
                run_args["instructions"] = instructions
            
            if additional_instructions:
                run_args["additional_instructions"] = additional_instructions
            
            if tools:
                run_args["tools"] = tools
            
            if metadata:
                run_args["metadata"] = metadata
            
            run = await self.client.beta.threads.runs.create(**run_args)
            logger.info("Started assistant run", thread_id=thread_id, run_id=run.id)
            return run.id
            
        except Exception as e:
            logger.error("Error running assistant", error=str(e))
            raise
    
    async def get_run_status(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Get the status of a run"""
        try:
            run = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            return run.model_dump()
        except Exception as e:
            logger.error("Error getting run status", error=str(e))
            raise
    
    async def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a thread"""
        try:
            messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
            return [message.model_dump() for message in messages.data]
        except Exception as e:
            logger.error("Error getting thread messages", error=str(e))
            raise
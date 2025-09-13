from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4


@dataclass
class SessionMessage:
    """Represents a message in a conversation session."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Session:
    """Session entity for stateful conversations."""

    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    messages: List[SessionMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    total_tokens_used: int = 0
    is_active: bool = True

    # Session limits
    max_messages: int = 100
    max_tokens: int = 4000
    session_timeout_hours: int = 24

    def add_message(self, role: str, content: str, token_count: int = 0, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add a message to the session."""
        if tool_calls is None:
            tool_calls = []

        message = SessionMessage(
            role=role,
            content=content,
            token_count=token_count,
            tool_calls=tool_calls
        )

        self.messages.append(message)
        self.total_tokens_used += token_count
        self.last_activity = datetime.utcnow()

        # Trim messages if exceeding limits
        self._trim_if_needed()

    def get_context_messages(self) -> List[Dict[str, Any]]:
        """Get messages formatted for OpenAI API."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {})
            }
            for msg in self.messages
        ]

    def _trim_if_needed(self) -> None:
        """Trim old messages if limits exceeded."""
        # Trim by message count
        if len(self.messages) > self.max_messages:
            # Keep system messages and recent messages
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]

            # Keep most recent messages
            keep_count = self.max_messages - len(system_messages)
            recent_messages = other_messages[-keep_count:]

            self.messages = system_messages + recent_messages

        # Trim by token count
        if self.total_tokens_used > self.max_tokens:
            # Remove oldest non-system messages until under limit
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]

            current_tokens = sum(msg.token_count for msg in system_messages)
            kept_messages = []

            for msg in reversed(other_messages):
                if current_tokens + msg.token_count <= self.max_tokens:
                    kept_messages.insert(0, msg)
                    current_tokens += msg.token_count
                else:
                    break

            self.messages = system_messages + kept_messages
            self.total_tokens_used = current_tokens

    def is_expired(self) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(hours=self.session_timeout_hours)
        return datetime.utcnow() > expiry_time

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "agent_id": self.agent_id,
            "message_count": len(self.messages),
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active and not self.is_expired(),
            "metadata": self.metadata,
        }
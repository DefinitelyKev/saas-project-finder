from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from src.config.constants import ExecutionStatus


@dataclass
class Execution:
    """Execution entity representing an agent execution instance."""

    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    session_id: Optional[UUID] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    token_usage: int = 0
    execution_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def start(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete(self, result: Dict[str, Any], token_usage: int) -> None:
        """Mark execution as completed successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.result = result
        self.token_usage = token_usage
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.execution_time_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )

    def fail(self, error_message: str) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.execution_time_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)."""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "agent_id": self.agent_id,
            "session_id": str(self.session_id) if self.session_id else None,
            "status": self.status.value,
            "input_parameters": self.input_parameters,
            "result": self.result if self.is_successful else None,
            "error_message": self.error_message,
            "token_usage": self.token_usage,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
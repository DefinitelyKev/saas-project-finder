from typing import Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class JobStatusResponse(BaseModel):
    """Response schema for job status."""

    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    progress_percentage: int = 0
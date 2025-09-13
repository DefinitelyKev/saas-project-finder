from typing import Dict, Any, List
from pydantic import BaseModel
from uuid import UUID


class UsageResponse(BaseModel):
    """Response schema for usage data."""

    tenant_id: UUID
    current_month: str
    monthly_tokens_used: int
    total_cost_usd: float
    usage_by_agent: Dict[str, int]
    daily_usage: List[Dict[str, Any]]
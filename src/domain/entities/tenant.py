from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from src.config.constants import TenantTier, TIER_LIMITS


@dataclass
class Tenant:
    """Tenant entity representing a SaaS project."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    api_key_hash: str = ""
    tier: TenantTier = TenantTier.FREE
    allowed_agents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    # Usage tracking
    monthly_tokens_used: int = 0
    current_month: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m"))

    @property
    def monthly_token_limit(self) -> int:
        """Get monthly token limit based on tier."""
        return TIER_LIMITS[self.tier]["monthly_tokens"]

    @property
    def rate_limit_per_minute(self) -> int:
        """Get rate limit per minute based on tier."""
        return TIER_LIMITS[self.tier]["requests_per_minute"]

    @property
    def max_sessions(self) -> int:
        """Get maximum sessions based on tier."""
        return TIER_LIMITS[self.tier]["max_sessions"]

    def can_access_agent(self, agent_id: str) -> bool:
        """Check if tenant can access specific agent."""
        return agent_id in self.allowed_agents or len(self.allowed_agents) == 0

    def has_tokens_remaining(self) -> bool:
        """Check if tenant has tokens remaining this month."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        if current_month != self.current_month:
            # Reset usage for new month
            self.monthly_tokens_used = 0
            self.current_month = current_month

        return self.monthly_tokens_used < self.monthly_token_limit

    def add_token_usage(self, tokens: int) -> None:
        """Add token usage to current month."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        if current_month != self.current_month:
            # Reset usage for new month
            self.monthly_tokens_used = 0
            self.current_month = current_month

        self.monthly_tokens_used += tokens
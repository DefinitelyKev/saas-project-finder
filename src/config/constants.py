from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TenantTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AgentType(str, Enum):
    CUSTOMER_SUPPORT = "customer-support"
    DATA_ANALYST = "data-analyst"
    CONTENT_WRITER = "content-writer"
    CODE_REVIEWER = "code-reviewer"


# Default limits by tier
TIER_LIMITS = {
    TenantTier.FREE: {
        "monthly_tokens": 10000,
        "requests_per_minute": 10,
        "max_sessions": 5,
    },
    TenantTier.PRO: {
        "monthly_tokens": 100000,
        "requests_per_minute": 50,
        "max_sessions": 25,
    },
    TenantTier.ENTERPRISE: {
        "monthly_tokens": 1000000,
        "requests_per_minute": 200,
        "max_sessions": 100,
    },
}

# API Configuration
API_V1_PREFIX = "/api/v1"
API_TITLE = "AI Backend API"
API_DESCRIPTION = "Central AI Multi-Tenant Backend for SaaS Projects"
API_VERSION = "1.0.0"

# Cache Keys
CACHE_KEY_TENANT = "tenant:{tenant_id}"
CACHE_KEY_AGENT = "agent:{agent_id}"
CACHE_KEY_RATE_LIMIT = "rate_limit:{tenant_id}"
CACHE_KEY_USAGE = "usage:{tenant_id}:{period}"
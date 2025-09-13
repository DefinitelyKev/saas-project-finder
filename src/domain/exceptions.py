class DomainException(Exception):
    """Base exception for domain-level errors."""
    pass


class TenantNotFound(DomainException):
    """Raised when a tenant is not found."""
    pass


class AgentNotFound(DomainException):
    """Raised when an agent is not found."""
    pass


class RateLimitExceeded(DomainException):
    """Raised when rate limit is exceeded."""
    pass


class InvalidApiKey(DomainException):
    """Raised when API key is invalid."""
    pass


class AgentExecutionError(DomainException):
    """Raised when agent execution fails."""
    pass


class SessionNotFound(DomainException):
    """Raised when a session is not found."""
    pass


class UsageLimitExceeded(DomainException):
    """Raised when usage limit is exceeded."""
    pass


class InvalidAgentParameters(DomainException):
    """Raised when agent parameters are invalid."""
    pass
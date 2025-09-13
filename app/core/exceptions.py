class SaaSBackendException(Exception):
    """Base exception class for SaaS Backend"""
    pass


class TenantError(SaaSBackendException):
    """Base tenant-related exception"""
    pass


class TenantNotFoundError(TenantError):
    """Tenant not found"""
    pass


class TenantAlreadyExistsError(TenantError):
    """Tenant already exists"""
    pass


class TenantInactiveError(TenantError):
    """Tenant is inactive"""
    pass


class AuthenticationError(SaaSBackendException):
    """Authentication failed"""
    pass


class AuthorizationError(SaaSBackendException):
    """Authorization failed"""
    pass


class RateLimitError(SaaSBackendException):
    """Rate limit exceeded"""
    pass


class AIServiceError(SaaSBackendException):
    """AI service error"""
    pass


class MCPError(SaaSBackendException):
    """MCP protocol error"""
    pass
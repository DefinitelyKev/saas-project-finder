from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant information from various sources:
    1. Subdomain (tenant.yourdomain.com)
    2. Custom header (X-Tenant-ID)
    3. Path parameter (/tenant/{tenant_id}/...)
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = await self._extract_tenant_id(request)
        
        # Skip tenant validation for certain paths
        if self._should_skip_tenant_validation(request.url.path):
            return await call_next(request)
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required"
            )
        
        # Add tenant_id to request state
        request.state.tenant_id = tenant_id
        
        return await call_next(request)
    
    async def _extract_tenant_id(self, request: Request) -> str | None:
        # 1. Try to extract from subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain and subdomain not in ["www", "api", "localhost"]:
                return subdomain
        
        # 2. Try to extract from custom header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return tenant_header
        
        # 3. Try to extract from path
        path_match = re.match(r"/api/v1/tenant/([^/]+)/", request.url.path)
        if path_match:
            return path_match.group(1)
        
        return None
    
    def _should_skip_tenant_validation(self, path: str) -> bool:
        """Paths that don't require tenant identification"""
        skip_patterns = [
            r"/api/v1/health",
            r"/api/v1/auth/register",
            r"/api/v1/tenants",  # Tenant management endpoints
            r"/docs",
            r"/openapi.json",
            r"/redoc",
            r"/metrics",
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, path):
                return True
        return False
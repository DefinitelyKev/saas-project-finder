from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import structlog

from src.services.tenant_service import TenantService
from src.infrastructure.persistence.repositories.tenant_repository import TenantRepository
from src.infrastructure.persistence.database import get_db_session
from src.domain.exceptions import TenantNotFound, InvalidApiKey

logger = structlog.get_logger()


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to resolve tenant from API key."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # Paths that don't require tenant resolution
        self.public_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and resolve tenant."""

        # Skip tenant resolution for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        # Skip if no API key (will be handled by auth middleware)
        if not hasattr(request.state, "api_key"):
            return await call_next(request)

        try:
            # Get database session
            async with get_db_session() as session:
                tenant_repository = TenantRepository(session)
                tenant_service = TenantService(tenant_repository)

                # Resolve tenant from API key
                tenant = await tenant_service.get_tenant_by_api_key(request.state.api_key)

                # Store tenant in request state
                request.state.tenant = tenant

                logger.debug(
                    "Tenant resolved", tenant_id=str(tenant.id), tenant_name=tenant.name, path=request.url.path
                )

        except (TenantNotFound, InvalidApiKey) as e:
            logger.warning("Tenant resolution failed", error=str(e), path=request.url.path)
            return JSONResponse(status_code=401, content={"error": "Unauthorized", "detail": "Invalid API key"})
        except Exception as e:
            logger.error("Tenant middleware error", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=500, content={"error": "Internal Server Error", "detail": "Tenant resolution failed"}
            )

        # Continue to next middleware
        response = await call_next(request)
        return response

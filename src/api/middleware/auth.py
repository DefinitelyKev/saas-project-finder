from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger()


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API key authentication."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and validate API key."""

        # Skip auth for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        # Extract API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix

        if not api_key:
            logger.warning("Missing API key", path=request.url.path)
            return JSONResponse(status_code=401, content={"error": "Unauthorized", "detail": "API key required"})

        # Store API key in request state for tenant middleware
        request.state.api_key = api_key

        # Continue to next middleware
        response = await call_next(request)
        return response

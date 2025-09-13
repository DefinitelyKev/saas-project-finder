from typing import Dict, List, Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import structlog
import time
import asyncio

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to handle rate limiting per tenant."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # In-memory rate limiting (in production, use Redis)
        self.request_counts: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()

        # Paths that don't count towards rate limiting
        self.exempt_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and apply rate limiting."""

        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Skip if no tenant (will be handled by other middleware)
        if not hasattr(request.state, "tenant"):
            return await call_next(request)

        tenant = request.state.tenant
        tenant_id = str(tenant.id)
        current_time = time.time()

        try:
            # Check rate limit
            if await self._is_rate_limited(tenant_id, tenant.rate_limit_per_minute, current_time):
                logger.warning("Rate limit exceeded",
                              tenant_id=tenant_id,
                              path=request.url.path)

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate Limit Exceeded",
                        "detail": f"Maximum {tenant.rate_limit_per_minute} requests per minute",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )

            # Record this request
            await self._record_request(tenant_id, current_time)

        except Exception as e:
            logger.error("Rate limit middleware error",
                        error=str(e),
                        tenant_id=tenant_id)
            # Continue processing - don't fail requests due to rate limiting errors

        # Continue to next middleware
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = await self._get_remaining_requests(tenant_id, tenant.rate_limit_per_minute, current_time)
        response.headers["X-RateLimit-Limit"] = str(tenant.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response

    async def _is_rate_limited(self, tenant_id: str, limit: int, current_time: float) -> bool:
        """Check if tenant has exceeded rate limit."""

        async with self.lock:
            # Get request history for tenant
            requests = self.request_counts.get(tenant_id, [])

            # Remove requests older than 1 minute
            cutoff_time = current_time - 60
            recent_requests = [req_time for req_time in requests if req_time > cutoff_time]

            # Update the stored requests
            self.request_counts[tenant_id] = recent_requests

            # Check if limit exceeded
            return len(recent_requests) >= limit

    async def _record_request(self, tenant_id: str, request_time: float) -> None:
        """Record a new request for the tenant."""

        async with self.lock:
            if tenant_id not in self.request_counts:
                self.request_counts[tenant_id] = []

            self.request_counts[tenant_id].append(request_time)

            # Clean up old entries to prevent memory leak
            cutoff_time = request_time - 60
            self.request_counts[tenant_id] = [
                req_time for req_time in self.request_counts[tenant_id]
                if req_time > cutoff_time
            ]

    async def _get_remaining_requests(self, tenant_id: str, limit: int, current_time: float) -> int:
        """Get remaining requests for tenant in current window."""

        async with self.lock:
            requests = self.request_counts.get(tenant_id, [])
            cutoff_time = current_time - 60
            recent_requests = [req_time for req_time in requests if req_time > cutoff_time]

            return limit - len(recent_requests)

    async def cleanup_old_entries(self) -> None:
        """Cleanup old entries to prevent memory leaks (call periodically)."""

        current_time = time.time()
        cutoff_time = current_time - 300  # Keep 5 minutes of history

        async with self.lock:
            for tenant_id in list(self.request_counts.keys()):
                self.request_counts[tenant_id] = [
                    req_time for req_time in self.request_counts[tenant_id]
                    if req_time > cutoff_time
                ]

                # Remove empty entries
                if not self.request_counts[tenant_id]:
                    del self.request_counts[tenant_id]
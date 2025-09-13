import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Get tenant info if available
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            tenant_id=tenant_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None,
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                request_id=request_id,
                tenant_id=tenant_id,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "Request failed",
                request_id=request_id,
                tenant_id=tenant_id,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise
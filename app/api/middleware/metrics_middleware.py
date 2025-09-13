import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'tenant_id']
)

ACTIVE_REQUESTS = Counter(
    'http_requests_active',
    'Active HTTP requests',
    ['tenant_id']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        tenant_id = getattr(request.state, 'tenant_id', 'unknown')
        method = request.method
        endpoint = self._get_endpoint_name(request.url.path)
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(tenant_id=tenant_id).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = str(response.status_code)
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                tenant_id=tenant_id
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                tenant_id=tenant_id
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code="500",
                tenant_id=tenant_id
            ).inc()
            
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                tenant_id=tenant_id
            ).observe(duration)
            
            raise
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.labels(tenant_id=tenant_id).dec()
    
    def _get_endpoint_name(self, path: str) -> str:
        """Normalize endpoint names for metrics"""
        # Replace UUIDs and dynamic segments with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path
        )
        
        # Replace other dynamic segments (simple approach)
        path = re.sub(r'/[^/]+/([0-9]+)$', r'/\1/{id}', path)
        
        return path or "/"


# Metrics endpoint handler
async def metrics_handler() -> Response:
    """Return Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
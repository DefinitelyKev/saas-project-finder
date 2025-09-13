from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from src.config.settings import settings
from src.config.constants import API_V1_PREFIX, API_TITLE, API_DESCRIPTION, API_VERSION
from src.api.middleware.tenant import TenantMiddleware
from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.api.v1.routes import auth, agents, sessions, jobs, usage, saas_ideas
from src.domain.exceptions import DomainException, TenantNotFound, AgentNotFound, RateLimitExceeded
from src.services.scheduler import SaaSProjectFinderScheduler
from src.infrastructure.persistence.database import get_async_session_factory
import os

# Configure structured logging
logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        debug=settings.debug,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Custom Middleware
    app.add_middleware(TenantMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Exception Handlers
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        logger.error("Domain exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=400,
            content={"error": exc.__class__.__name__, "detail": str(exc)}
        )

    @app.exception_handler(TenantNotFound)
    async def tenant_not_found_handler(request: Request, exc: TenantNotFound) -> JSONResponse:
        logger.warning("Tenant not found", tenant_id=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "detail": "Invalid API key"}
        )

    @app.exception_handler(AgentNotFound)
    async def agent_not_found_handler(request: Request, exc: AgentNotFound) -> JSONResponse:
        logger.warning("Agent not found", agent_id=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=404,
            content={"error": "Not Found", "detail": f"Agent '{exc}' not found"}
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        logger.warning("Rate limit exceeded", tenant_id=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=429,
            content={"error": "Rate Limit Exceeded", "detail": "Too many requests"}
        )

    # Health Check
    @app.get("/health")
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "version": API_VERSION,
            "environment": settings.environment
        }

    # API Routes
    app.include_router(auth.router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
    app.include_router(agents.router, prefix=f"{API_V1_PREFIX}/agents", tags=["Agents"])
    app.include_router(sessions.router, prefix=f"{API_V1_PREFIX}/sessions", tags=["Sessions"])
    app.include_router(jobs.router, prefix=f"{API_V1_PREFIX}/jobs", tags=["Jobs"])
    app.include_router(usage.router, prefix=f"{API_V1_PREFIX}/usage", tags=["Usage"])
    app.include_router(saas_ideas.router, prefix=f"{API_V1_PREFIX}/saas-ideas", tags=["SaaS Ideas"])

    # Application State
    app.state.scheduler = None

    # Startup and Shutdown Events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on application startup."""
        try:
            # Initialize scheduler if enabled
            scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

            if scheduler_enabled:
                session_factory = get_async_session_factory()
                scheduler = SaaSProjectFinderScheduler(session_factory)
                await scheduler.start()
                app.state.scheduler = scheduler

                logger.info("SaaS Project Finder scheduler started successfully")
            else:
                logger.info("SaaS Project Finder scheduler disabled")

        except Exception as e:
            logger.error("Failed to initialize services on startup", error=str(e))
            # Don't raise - let the app start even if scheduler fails

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on application shutdown."""
        try:
            # Stop scheduler if running
            if app.state.scheduler:
                await app.state.scheduler.stop()
                logger.info("SaaS Project Finder scheduler stopped successfully")

        except Exception as e:
            logger.error("Failed to clean up resources on shutdown", error=str(e))

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
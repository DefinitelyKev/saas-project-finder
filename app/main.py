from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.container import container
from app.api.middleware.tenant_middleware import TenantMiddleware
from app.api.middleware.logging_middleware import LoggingMiddleware
from app.api.middleware.metrics_middleware import MetricsMiddleware
from app.api.v1.api import api_router
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await container.database_manager().initialize()
    await container.redis_client().initialize()
    yield
    # Shutdown
    await container.database_manager().close()
    await container.redis_client().close()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Custom middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TenantMiddleware)

    # Wire container
    container.wire(
        modules=[
            "app.api.v1.endpoints.tenants",
            "app.api.v1.endpoints.auth",
            "app.api.v1.endpoints.ai",
            "app.api.v1.endpoints.projects",
        ]
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

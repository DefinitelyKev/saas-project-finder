from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from app.core.config import Settings
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.cache.redis_client import RedisClient
from app.infrastructure.external.openai_client import OpenAIClient
from app.infrastructure.external.mcp_client import MCPClient
from app.services.tenant_service import TenantService
from app.services.ai_service import AIService
from app.services.auth_service import AuthService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[
        "app.api.v1.endpoints.tenants",
        "app.api.v1.endpoints.auth",
        "app.api.v1.endpoints.ai",
        "app.api.v1.endpoints.projects",
    ])
    
    # Configuration
    config = providers.Singleton(Settings)
    
    # Infrastructure
    database_manager = providers.Singleton(
        DatabaseManager,
        database_url=config.provided.DATABASE_URL,
        pool_size=config.provided.DATABASE_POOL_SIZE,
        pool_overflow=config.provided.DATABASE_POOL_OVERFLOW,
    )
    
    redis_client = providers.Singleton(
        RedisClient,
        redis_url=config.provided.REDIS_URL,
    )
    
    openai_client = providers.Singleton(
        OpenAIClient,
        api_key=config.provided.OPENAI_API_KEY,
        model=config.provided.OPENAI_MODEL,
    )
    
    mcp_client = providers.Singleton(
        MCPClient,
        enabled=config.provided.MCP_ENABLED,
    )
    
    # Services
    tenant_service = providers.Factory(
        TenantService,
        database_manager=database_manager,
        redis_client=redis_client,
    )
    
    auth_service = providers.Factory(
        AuthService,
        database_manager=database_manager,
        redis_client=redis_client,
        secret_key=config.provided.SECRET_KEY,
        algorithm=config.provided.ALGORITHM,
    )
    
    ai_service = providers.Factory(
        AIService,
        openai_client=openai_client,
        mcp_client=mcp_client,
        database_manager=database_manager,
    )


container = Container()
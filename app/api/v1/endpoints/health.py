from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.container import Container, Provide
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.cache.redis_client import RedisClient

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check"""
    return {"status": "healthy", "service": "SaaS AI Backend"}


@router.get("/detailed")
async def detailed_health_check(
    db_manager: DatabaseManager = Depends(Provide[Container.database_manager]),
    redis_client: RedisClient = Depends(Provide[Container.redis_client]),
) -> Dict[str, Any]:
    """Detailed health check with dependencies"""
    checks = {
        "database": await db_manager.health_check(),
        "redis": await redis_client.health_check(),
    }
    
    overall_healthy = all(checks.values())
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "service": "SaaS AI Backend",
        "checks": checks
    }
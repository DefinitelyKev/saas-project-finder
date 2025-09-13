from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.api.v1.schemas import (
    CreateTenantRequest,
    CreateTenantResponse,
    TenantResponse,
    UsageResponse,
)
from src.api.v1.dependencies import get_tenant_service, get_current_tenant
from src.services.tenant_service import TenantService
from src.domain.entities.tenant import Tenant
from src.domain.exceptions import DomainException
from src.config.constants import TenantTier

router = APIRouter()
logger = structlog.get_logger()


@router.post("/register", response_model=CreateTenantResponse)
async def register_tenant(
    request: CreateTenantRequest,
    tenant_service: TenantService = Depends(get_tenant_service),
) -> CreateTenantResponse:
    """Register a new tenant and get API key."""

    try:
        tenant, api_key = await tenant_service.create_tenant(
            name=request.name,
            tier=TenantTier(request.tier),
            allowed_agents=request.allowed_agents or [],
        )

        tenant_response = TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            tier=tenant.tier.value,
            allowed_agents=tenant.allowed_agents,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
        )

        logger.info("Tenant registered successfully",
                   tenant_id=str(tenant.id),
                   name=request.name)

        return CreateTenantResponse(
            tenant=tenant_response,
            api_key=api_key,
        )

    except DomainException as e:
        logger.error("Tenant registration failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during tenant registration", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/validate", response_model=TenantResponse)
async def validate_api_key(
    tenant: Tenant = Depends(get_current_tenant),
) -> TenantResponse:
    """Validate API key and return tenant information."""

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        tier=tenant.tier.value,
        allowed_agents=tenant.allowed_agents,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
    )


@router.get("/usage", response_model=UsageResponse)
async def get_tenant_usage(
    tenant: Tenant = Depends(get_current_tenant),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> UsageResponse:
    """Get current tenant usage statistics."""

    try:
        usage_data = await tenant_service.get_tenant_usage(str(tenant.id))
        return UsageResponse(**usage_data)

    except DomainException as e:
        logger.error("Failed to get tenant usage", error=str(e), tenant_id=str(tenant.id))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error getting tenant usage", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/regenerate-key")
async def regenerate_api_key(
    tenant: Tenant = Depends(get_current_tenant),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> dict:
    """Generate a new API key for the tenant."""

    try:
        new_api_key = await tenant_service.generate_new_api_key(str(tenant.id))

        logger.info("API key regenerated", tenant_id=str(tenant.id))

        return {
            "message": "API key regenerated successfully",
            "api_key": new_api_key,
        }

    except DomainException as e:
        logger.error("Failed to regenerate API key", error=str(e), tenant_id=str(tenant.id))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error regenerating API key", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
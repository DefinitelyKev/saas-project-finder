from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.api.v1.schemas import UsageResponse
from src.api.v1.dependencies import get_current_tenant, get_tenant_service
from src.domain.entities.tenant import Tenant
from src.services.tenant_service import TenantService
from src.domain.exceptions import DomainException

router = APIRouter()
logger = structlog.get_logger()


@router.get("", response_model=UsageResponse)
async def get_usage(
    tenant: Tenant = Depends(get_current_tenant),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> UsageResponse:
    """Get tenant usage statistics."""

    try:
        usage_data = await tenant_service.get_tenant_usage(str(tenant.id))
        return UsageResponse(**usage_data)

    except DomainException as e:
        logger.error("Failed to get usage", error=str(e), tenant_id=str(tenant.id))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error getting usage", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
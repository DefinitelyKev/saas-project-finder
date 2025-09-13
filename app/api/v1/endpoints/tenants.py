from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.container import Container, Provide
from app.services.tenant_service import TenantService
from app.domains.tenant.schemas import TenantCreate, TenantUpdate, TenantResponse
from app.core.exceptions import TenantNotFoundError, TenantAlreadyExistsError

router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
) -> TenantResponse:
    """Create a new tenant"""
    try:
        tenant = await tenant_service.create_tenant(tenant_data)
        return TenantResponse.model_validate(tenant)
    except TenantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
) -> TenantResponse:
    """Get tenant by ID"""
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return TenantResponse.model_validate(tenant)


@router.get("/slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
) -> TenantResponse:
    """Get tenant by slug"""
    tenant = await tenant_service.get_tenant_by_slug(slug)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return TenantResponse.model_validate(tenant)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
) -> TenantResponse:
    """Update tenant"""
    try:
        tenant = await tenant_service.update_tenant(tenant_id, tenant_data)
        return TenantResponse.model_validate(tenant)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
):
    """Delete tenant"""
    success = await tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
) -> List[TenantResponse]:
    """List tenants"""
    tenants = await tenant_service.list_tenants(skip=skip, limit=limit, active_only=active_only)
    return [TenantResponse.model_validate(tenant) for tenant in tenants]


@router.post("/{tenant_id}/activate", status_code=status.HTTP_200_OK)
async def activate_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
):
    """Activate tenant"""
    success = await tenant_service.activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return {"message": "Tenant activated successfully"}


@router.post("/{tenant_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(Provide[Container.tenant_service]),
):
    """Deactivate tenant"""
    success = await tenant_service.deactivate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return {"message": "Tenant deactivated successfully"}
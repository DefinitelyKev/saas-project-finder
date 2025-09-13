from typing import Dict, Any, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class RegisterTenantRequest(BaseModel):
    """Request schema for tenant registration."""

    name: str
    tier: str = "free"
    allowed_agents: List[str] = []


class CreateTenantRequest(BaseModel):
    """Request schema for creating a tenant."""

    name: str
    tier: str = "free"
    allowed_agents: List[str] = []


class TenantResponse(BaseModel):
    """Response schema for tenant details."""

    id: str
    name: str
    tier: str
    allowed_agents: List[str]
    is_active: bool
    created_at: datetime


class CreateTenantResponse(BaseModel):
    """Response schema for tenant creation."""

    tenant: TenantResponse
    api_key: str


class RegisterTenantResponse(BaseModel):
    """Response schema for tenant registration."""

    tenant_id: UUID
    api_key: str
    tier: str
    message: str


class ValidateKeyRequest(BaseModel):
    """Request schema for API key validation."""

    api_key: str


class ValidateKeyResponse(BaseModel):
    """Response schema for API key validation."""

    tenant_id: UUID
    tenant_name: str
    tier: str
    is_active: bool
    allowed_agents: List[str]
    monthly_tokens_used: int
    rate_limit_per_minute: int
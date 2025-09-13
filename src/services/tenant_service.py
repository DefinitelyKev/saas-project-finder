from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from src.domain.entities.tenant import Tenant
from src.domain.value_objects.api_key import ApiKey
from src.domain.exceptions import TenantNotFound, InvalidApiKey
from src.config.constants import TenantTier
from src.infrastructure.persistence.repositories.tenant_repository import TenantRepository

logger = structlog.get_logger()


class TenantService:
    """Service for managing tenants."""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def create_tenant(
        self,
        name: str,
        tier: TenantTier = TenantTier.FREE,
        allowed_agents: Optional[List[str]] = None,
    ) -> tuple[Tenant, str]:
        """Create a new tenant and return tenant with API key."""

        if allowed_agents is None:
            allowed_agents = []

        # Generate API key
        api_key = ApiKey.generate()
        api_key_hash = api_key.hash()

        # Create tenant
        tenant = Tenant(
            name=name,
            api_key_hash=api_key_hash,
            tier=tier,
            allowed_agents=allowed_agents,
        )

        # Save to repository
        await self.tenant_repository.create(tenant)

        logger.info("Tenant created",
                   tenant_id=str(tenant.id),
                   name=name,
                   tier=tier.value)

        return tenant, str(api_key)

    async def get_tenant_by_api_key(self, api_key: str) -> Tenant:
        """Get tenant by API key."""

        # Hash the provided API key
        api_key_hash = ApiKey.hash_key(api_key)

        # Find tenant
        tenant = await self.tenant_repository.get_by_api_key_hash(api_key_hash)
        if not tenant:
            raise TenantNotFound("Invalid API key")

        if not tenant.is_active:
            raise InvalidApiKey("Tenant account is inactive")

        return tenant

    async def update_tenant_usage(self, tenant_id: str, tokens_used: int) -> None:
        """Update tenant token usage."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        tenant.add_token_usage(tokens_used)
        await self.tenant_repository.update(tenant)

        logger.debug("Tenant usage updated",
                    tenant_id=tenant_id,
                    tokens_used=tokens_used,
                    total_usage=tenant.monthly_tokens_used)

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage statistics."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        return {
            "tenant_id": str(tenant.id),
            "name": tenant.name,
            "tier": tenant.tier.value,
            "current_month": tenant.current_month,
            "tokens_used": tenant.monthly_tokens_used,
            "token_limit": tenant.monthly_token_limit,
            "tokens_remaining": tenant.monthly_token_limit - tenant.monthly_tokens_used,
            "usage_percentage": (tenant.monthly_tokens_used / tenant.monthly_token_limit) * 100,
            "rate_limit_per_minute": tenant.rate_limit_per_minute,
            "max_sessions": tenant.max_sessions,
            "allowed_agents": tenant.allowed_agents,
        }

    async def update_tenant_tier(self, tenant_id: str, new_tier: TenantTier) -> Tenant:
        """Update tenant tier."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        old_tier = tenant.tier
        tenant.tier = new_tier

        await self.tenant_repository.update(tenant)

        logger.info("Tenant tier updated",
                   tenant_id=tenant_id,
                   old_tier=old_tier.value,
                   new_tier=new_tier.value)

        return tenant

    async def add_agent_access(self, tenant_id: str, agent_id: str) -> Tenant:
        """Add agent access to tenant."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        if agent_id not in tenant.allowed_agents:
            tenant.allowed_agents.append(agent_id)
            await self.tenant_repository.update(tenant)

            logger.info("Agent access added",
                       tenant_id=tenant_id,
                       agent_id=agent_id)

        return tenant

    async def remove_agent_access(self, tenant_id: str, agent_id: str) -> Tenant:
        """Remove agent access from tenant."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        if agent_id in tenant.allowed_agents:
            tenant.allowed_agents.remove(agent_id)
            await self.tenant_repository.update(tenant)

            logger.info("Agent access removed",
                       tenant_id=tenant_id,
                       agent_id=agent_id)

        return tenant

    async def generate_new_api_key(self, tenant_id: str) -> str:
        """Generate new API key for tenant."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        # Generate new API key
        api_key = ApiKey.generate()
        tenant.api_key_hash = api_key.hash()

        await self.tenant_repository.update(tenant)

        logger.info("New API key generated",
                   tenant_id=tenant_id)

        return str(api_key)

    async def deactivate_tenant(self, tenant_id: str) -> Tenant:
        """Deactivate tenant account."""

        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(f"Tenant not found: {tenant_id}")

        tenant.is_active = False
        await self.tenant_repository.update(tenant)

        logger.info("Tenant deactivated", tenant_id=tenant_id)

        return tenant
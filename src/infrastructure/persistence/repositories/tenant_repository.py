from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from src.domain.entities.tenant import Tenant
from src.domain.exceptions import TenantNotFound
from src.infrastructure.persistence.models import TenantModel
from src.config.constants import TenantTier


class TenantRepository:
    """Repository for tenant data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""

        tenant_model = TenantModel(
            id=tenant.id,
            name=tenant.name,
            api_key_hash=tenant.api_key_hash,
            tier=tenant.tier.value,
            allowed_agents=tenant.allowed_agents,
            monthly_tokens_used=tenant.monthly_tokens_used,
            current_month=tenant.current_month,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
        )

        self.session.add(tenant_model)

        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Tenant creation failed: {str(e)}")

        return tenant

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""

        stmt = select(TenantModel).where(TenantModel.id == UUID(tenant_id))
        result = await self.session.execute(stmt)
        tenant_model = result.scalar_one_or_none()

        if not tenant_model:
            return None

        return self._model_to_entity(tenant_model)

    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[Tenant]:
        """Get tenant by API key hash."""

        stmt = select(TenantModel).where(TenantModel.api_key_hash == api_key_hash)
        result = await self.session.execute(stmt)
        tenant_model = result.scalar_one_or_none()

        if not tenant_model:
            return None

        return self._model_to_entity(tenant_model)

    async def update(self, tenant: Tenant) -> Tenant:
        """Update existing tenant."""

        stmt = (
            update(TenantModel)
            .where(TenantModel.id == tenant.id)
            .values(
                name=tenant.name,
                api_key_hash=tenant.api_key_hash,
                tier=tenant.tier.value,
                allowed_agents=tenant.allowed_agents,
                monthly_tokens_used=tenant.monthly_tokens_used,
                current_month=tenant.current_month,
                is_active=tenant.is_active,
            )
        )

        result = await self.session.execute(stmt)

        if result.rowcount == 0:
            raise TenantNotFound(f"Tenant not found: {tenant.id}")

        await self.session.flush()
        return tenant

    async def list_tenants(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with pagination."""

        stmt = select(TenantModel)

        if active_only:
            stmt = stmt.where(TenantModel.is_active == True)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        tenant_models = result.scalars().all()

        return [self._model_to_entity(model) for model in tenant_models]

    async def count_tenants(self, active_only: bool = True) -> int:
        """Count total tenants."""

        from sqlalchemy import func

        stmt = select(func.count(TenantModel.id))

        if active_only:
            stmt = stmt.where(TenantModel.is_active == True)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete by setting inactive)."""

        stmt = (
            update(TenantModel)
            .where(TenantModel.id == UUID(tenant_id))
            .values(is_active=False)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0

    def _model_to_entity(self, model: TenantModel) -> Tenant:
        """Convert database model to domain entity."""

        return Tenant(
            id=model.id,
            name=model.name,
            api_key_hash=model.api_key_hash,
            tier=TenantTier(model.tier),
            allowed_agents=model.allowed_agents or [],
            monthly_tokens_used=model.monthly_tokens_used,
            current_month=model.current_month,
            is_active=model.is_active,
            created_at=model.created_at,
        )
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.domains.tenant.models import Tenant
from app.domains.tenant.schemas import TenantCreate, TenantUpdate
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.cache.redis_client import RedisClient
from app.core.exceptions import TenantNotFoundError, TenantAlreadyExistsError

logger = structlog.get_logger(__name__)


class TenantService:
    def __init__(self, database_manager: DatabaseManager, redis_client: RedisClient):
        self.db_manager = database_manager
        self.redis_client = redis_client
        self._cache_prefix = "tenant:"
        self._cache_ttl = 3600  # 1 hour
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant"""
        async with self.db_manager.get_session() as session:
            # Check if tenant already exists
            existing = await self._get_tenant_by_slug(session, tenant_data.slug)
            if existing:
                raise TenantAlreadyExistsError(f"Tenant with slug '{tenant_data.slug}' already exists")
            
            # Create tenant
            tenant = Tenant(**tenant_data.model_dump())
            session.add(tenant)
            await session.flush()  # Get the ID
            
            logger.info("Created tenant", tenant_id=tenant.id, slug=tenant.slug)
            
            # Create tenant-specific database schema
            await self.db_manager.create_tenant_schema(tenant.id)
            
            # Cache tenant
            await self._cache_tenant(tenant)
            
            return tenant
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        # Try cache first
        cached_tenant = await self._get_cached_tenant(tenant_id)
        if cached_tenant:
            return cached_tenant
        
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.id == tenant_id,
                    Tenant.is_deleted.is_(False)
                )
            )
            tenant = result.scalar_one_or_none()
            
            if tenant:
                await self._cache_tenant(tenant)
            
            return tenant
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        async with self.db_manager.get_session() as session:
            return await self._get_tenant_by_slug(session, slug)
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.domain == domain,
                    Tenant.is_deleted.is_(False),
                    Tenant.is_active.is_(True)
                )
            )
            return result.scalar_one_or_none()
    
    async def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Tenant:
        """Update tenant"""
        async with self.db_manager.get_session() as session:
            tenant = await self._get_tenant_by_id(session, tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant with ID '{tenant_id}' not found")
            
            # Update fields
            update_data = tenant_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(tenant, field, value)
            
            await session.flush()
            
            logger.info("Updated tenant", tenant_id=tenant_id)
            
            # Update cache
            await self._cache_tenant(tenant)
            
            return tenant
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Soft delete tenant"""
        async with self.db_manager.get_session() as session:
            tenant = await self._get_tenant_by_id(session, tenant_id)
            if not tenant:
                return False
            
            # Soft delete
            tenant.is_deleted = True
            tenant.is_active = False
            await session.flush()
            
            logger.info("Deleted tenant", tenant_id=tenant_id)
            
            # Remove from cache
            await self._remove_tenant_from_cache(tenant_id)
            
            # Drop tenant schema (optional - you might want to keep data)
            # await self.db_manager.drop_tenant_schema(tenant_id)
            
            return True
    
    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Tenant]:
        """List tenants"""
        async with self.db_manager.get_session() as session:
            query = select(Tenant).where(Tenant.is_deleted.is_(False))
            
            if active_only:
                query = query.where(Tenant.is_active.is_(True))
            
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """Activate tenant"""
        return await self._update_tenant_status(tenant_id, is_active=True)
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate tenant"""
        return await self._update_tenant_status(tenant_id, is_active=False)
    
    async def verify_tenant(self, tenant_id: str) -> bool:
        """Verify tenant"""
        return await self._update_tenant_status(tenant_id, is_verified=True)
    
    async def update_tenant_plan(self, tenant_id: str, plan_type: str, features: Dict[str, Any]) -> bool:
        """Update tenant plan and features"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id, Tenant.is_deleted.is_(False))
                .values(plan_type=plan_type, features=features)
            )
            
            if result.rowcount == 0:
                return False
            
            logger.info("Updated tenant plan", tenant_id=tenant_id, plan_type=plan_type)
            
            # Invalidate cache
            await self._remove_tenant_from_cache(tenant_id)
            
            return True
    
    # Helper methods
    async def _get_tenant_by_id(self, session: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID from database"""
        result = await session.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.is_deleted.is_(False)
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_tenant_by_slug(self, session: AsyncSession, slug: str) -> Optional[Tenant]:
        """Get tenant by slug from database"""
        result = await session.execute(
            select(Tenant).where(
                Tenant.slug == slug,
                Tenant.is_deleted.is_(False)
            )
        )
        return result.scalar_one_or_none()
    
    async def _update_tenant_status(self, tenant_id: str, **status_fields) -> bool:
        """Update tenant status fields"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id, Tenant.is_deleted.is_(False))
                .values(**status_fields)
            )
            
            if result.rowcount > 0:
                await self._remove_tenant_from_cache(tenant_id)
                return True
            return False
    
    # Cache methods
    async def _cache_tenant(self, tenant: Tenant) -> None:
        """Cache tenant data"""
        cache_key = f"{self._cache_prefix}{tenant.id}"
        tenant_data = tenant.to_dict()
        await self.redis_client.set(
            cache_key, 
            tenant_data, 
            expire=self._cache_ttl
        )
    
    async def _get_cached_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant from cache"""
        cache_key = f"{self._cache_prefix}{tenant_id}"
        tenant_data = await self.redis_client.get(cache_key)
        
        if tenant_data:
            return Tenant(**tenant_data)
        return None
    
    async def _remove_tenant_from_cache(self, tenant_id: str) -> None:
        """Remove tenant from cache"""
        cache_key = f"{self._cache_prefix}{tenant_id}"
        await self.redis_client.delete(cache_key)
from typing import AsyncGenerator, Dict, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.infrastructure.database.base import Base


class DatabaseManager:
    def __init__(
        self, 
        database_url: str, 
        pool_size: int = 10, 
        pool_overflow: int = 20
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.pool_overflow = pool_overflow
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_makers: Dict[str, async_sessionmaker] = {}
        self._main_engine: Optional[AsyncEngine] = None
    
    async def initialize(self) -> None:
        """Initialize the main database engine"""
        self._main_engine = create_async_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.pool_overflow,
            echo=settings.LOG_LEVEL == "DEBUG",
        )
        
        # Create main session maker
        self._session_makers["main"] = async_sessionmaker(
            self._main_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def close(self) -> None:
        """Close all database connections"""
        if self._main_engine:
            await self._main_engine.dispose()
        
        for engine in self._engines.values():
            await engine.dispose()
        
        self._engines.clear()
        self._session_makers.clear()
    
    def get_tenant_engine(self, tenant_id: str) -> AsyncEngine:
        """Get or create tenant-specific database engine"""
        if tenant_id not in self._engines:
            # For database-per-tenant, you would construct tenant-specific URL here
            # For now, using schema-per-tenant approach with search_path
            tenant_url = f"{self.database_url}?options=-csearch_path={tenant_id}"
            
            self._engines[tenant_id] = create_async_engine(
                tenant_url,
                pool_size=max(2, self.pool_size // 10),  # Smaller pools for tenants
                max_overflow=max(5, self.pool_overflow // 10),
                echo=settings.LOG_LEVEL == "DEBUG",
            )
            
            self._session_makers[tenant_id] = async_sessionmaker(
                self._engines[tenant_id],
                class_=AsyncSession,
                expire_on_commit=False,
            )
        
        return self._engines[tenant_id]
    
    @asynccontextmanager
    async def get_session(self, tenant_id: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        session_key = tenant_id if tenant_id else "main"
        
        if tenant_id and tenant_id not in self._session_makers:
            self.get_tenant_engine(tenant_id)
        
        session_maker = self._session_makers[session_key]
        
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tenant_schema(self, tenant_id: str) -> None:
        """Create tenant-specific database schema"""
        async with self.get_session() as session:
            # Create schema
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant_id}"))
            await session.commit()
        
        # Create tables in tenant schema
        tenant_engine = self.get_tenant_engine(tenant_id)
        async with tenant_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tenant_schema(self, tenant_id: str) -> None:
        """Drop tenant-specific database schema"""
        async with self.get_session() as session:
            await session.execute(text(f"DROP SCHEMA IF EXISTS {tenant_id} CASCADE"))
            await session.commit()
        
        # Remove from cache
        if tenant_id in self._engines:
            await self._engines[tenant_id].dispose()
            del self._engines[tenant_id]
            del self._session_makers[tenant_id]
    
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
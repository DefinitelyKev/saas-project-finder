from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config.settings import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def create_database_engine():
    """Create database engine with production-ready configuration."""

    # Base engine configuration
    engine_config = {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
        "pool_recycle": settings.database_pool_recycle,
        "pool_pre_ping": settings.database_pool_pre_ping,
        "echo": settings.database_echo,
        "echo_pool": settings.debug,
        "future": True,
    }

    # Environment-specific configurations
    if settings.is_production():
        engine_config.update({
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "echo": False,
            "echo_pool": False,
        })
    elif settings.is_staging():
        engine_config.update({
            "pool_size": 10,
            "max_overflow": 15,
            "pool_timeout": 20,
            "pool_recycle": 1800,
        })
    else:  # development
        engine_config.update({
            "pool_size": 5,
            "max_overflow": 5,
            "pool_timeout": 10,
            "pool_recycle": -1,  # Disable pool recycling in dev
        })

    logger.info(f"Creating database engine for {settings.environment} environment")
    logger.info(f"Database pool configuration: {engine_config}")

    return create_async_engine(settings.database_url, **engine_config)


# Create async engine with production configuration
engine = create_database_engine()

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Better control over when to flush
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, OSError)),
)
async def create_session_with_retry() -> AsyncSession:
    """Create database session with retry logic."""
    try:
        return AsyncSessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager with production-ready error handling."""
    session = None
    start_time = time.time()

    try:
        session = await create_session_with_retry()
        logger.debug("Database session created successfully")

        yield session

        # Commit transaction
        await session.commit()
        logger.debug(f"Database transaction committed successfully in {time.time() - start_time:.3f}s")

    except Exception as e:
        if session:
            try:
                await session.rollback()
                logger.warning(f"Database transaction rolled back due to error: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")

        logger.error(f"Database session error after {time.time() - start_time:.3f}s: {e}")
        raise

    finally:
        if session:
            try:
                await session.close()
                logger.debug("Database session closed successfully")
            except Exception as close_error:
                logger.error(f"Failed to close database session: {close_error}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with get_db_session() as session:
        yield session


@retry(
    stop=stop_after_attempt(settings.database_retry_attempts),
    wait=wait_exponential(multiplier=settings.database_retry_delay, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, OSError)),
)
async def health_check() -> bool:
    """Health check for database connectivity."""
    try:
        async with get_db_session() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_database_info() -> dict:
    """Get database connection information for monitoring."""
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the async session factory."""
    return AsyncSessionLocal


async def close_database_connections():
    """Gracefully close all database connections."""
    logger.info("Closing database connections...")
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
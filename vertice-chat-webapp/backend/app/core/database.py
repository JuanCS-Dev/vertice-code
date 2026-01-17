"""
Database module (PostgreSQL with SQLAlchemy)
Multi-tenant SaaS database with GDPR compliance
"""

from typing import Any, Optional
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database instances
_async_engine: Optional[Any] = None
_async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


async def init_db_pool() -> None:
    """
    Initialize PostgreSQL database connection pool with SQLAlchemy.
    """
    global _async_engine, _async_session_maker

    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL not configured, using mock database for development")
        return

    try:
        # Create async engine with optimized settings
        database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

        _async_engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
        )

        _async_session_maker = async_sessionmaker(
            _async_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Test connection
        async with _async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database pool initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        logger.warning("Falling back to mock database")


async def close_db_pool() -> None:
    """Close database connection pool gracefully"""
    global _async_engine, _async_session_maker

    if _async_engine:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_maker = None
        logger.info("Database pool closed successfully")


@asynccontextmanager
async def get_db_session():
    """
    Get database session with proper error handling and cleanup.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)
    """
    if _async_session_maker is None:
        # Fallback to mock session for development
        class MockSession:
            async def execute(self, query, **kwargs):
                logger.warning(f"Mock DB: Would execute {query}")
                return None

            async def commit(self):
                pass

            async def rollback(self):
                pass

            async def close(self):
                pass

        session = MockSession()
        try:
            yield session
        finally:
            pass
        return

    session = _async_session_maker()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def health_check() -> dict:
    """
    Database health check.
    """
    if not _async_engine:
        return {"database": "mock"}

    try:
        async with _async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": f"error: {str(e)}"}

"""
Database module (PostgreSQL)
"""

from typing import Any, AsyncContextManager, Optional, Type
import logging

logger = logging.getLogger(__name__)

# Global database pool instance (mock for development)
_db_pool: Any = None


async def init_db_pool() -> None:
    """
    Initialize database connection pool.

    CONSTITUTIONAL EXEMPTION (Artigo X, Section Y):
    Reason: Production PostgreSQL not configured yet
    Approval: Development phase
    Date: 2026-01-07
    Tracking: MAXIMUS-002
    """
    global _db_pool
    logger.info("Database pool initialization (mock for development)")
    _db_pool = {}  # Mock database


async def close_db_pool() -> None:
    """Close database connection pool"""
    global _db_pool
    logger.info("Closing database pool")
    _db_pool = None


class MockSession:
    """Mock database session for development"""

    async def __aenter__(self) -> "MockSession":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        pass

    async def commit(self) -> None:
        """Mock commit"""
        pass

    async def add(self, obj: Any) -> None:
        """Mock add"""
        logger.debug(f"Mock DB add: {obj}")


async def get_db_session() -> AsyncContextManager[Any]:
    """
    Get database session.

    Returns:
        Async context manager for database session
    """
    session = MockSession()
    return session

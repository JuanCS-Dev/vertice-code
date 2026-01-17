"""
Cache module (Firestore)
"""

from typing import Optional
import logging
from app.integrations.firestore_cache import FirestoreCache

logger = logging.getLogger(__name__)

# Global Firestore client instance
_firestore_cache: Optional[FirestoreCache] = None


async def init_cache_pool() -> None:
    """Initialize Firestore cache connection."""
    global _firestore_cache
    logger.info("Initializing Firestore cache...")
    _firestore_cache = FirestoreCache()


async def close_cache_pool() -> None:
    """Close Firestore cache connection."""
    global _firestore_cache
    if _firestore_cache:
        await _firestore_cache.close()
        _firestore_cache = None
    logger.info("Firestore cache closed")


async def get_cached_prompt(key: str) -> Optional[str]:
    """Get cached prompt from Firestore."""
    if not _firestore_cache:
        logger.warning("Firestore cache not initialized")
        return None
    return await _firestore_cache.get(key)


async def set_cached_prompt(key: str, value: str) -> None:
    """Set cached prompt in Firestore."""
    if not _firestore_cache:
        logger.warning("Firestore cache not initialized")
        return
    await _firestore_cache.set(key, value)


async def get_cache() -> FirestoreCache:
    """Get Firestore cache instance."""
    if not _firestore_cache:
        await init_cache_pool()
    return _firestore_cache or FirestoreCache()


# Compatibility stub for modules expecting Redis
def get_redis():
    """
    Compatibility stub - returns None.
    This project uses Firestore, not Redis.
    Callers should handle None gracefully.
    """
    logger.warning("get_redis called but Redis not configured (using Firestore)")
    return None

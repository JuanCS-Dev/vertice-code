"""
Rate limiting implementation using Redis
Provides distributed rate limiting for API endpoints

Reference: https://redis.io/commands/INCR
"""

import time
from typing import Optional
from fastapi import Request, HTTPException
import redis.asyncio as redis

from app.core.config import settings


class RateLimiter:
    """Distributed rate limiter using Redis"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is allowed under rate limit

        Args:
            key: Unique identifier (e.g., "user:123:api")
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        current_time = int(time.time())

        # Use Redis sorted set to track requests
        # Key format: rate_limit:{key}
        redis_key = f"rate_limit:{key}"

        # Remove old entries outside the window
        min_time = current_time - window_seconds
        await self.redis.zremrangebyscore(redis_key, 0, min_time)

        # Count current requests in window
        count = await self.redis.zcard(redis_key)

        if count >= limit:
            return False

        # Add current request
        await self.redis.zadd(redis_key, {str(current_time): current_time})

        # Set expiry on the key (window + buffer)
        await self.redis.expire(redis_key, window_seconds * 2)

        return True

    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        """Get remaining requests allowed in current window"""
        current_time = int(time.time())
        redis_key = f"rate_limit:{key}"

        # Remove old entries
        min_time = current_time - window_seconds
        await self.redis.zremrangebyscore(redis_key, 0, min_time)

        # Count current requests
        count = await self.redis.zcard(redis_key)

        return max(0, limit - count)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        # Initialize Redis connection
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL or "redis://localhost:6379",
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


async def check_rate_limit(
    request: Request, user_id: Optional[str] = None, endpoint: str = "api"
) -> None:
    """
    Check rate limit for request

    Raises HTTPException if rate limited
    """
    # Get client identifier (user or IP)
    client_id = user_id or (request.client.host if request.client else "anonymous")

    # Create rate limit key
    key = f"{client_id}:{endpoint}"

    # Get rate limiter
    limiter = await get_rate_limiter()

    # Check if allowed
    allowed = await limiter.is_allowed(
        key=key,
        limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        window_seconds=60,  # 1 minute window
    )

    if not allowed:
        # Get remaining time until reset
        remaining = await limiter.get_remaining(key, settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": 60,  # seconds
                "remaining": remaining,
            },
        )

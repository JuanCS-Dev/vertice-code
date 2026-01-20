"""
Tool Caching Utilities.

Provides decorators and mixins for caching tool results.
"""

import functools
import time
from typing import Dict, Any, Tuple

# Async lock for thread/task safety
from asyncio import Lock


def _make_hashable(value: Any) -> Any:
    """Make value hashable for cache key."""
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_make_hashable(v) for v in value)
    return value


def cache_tool_result(ttl_seconds: float = 60.0):
    """
    Decorator to cache tool results for a specified duration.

    Usage:
        @cache_tool_result(ttl_seconds=300)
        async def _execute_validated(self, **kwargs):
            ...
    """

    def decorator(func):
        cache: Dict[Tuple, Tuple[float, Any]] = {}
        lock = Lock()

        @functools.wraps(func)
        async def wrapper(self, **kwargs):
            # Create a stable cache key from kwargs
            # We filter out 'indexer' or other non-serializable objects if needed,
            # but usually tool args are JSON-serializable.

            # Simple approach: sorted tuple of items
            try:
                key = _make_hashable(kwargs)
            except TypeError:
                # If args are not hashable, skip caching
                return await func(self, **kwargs)

            async with lock:
                now = time.time()
                if key in cache:
                    ts, result = cache[key]
                    if now - ts < ttl_seconds:
                        # If result is a ToolResult, add metadata
                        if hasattr(result, "metadata") and isinstance(result.metadata, dict):
                            result.metadata["cached"] = True
                            result.metadata["cache_age"] = round(now - ts, 2)
                        return result
                    else:
                        del cache[key]

            # Execute
            result = await func(self, **kwargs)

            # Cache if successful
            should_cache = True
            if hasattr(result, "success") and not result.success:
                should_cache = False

            if should_cache:
                async with lock:
                    cache[key] = (time.time(), result)

            return result

        # Add method to clear cache
        def invalidate_cache():
            cache.clear()

        wrapper.invalidate_cache = invalidate_cache
        return wrapper

    return decorator

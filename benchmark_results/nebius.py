```python
import asyncio
from collections import OrderedDict
import time
from typing import Any, Callable, Optional, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class AsyncLRUCache:
    def __init__(
        self,
        maxsize: int,
        on_evict: Optional[Callable[[K, V], Any]] = None
    ):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self.maxsize = maxsize
        self._on_evict = on_evict
        self._cache: OrderedDict[K, tuple[V, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: K) -> Optional[V]:
        async with self._lock:
            if key not in self._cache:
                return None
            value, expiry = self._cache[key]
            if expiry is not None and time.monotonic() > expiry:
                await self._remove_item(key)
                return None
            self._cache.move_to_end(key)
            return value

    async def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        async with self._lock:
            expiry = time.monotonic() + ttl if ttl is not None else None
            if key in self._cache:
                await self._remove_item(key)
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
            await self._evict_if_needed()

    async def size(self) -> int:
        async with self._lock:
            return len(self._cache)

    async def clear(self) -> None:
        async with self._lock:
            if self._on_evict:
                for key in list(self._cache.keys()):
                    await self._remove_item(key)
            self._cache.clear()

    async def _evict_if_needed(self) -> None:
        while len(self._cache) > self.maxsize:
            key, (value, _) = self._cache.popitem(last=False)
            if self._on_evict:
                await self._on_evict(key, value)

    async def _remove_item(self, key: K) -> None:
        value, _ = self._cache.pop(key)
        if self._on_evict:
            await self._on_evict(key, value)
```
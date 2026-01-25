from __future__ import annotations

import dataclasses
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


@dataclasses.dataclass(frozen=True, slots=True)
class AlloyDBConfig:
    """Minimal async SQLAlchemy config for AlloyDB/PG (pool-managed)."""

    dsn: str  # e.g. "postgresql+asyncpg://user:pass@host:5432/db"  # pragma: allowlist secret
    pool_size: int = 5


class AlloyDBConnector:
    def __init__(self, config: AlloyDBConfig) -> None:
        self._config = config
        self._engine: Optional[AsyncEngine] = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("AlloyDBConnector not started. Call `await start()` first.")
        return self._engine

    async def start(self) -> None:
        if self._engine is not None:
            return
        cfg = self._config
        self._engine = create_async_engine(
            cfg.dsn,
            pool_size=cfg.pool_size,
            max_overflow=0,
            pool_pre_ping=True,
        )

    async def close(self) -> None:
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        async with self.engine.connect() as conn:
            yield conn

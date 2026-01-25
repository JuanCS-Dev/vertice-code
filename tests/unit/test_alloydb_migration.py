from __future__ import annotations

from contextlib import asynccontextmanager
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

import pytest

import vertice_core.memory.alloydb_connector as alloydb_mod
from vertice_core.memory.alloydb_connector import AlloyDBConfig, AlloyDBConnector
from vertice_core.memory.cortex.connection_pool import get_connection_pool
from vertice_core.memory.cortex.episodic import EpisodicBackendConfig, EpisodicMemory
from vertice_core.memory.cortex.semantic import SemanticBackendConfig, SemanticMemory
from tools.migrate_memory import migrate_memories, read_prometheus_memories


@pytest.mark.asyncio
async def test_alloydb_connector_manages_engine_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    created: List[Dict[str, Any]] = []

    class FakeEngine:
        def __init__(self) -> None:
            self.disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    def fake_create_async_engine(url: str, **kwargs: Any) -> FakeEngine:
        created.append({"url": url, "kwargs": kwargs})
        return FakeEngine()

    monkeypatch.setattr(alloydb_mod, "create_async_engine", fake_create_async_engine)

    connector = AlloyDBConnector(
        AlloyDBConfig(
            dsn="postgresql+asyncpg://user:pass@localhost:5432/db",  # pragma: allowlist secret
            pool_size=3,
        )
    )

    await connector.start()
    await connector.start()  # idempotent

    assert len(created) == 1
    assert created[0]["url"].startswith("postgresql+asyncpg://")
    assert created[0]["kwargs"]["pool_size"] == 3

    engine = connector.engine
    await connector.close()
    assert engine.disposed is True


def test_episodic_memory_accepts_alloydb_backend_via_config() -> None:
    executed_sql: List[str] = []

    class FakeConn:
        async def execute(self, stmt: Any, params: Optional[Dict[str, Any]] = None) -> Any:
            sql = getattr(stmt, "text", None) or str(stmt)
            executed_sql.append(sql)

            class _FakeResult:
                rowcount = 0

                def fetchall(self) -> list[Any]:
                    return []

                def fetchone(self) -> Any:
                    return None

            return _FakeResult()

    class _AsyncCM:
        async def __aenter__(self) -> FakeConn:
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class FakeEngine:
        def begin(self) -> _AsyncCM:
            return _AsyncCM()

        def connect(self) -> _AsyncCM:
            return _AsyncCM()

    class FakeAlloyDBConnector:
        def __init__(self) -> None:
            self.engine = FakeEngine()

        async def start(self) -> None:
            return None

        async def close(self) -> None:
            return None

        @asynccontextmanager
        async def connect(self):  # type: ignore[override]
            yield FakeConn()

    config = EpisodicBackendConfig(
        backend="alloydb",
        alloydb_dsn="postgresql+asyncpg://user:pass@localhost:5432/db",
    )
    EpisodicMemory(
        Path("ignored.db"), get_connection_pool(), config=config, alloydb=FakeAlloyDBConnector()
    )

    assert any("CREATE TABLE IF NOT EXISTS episodes" in sql for sql in executed_sql)


def test_semantic_memory_accepts_alloydb_backend_via_config() -> None:
    executed: List[Dict[str, Any]] = []

    class FakeConn:
        async def execute(self, stmt: Any, params: Optional[Dict[str, Any]] = None) -> Any:
            sql = getattr(stmt, "text", None) or str(stmt)
            executed.append({"sql": sql, "params": params or {}})

            class _FakeResult:
                def fetchall(self) -> list[Any]:
                    return []

            return _FakeResult()

    class _AsyncCM:
        async def __aenter__(self) -> FakeConn:
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class FakeEngine:
        def begin(self) -> _AsyncCM:
            return _AsyncCM()

        def connect(self) -> _AsyncCM:
            return _AsyncCM()

    class FakeAlloyDBConnector:
        def __init__(self) -> None:
            self.engine = FakeEngine()

        async def start(self) -> None:
            return None

        async def close(self) -> None:
            return None

        @asynccontextmanager
        async def connect(self):  # type: ignore[override]
            yield FakeConn()

    config = SemanticBackendConfig(
        backend="alloydb",
        alloydb_dsn="postgresql+asyncpg://user:pass@localhost:5432/db",
    )
    mem = SemanticMemory(Path("ignored"), config=config, alloydb=FakeAlloyDBConnector())
    mem.store(content="hello", category="general", metadata={"k": "v"})

    sqls = [e["sql"] for e in executed]
    assert any("CREATE EXTENSION IF NOT EXISTS google_ml_integration" in s for s in sqls)
    assert any("CREATE TABLE IF NOT EXISTS semantic_memories" in s for s in sqls)
    assert any("INSERT INTO semantic_memories" in s and "embedding(" in s for s in sqls)


@pytest.mark.asyncio
async def test_tools_migrate_memory_moves_sqlite_rows_to_alloydb(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "prometheus.db"
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            CREATE TABLE memories (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              content TEXT NOT NULL,
              metadata TEXT,
              importance FLOAT DEFAULT 0.5,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO memories (id, type, content, metadata) VALUES (?, ?, ?, ?)",
            ("1", "episodic", "ep-content", json.dumps({"session_id": "s1", "event_type": "evt"})),
        )
        conn.execute(
            "INSERT INTO memories (id, type, content, metadata) VALUES (?, ?, ?, ?)",
            ("2", "semantic", "sem-content", json.dumps({"category": "facts"})),
        )

    executed: List[Dict[str, Any]] = []

    class FakeConn:
        async def execute(self, stmt: Any, params: Optional[Dict[str, Any]] = None) -> Any:
            sql = getattr(stmt, "text", None) or str(stmt)
            executed.append({"sql": sql, "params": params or {}})

            class _FakeResult:
                def fetchall(self) -> list[Any]:
                    return []

            return _FakeResult()

    class _AsyncCM:
        async def __aenter__(self) -> FakeConn:
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class FakeEngine:
        def begin(self) -> _AsyncCM:
            return _AsyncCM()

    class FakeAlloyDBConnector:
        def __init__(self) -> None:
            self.engine = FakeEngine()

        async def start(self) -> None:
            return None

    memories = read_prometheus_memories(sqlite_path)
    counts = await migrate_memories(
        FakeAlloyDBConnector(),  # type: ignore[arg-type]
        memories=memories,
        embedding_model="text-embedding-005",
        types=("episodic", "semantic"),
        dry_run=False,
    )

    assert counts["episodic"] == 1
    assert counts["semantic"] == 1
    assert any("INSERT INTO episodes" in e["sql"] for e in executed)
    assert any(
        "INSERT INTO semantic_memories" in e["sql"] and "embedding(" in e["sql"] for e in executed
    )

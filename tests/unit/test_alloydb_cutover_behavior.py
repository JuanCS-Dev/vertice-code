from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from vertice_core.memory.cortex.cortex import MemoryCortex
from vertice_core.memory.cortex.connection_pool import get_connection_pool
from vertice_core.memory.cortex.episodic import EpisodicBackendConfig, EpisodicMemory
from vertice_core.memory.cortex.semantic import SemanticBackendConfig, SemanticMemory
from tools.migrate_memory import ensure_alloydb_schema, migrate_memories


class _FakeResult:
    def fetchall(self) -> list[Any]:
        return []


class _FakeConn:
    def __init__(self, executed: List[tuple[str, Optional[Dict[str, Any]]]]) -> None:
        self._executed = executed

    async def execute(self, stmt: Any, params: Optional[Dict[str, Any]] = None) -> _FakeResult:
        sql = getattr(stmt, "text", None) or str(stmt)
        self._executed.append((str(sql), params))
        return _FakeResult()


class _AsyncCM:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeEngine:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def begin(self) -> _AsyncCM:
        return _AsyncCM(self._conn)


class _FakeAlloyDBConnector:
    def __init__(self, executed: List[tuple[str, Optional[Dict[str, Any]]]]) -> None:
        self._executed = executed
        self._conn = _FakeConn(executed)
        self.engine = _FakeEngine(self._conn)
        self.start_calls = 0

    async def start(self) -> None:
        self.start_calls += 1

    def connect(self) -> _AsyncCM:
        return _AsyncCM(self._conn)


def test_semantic_memory_falls_back_to_sqlite_without_dsn(tmp_path: Path) -> None:
    mem = SemanticMemory(tmp_path / "semantic", config=SemanticBackendConfig(alloydb_dsn=None))

    assert mem.is_vector_enabled is False
    entry_id = mem.store(content="hello", category="general", metadata={"k": "v"})
    assert isinstance(entry_id, str) and entry_id

    fallback_db = tmp_path / "semantic" / "semantic_fallback.db"
    assert fallback_db.exists()
    with sqlite3.connect(fallback_db) as conn:
        row = conn.execute("SELECT COUNT(*) FROM semantic_fts").fetchone()
        assert row is not None and int(row[0]) == 1


def test_episodic_memory_falls_back_to_sqlite_without_dsn(tmp_path: Path) -> None:
    pool = get_connection_pool()
    mem = EpisodicMemory(
        tmp_path / "episodic.db",
        pool,
        config=EpisodicBackendConfig(alloydb_dsn=None),
    )

    episode_id = mem.record(event_type="evt", content="c", session_id="s1", metadata={"x": 1})
    assert isinstance(episode_id, str) and episode_id

    with sqlite3.connect(tmp_path / "episodic.db") as conn:
        row = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
        assert row is not None and int(row[0]) == 1


def test_memorycortex_defaults_to_local_sqlite_when_no_dsn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VERTICE_ALLOYDB_DSN", raising=False)
    monkeypatch.delenv("ALLOYDB_DSN", raising=False)

    cortex = MemoryCortex(base_path=tmp_path)
    assert cortex.episodic._backend_effective == "sqlite"  # type: ignore[attr-defined]
    assert cortex.semantic.is_vector_enabled is False


def test_memorycortex_prefers_vertice_alloydb_dsn_over_alloydb_dsn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERTICE_ALLOYDB_DSN", "postgresql+asyncpg://vertice")
    monkeypatch.setenv("ALLOYDB_DSN", "postgresql+asyncpg://legacy")

    cortex = MemoryCortex(base_path=tmp_path)
    assert cortex._alloydb_dsn == "postgresql+asyncpg://vertice"  # noqa: SLF001


def test_semantic_memory_alloydb_store_uses_in_db_embedding_function(tmp_path: Path) -> None:
    executed: List[tuple[str, Optional[Dict[str, Any]]]] = []
    fake = _FakeAlloyDBConnector(executed)
    mem = SemanticMemory(
        tmp_path / "semantic",
        config=SemanticBackendConfig(
            alloydb_dsn="postgresql+asyncpg://x", embedding_model="text-embedding-005"
        ),
        alloydb=fake,  # type: ignore[arg-type]
    )

    mem.store(content="hello", category="general")

    inserts = [
        (sql, params) for (sql, params) in executed if "INSERT INTO semantic_memories" in sql
    ]
    assert len(inserts) == 1
    sql, params = inserts[0]
    assert "embedding(:model, :content)" in sql
    assert params is not None and params.get("model") == "text-embedding-005"


@pytest.mark.asyncio
async def test_semantic_memory_alloydb_search_uses_in_db_embedding_function(tmp_path: Path) -> None:
    executed: List[tuple[str, Optional[Dict[str, Any]]]] = []
    fake = _FakeAlloyDBConnector(executed)
    mem = SemanticMemory(
        tmp_path / "semantic",
        config=SemanticBackendConfig(
            alloydb_dsn="postgresql+asyncpg://x", embedding_model="text-embedding-005"
        ),
        alloydb=fake,  # type: ignore[arg-type]
    )

    await mem.search("q", limit=3)

    selects = [(sql, params) for (sql, params) in executed if "FROM semantic_memories" in sql]
    assert len(selects) == 1
    sql, params = selects[0]
    assert "embedding(:model, :query)" in sql
    assert params is not None and params.get("model") == "text-embedding-005"
    assert params.get("query") == "q"


@pytest.mark.asyncio
async def test_migrate_memories_dry_run_does_not_execute_sql(tmp_path: Path) -> None:
    memories = [
        {
            "id": "1",
            "type": "episodic",
            "content": "ep",
            "metadata": json.dumps({"session_id": "s"}),
        },
        {
            "id": "2",
            "type": "semantic",
            "content": "sem",
            "metadata": json.dumps({"category": "facts"}),
        },
    ]

    executed: List[str] = []

    class FakeConn:
        async def execute(self, stmt: Any, params: Optional[Dict[str, Any]] = None) -> Any:
            sql = getattr(stmt, "text", None) or str(stmt)
            executed.append(sql)

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

    counts = await migrate_memories(
        FakeAlloyDBConnector(),  # type: ignore[arg-type]
        memories=memories,
        embedding_model="text-embedding-005",
        types=("episodic", "semantic"),
        dry_run=True,
    )

    assert counts["episodic"] == 1
    assert counts["semantic"] == 1
    assert executed == []


@pytest.mark.asyncio
async def test_migrate_memories_honors_types_filter(tmp_path: Path) -> None:
    memories = [
        {
            "id": "1",
            "type": "episodic",
            "content": "ep",
            "metadata": json.dumps({"session_id": "s"}),
        },
        {
            "id": "2",
            "type": "semantic",
            "content": "sem",
            "metadata": json.dumps({"category": "facts"}),
        },
    ]

    executed: List[tuple[str, Optional[Dict[str, Any]]]] = []
    fake = _FakeAlloyDBConnector(executed)

    counts = await migrate_memories(
        fake,  # type: ignore[arg-type]
        memories=memories,
        embedding_model="text-embedding-005",
        types=("semantic",),
        dry_run=True,
    )

    assert counts["episodic"] == 0
    assert counts["semantic"] == 1
    assert counts["skipped"] == 1
    assert executed == []


def test_episodic_memory_alloydb_record_executes_insert(tmp_path: Path) -> None:
    executed: List[tuple[str, Optional[Dict[str, Any]]]] = []
    fake = _FakeAlloyDBConnector(executed)
    pool = get_connection_pool()
    mem = EpisodicMemory(
        tmp_path / "episodic.db",
        pool,
        config=EpisodicBackendConfig(alloydb_dsn="postgresql+asyncpg://x"),
        alloydb=fake,  # type: ignore[arg-type]
    )

    episode_id = mem.record(event_type="evt", content="c", session_id="s1", metadata={"x": 1})
    assert isinstance(episode_id, str) and episode_id

    inserts = [(sql, params) for (sql, params) in executed if "INSERT INTO episodes" in sql]
    assert len(inserts) == 1
    _, params = inserts[0]
    assert params is not None and params.get("session_id") == "s1"


@pytest.mark.asyncio
async def test_ensure_alloydb_schema_executes_expected_statements() -> None:
    executed: List[tuple[str, Optional[Dict[str, Any]]]] = []
    fake = _FakeAlloyDBConnector(executed)

    await ensure_alloydb_schema(fake, embedding_dim=768)  # type: ignore[arg-type]

    sqls = [sql for (sql, _) in executed]
    assert any("CREATE TABLE IF NOT EXISTS episodes" in s for s in sqls)
    assert any("CREATE EXTENSION IF NOT EXISTS google_ml_integration" in s for s in sqls)
    assert any("CREATE TABLE IF NOT EXISTS semantic_memories" in s for s in sqls)

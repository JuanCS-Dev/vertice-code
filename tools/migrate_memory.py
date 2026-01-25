from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy import text

from vertice_core.memory.alloydb_connector import AlloyDBConfig, AlloyDBConnector


@dataclass(frozen=True, slots=True)
class MigrationConfig:
    sqlite_path: Path
    alloydb_dsn: str
    embedding_model: str = "text-embedding-005"
    embedding_dim: int = 768
    types: Sequence[str] = ("episodic", "semantic")
    dry_run: bool = False


def _normalize_uuid(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"prometheus:{value}"))


def _parse_json(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def read_prometheus_memories(sqlite_path: Path) -> List[Dict[str, Any]]:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, type, content, metadata, importance, created_at FROM memories ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]


async def ensure_alloydb_schema(connector: AlloyDBConnector, *, embedding_dim: int) -> None:
    await connector.start()
    stmts = [
        # Episodes
        text(
            """
            CREATE TABLE IF NOT EXISTS episodes (
              id UUID PRIMARY KEY,
              session_id TEXT NOT NULL,
              agent_id TEXT NULL,
              event_type TEXT NOT NULL,
              content TEXT NOT NULL,
              metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ),
        text("CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id)"),
        text("CREATE INDEX IF NOT EXISTS idx_episodes_agent ON episodes(agent_id)"),
        text("CREATE INDEX IF NOT EXISTS idx_episodes_created_at ON episodes(created_at DESC)"),
        # Semantic
        text("CREATE EXTENSION IF NOT EXISTS vector"),
        text("CREATE EXTENSION IF NOT EXISTS google_ml_integration"),
        text(
            f"""
            CREATE TABLE IF NOT EXISTS semantic_memories (
              id UUID PRIMARY KEY,
              category TEXT NOT NULL,
              content TEXT NOT NULL,
              metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
              embedding vector({embedding_dim}) NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ),
        text(
            "CREATE INDEX IF NOT EXISTS idx_semantic_memories_category ON semantic_memories(category)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS idx_semantic_memories_created_at "
            "ON semantic_memories(created_at DESC)"
        ),
    ]

    async with connector.engine.begin() as conn:
        for stmt in stmts:
            await conn.execute(stmt)


async def migrate_memories(
    connector: AlloyDBConnector,
    *,
    memories: Iterable[Dict[str, Any]],
    embedding_model: str,
    types: Sequence[str],
    dry_run: bool,
) -> Dict[str, int]:
    counts = {"episodic": 0, "semantic": 0, "skipped": 0}
    await connector.start()

    async with connector.engine.begin() as conn:
        for m in memories:
            m_type = (m.get("type") or "").strip()
            if m_type not in types:
                counts["skipped"] += 1
                continue

            mid = _normalize_uuid(str(m.get("id") or ""))
            content = str(m.get("content") or "")
            metadata = _parse_json(m.get("metadata"))
            created_at = m.get("created_at")

            if m_type == "episodic":
                session_id = str(metadata.get("session_id") or "legacy-prometheus")
                agent_id = metadata.get("agent_id")
                event_type = str(metadata.get("event_type") or "memory")
                stmt = text(
                    """
                    INSERT INTO episodes (id, session_id, agent_id, event_type, content, metadata, created_at)
                    VALUES (
                      :id::uuid, :session_id, :agent_id, :event_type, :content, :metadata::jsonb,
                      COALESCE(:created_at::timestamptz, NOW())
                    )
                    ON CONFLICT (id) DO NOTHING
                    """
                )
                params = {
                    "id": mid,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "event_type": event_type,
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "created_at": created_at,
                }
                counts["episodic"] += 1
            elif m_type == "semantic":
                category = str(metadata.get("category") or "general")
                stmt = text(
                    """
                    INSERT INTO semantic_memories (id, category, content, metadata, embedding, created_at)
                    VALUES (
                      :id::uuid, :category, :content, :metadata::jsonb,
                      embedding(:model, :content),
                      COALESCE(:created_at::timestamptz, NOW())
                    )
                    ON CONFLICT (id) DO NOTHING
                    """
                )
                params = {
                    "id": mid,
                    "category": category,
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "model": embedding_model,
                    "created_at": created_at,
                }
                counts["semantic"] += 1
            else:
                counts["skipped"] += 1
                continue

            if dry_run:
                continue
            await conn.execute(stmt, params)

    return counts


async def migrate_sqlite_to_alloydb(cfg: MigrationConfig) -> Dict[str, int]:
    connector = AlloyDBConnector(AlloyDBConfig(dsn=cfg.alloydb_dsn))
    try:
        await ensure_alloydb_schema(connector, embedding_dim=cfg.embedding_dim)
        memories = read_prometheus_memories(cfg.sqlite_path)
        return await migrate_memories(
            connector,
            memories=memories,
            embedding_model=cfg.embedding_model,
            types=cfg.types,
            dry_run=cfg.dry_run,
        )
    finally:
        await connector.close()


def _parse_args(argv: Optional[Sequence[str]] = None) -> MigrationConfig:
    default_sqlite = Path(os.getcwd()) / ".prometheus" / "prometheus.db"
    parser = argparse.ArgumentParser(description="Migrate Prometheus SQLite memories to AlloyDB.")
    parser.add_argument("--sqlite", type=Path, default=default_sqlite)
    parser.add_argument(
        "--alloydb-dsn", default=os.getenv("VERTICE_ALLOYDB_DSN") or os.getenv("ALLOYDB_DSN")
    )
    parser.add_argument("--embedding-model", default="text-embedding-005")
    parser.add_argument("--embedding-dim", type=int, default=768)
    parser.add_argument(
        "--types",
        default="episodic,semantic",
        help="Comma-separated list: episodic,semantic",
    )
    parser.add_argument("--dry-run", action="store_true")
    ns = parser.parse_args(argv)

    if not ns.alloydb_dsn:
        raise SystemExit("Missing AlloyDB DSN. Provide --alloydb-dsn or set VERTICE_ALLOYDB_DSN.")

    types = tuple([t.strip() for t in str(ns.types).split(",") if t.strip()])
    return MigrationConfig(
        sqlite_path=ns.sqlite,
        alloydb_dsn=ns.alloydb_dsn,
        embedding_model=ns.embedding_model,
        embedding_dim=ns.embedding_dim,
        types=types,
        dry_run=bool(ns.dry_run),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    cfg = _parse_args(argv)
    counts = asyncio.run(migrate_sqlite_to_alloydb(cfg))
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

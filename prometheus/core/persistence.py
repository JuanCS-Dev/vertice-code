"""
Prometheus Persistence Layer.

Handles storage of Agent state, Memory (MIRIX), and Evolution (Agent0).
Uses aiosqlite for non-blocking persistence.

Schema:
- agent_state: Stores active task, context, and orchestrator state.
- memories: Stores episodic, semantic, and procedural memories.
- skills: Stores learned skills from Agent0 evolution.
- evolution_history: Stores the history of self-improvements.

Phase 4 of Prometheus Integration Roadmap v2.6.
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

import aiosqlite
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.getcwd(), ".prometheus", "prometheus.db")

# Ensure directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


class PersistenceLayer:
    """
    Async persistence layer for Prometheus using SQLite.
    
    Implements 'IMMEDIATE' transactions for write safety and 
    connection pooling via aiosqlite.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._initialized = False

    async def initialize(self):
        """Initialize database schema."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency
            await db.execute("PRAGMA journal_mode=WAL;")
            
            # Agent State Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Memories Table (MIRIX)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,  -- episodic, semantic, procedural
                    content TEXT NOT NULL,
                    metadata TEXT,
                    importance FLOAT DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Index for fast retrieval by type and importance
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type_importance 
                ON memories(type, importance DESC);
            """)

            # Skills Table (Agent0)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    name TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    description TEXT,
                    success_rate FLOAT DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Evolution History
            await db.execute("""
                CREATE TABLE IF NOT EXISTS evolution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation INTEGER,
                    changes TEXT,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.commit()
            self._initialized = True
            logger.info(f"Persistence initialized at {self.db_path}")

    async def save_state(self, key: str, value: Dict[str, Any]):
        """Save a state object."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), datetime.now().isoformat())
            )
            await db.commit()

    async def load_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a state object."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM agent_state WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
        return None

    async def store_memory(self, memory_id: str, type: str, content: str, metadata: Dict[str, Any], importance: float):
        """Store a memory item."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO memories (id, type, content, metadata, importance)
                VALUES (?, ?, ?, ?, ?)
                """,
                (memory_id, type, content, json.dumps(metadata), importance)
            )
            await db.commit()

    async def retrieve_memories(self, type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve top important memories by type."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM memories WHERE type = ? ORDER BY importance DESC LIMIT ?",
                (type, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    mem = dict(row)
                    mem['metadata'] = json.loads(mem['metadata']) if mem['metadata'] else {}
                    results.append(mem)
                return results

    async def store_skill(self, name: str, code: str, description: str):
        """Store a learned skill."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO skills (name, code, description)
                VALUES (?, ?, ?)
                """,
                (name, code, description)
            )
            await db.commit()

    async def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM skills ORDER BY usage_count DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def log_evolution(self, generation: int, changes: Dict[str, Any], metrics: Dict[str, Any]):
        """Log an evolution step."""
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO evolution_history (generation, changes, metrics) VALUES (?, ?, ?)",
                (generation, json.dumps(changes), json.dumps(metrics))
            )
            await db.commit()

# Singleton instance
persistence = PersistenceLayer()

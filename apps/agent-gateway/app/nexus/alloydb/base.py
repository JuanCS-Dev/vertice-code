"""
AlloyDB Base - Connection and Schema Management.

Handles AlloyDB connection initialization, schema creation, and base operations.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from nexus.config import NexusConfig

logger = logging.getLogger(__name__)

# Feature flags
ALLOYDB_AVAILABLE = False
VERTEX_EMBEDDINGS_AVAILABLE = False
ASYNCPG_AVAILABLE = False

try:
    from langchain_google_alloydb_pg import (
        AlloyDBEngine,
        AlloyDBVectorStore,
    )

    ALLOYDB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AlloyDB LangChain not available: {e}")

try:
    from langchain_google_vertexai import VertexAIEmbeddings

    VERTEX_EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vertex AI Embeddings not available: {e}")

try:
    import asyncpg as _asyncpg_check
    ASYNCPG_AVAILABLE = True
    del _asyncpg_check
except ImportError:
    pass


NEXUS_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS nexus_memories (
    id TEXT PRIMARY KEY,
    level TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    token_count INTEGER DEFAULT 0,
    importance FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS nexus_insights (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    context TEXT,
    observation TEXT,
    causal_analysis TEXT,
    learning TEXT,
    action TEXT,
    confidence FLOAT DEFAULT 0.0,
    category TEXT,
    applied BOOLEAN DEFAULT FALSE,
    embedding vector(768),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS nexus_evolution (
    id TEXT PRIMARY KEY,
    code TEXT,
    prompt TEXT,
    ancestry TEXT[],
    generation INTEGER DEFAULT 0,
    island_id INTEGER DEFAULT 0,
    fitness_scores JSONB DEFAULT '{}'::jsonb,
    evaluation_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS nexus_healing (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    anomaly_type TEXT,
    anomaly_severity FLOAT DEFAULT 0.0,
    diagnosis TEXT,
    action TEXT,
    success BOOLEAN DEFAULT FALSE,
    rollback_available BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS nexus_state (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    state JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memories_level ON nexus_memories(level);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON nexus_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_insights_category ON nexus_insights(category);
CREATE INDEX IF NOT EXISTS idx_insights_confidence ON nexus_insights(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_evolution_generation ON nexus_evolution(generation);
CREATE INDEX IF NOT EXISTS idx_healing_timestamp ON nexus_healing(timestamp DESC);
"""


class AlloyDBBase:
    """
    Base class for AlloyDB operations.

    Handles connection management and provides shared infrastructure.
    """

    def __init__(self, config: NexusConfig):
        """Initialize AlloyDB base."""
        self.config = config
        self._engine: Optional[Any] = None
        self._vector_store: Optional[Any] = None
        self._embeddings: Optional[Any] = None
        self._pool: Optional[Any] = None
        self._initialized = False

        self.project_id = config.project_id
        self.region = config.location
        self.cluster = os.getenv("ALLOYDB_CLUSTER", "vertice-memory-cluster")
        self.instance = os.getenv("ALLOYDB_INSTANCE", "vertice-memory-primary")
        self.database = os.getenv("ALLOYDB_DATABASE", "postgres")
        self.dsn = os.getenv("ALLOYDB_DSN")

    @property
    def is_initialized(self) -> bool:
        """Check if store is initialized."""
        return self._initialized

    async def initialize(self) -> bool:
        """Initialize AlloyDB connection and schema."""
        if self._initialized:
            return True

        if not ALLOYDB_AVAILABLE:
            logger.warning("AlloyDB not available, using in-memory fallback")
            return False

        try:
            if VERTEX_EMBEDDINGS_AVAILABLE:
                self._embeddings = VertexAIEmbeddings(
                    model_name="gemini-embedding-001",
                    project=self.project_id,
                    location=self.region,
                )

            if self.dsn:
                await self._init_with_dsn()
            else:
                await self._init_with_langchain()

            await self._create_schema()
            self._initialized = True
            logger.info("✅ AlloyDB store initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AlloyDB: {e}")
            return False

    async def _init_with_dsn(self) -> None:
        """Initialize using direct DSN connection."""
        if not ASYNCPG_AVAILABLE:
            raise RuntimeError("asyncpg not available")

        import asyncpg  # noqa: F811

        self._pool = await asyncpg.create_pool(
            dsn=self.dsn.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2,
            max_size=10,
            command_timeout=30,
        )

    async def _init_with_langchain(self) -> None:
        """Initialize using LangChain AlloyDBEngine."""
        self._engine = await AlloyDBEngine.afrom_instance(
            project_id=self.project_id,
            region=self.region,
            cluster=self.cluster,
            instance=self.instance,
            database=self.database,
        )

        if self._embeddings:
            await self._engine.ainit_vectorstore_table(
                table_name="nexus_memories_vector",
                vector_size=768,
                overwrite_existing=False,
            )
            self._vector_store = await AlloyDBVectorStore.create(
                engine=self._engine,
                embedding_service=self._embeddings,
                table_name="nexus_memories_vector",
            )

    async def _create_schema(self) -> None:
        """Create NEXUS tables."""
        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(NEXUS_SCHEMA_SQL)
        elif self._engine:
            async with self._engine._pool.acquire() as conn:
                await conn.execute(NEXUS_SCHEMA_SQL)

    async def close(self) -> None:
        """Close database connections."""
        if self._pool:
            await self._pool.close()
        if self._engine:
            await self._engine.close()
        self._initialized = False

    async def execute(self, query: str, *args) -> Any:
        """Execute a query."""
        if self._pool:
            async with self._pool.acquire() as conn:
                return await conn.execute(query, *args)
        elif self._engine:
            async with self._engine._pool.acquire() as conn:
                return await conn.execute(query, *args)
        return None

    async def fetch(self, query: str, *args) -> list:
        """Fetch rows from a query."""
        if self._pool:
            async with self._pool.acquire() as conn:
                return await conn.fetch(query, *args)
        elif self._engine:
            async with self._engine._pool.acquire() as conn:
                return await conn.fetch(query, *args)
        return []

    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        """Fetch a single row."""
        if self._pool:
            async with self._pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        elif self._engine:
            async with self._engine._pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        return None

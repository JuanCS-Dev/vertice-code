-- Vertice Core Memory Schema (AlloyDB / Postgres)
-- Scope: MVP for EpisodicMemory + SemanticMemory (Phase 4 cutover).

-- Extensions required for AlloyDB AI vector search.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

CREATE TABLE IF NOT EXISTS episodes (
  id UUID PRIMARY KEY,
  session_id TEXT NOT NULL,
  agent_id TEXT NULL,
  event_type TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id);
CREATE INDEX IF NOT EXISTS idx_episodes_agent ON episodes(agent_id);
CREATE INDEX IF NOT EXISTS idx_episodes_created_at ON episodes(created_at DESC);

-- Semantic memory (knowledge/facts) with DB-side embeddings.
-- Note: adjust vector dimension if your embedding model changes.
CREATE TABLE IF NOT EXISTS semantic_memories (
  id UUID PRIMARY KEY,
  category TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(768) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_semantic_memories_category ON semantic_memories(category);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_created_at ON semantic_memories(created_at DESC);

# PR‑4 — AlloyDB desde o início (fundação de memória) — Episodic MVP
**Date:** January 25, 2026
**Scope:** Backend-only, config-driven, sem infraestrutura AlloyDB real (testes com fakes/mocks)

---

## Objetivo
Implementar a fundação de memória em **AlloyDB/Postgres** no `vertice-core`, migrando **primeiro** a camada
`EpisodicMemory` para aceitar AlloyDB como backend via configuração (sem trocar o sistema inteiro de uma vez).

## Atualização (Phase 4)
O **cutover** (AlloyDB como default, com fallback para SQLite apenas sem DSN) + **migração real** + **memória
semântica com embeddings nativos** foram implementados em `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`.

## Entregáveis implementados

### 1) Conector AlloyDB com pool
- Arquivo: `packages/vertice-core/src/vertice_core/memory/alloydb_connector.py`
- Componentes:
  - `AlloyDBConfig(dsn: str, pool_size: int = 5)`
  - `AlloyDBConnector` (wrapper de `sqlalchemy.ext.asyncio.AsyncEngine`)
- Responsabilidades:
  - `start()` idempotente: cria o engine e gerencia pool.
  - `close()`: `dispose()` do engine.
  - `connect()`: async context manager retornando `AsyncConnection`.

### 2) Schema MVP (episódico)
- Arquivo: `packages/vertice-core/src/vertice_core/memory/schema.sql`
- Estrutura mínima (Postgres/AlloyDB-friendly):
  - Tabela `episodes` com `UUID`, `JSONB`, `TIMESTAMPTZ`.
  - Índices por `session_id`, `agent_id`, `created_at` para leituras “recent/session”.

### 3) EpisodicMemory aceita AlloyDB via config (sem quebrar SQLite)
- Arquivo: `packages/vertice-core/src/vertice_core/memory/cortex/episodic.py`
- Config:
  - `EpisodicBackendConfig(backend="sqlite"|"alloydb", alloydb_dsn=..., alloydb_pool_size=...)`
- Comportamento:
  - Nesta fundação (PR‑4), o default era **SQLite** (para não cortar o sistema atual).
  - Quando `backend="alloydb"`:
    - Usa `AlloyDBConnector` (ou aceita injeção via `alloydb=` para testes).
    - Executa init/schema e CRUD via engine async (ponte sync para não exigir callers async).

## Como habilitar (dev/local)

```python
from vertice_core.memory.cortex.episodic import EpisodicBackendConfig, EpisodicMemory
from vertice_core.memory.cortex.connection_pool import get_connection_pool
from pathlib import Path

config = EpisodicBackendConfig(
    backend="alloydb",
    alloydb_dsn="postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME",  # pragma: allowlist secret
    alloydb_pool_size=5,
)

memory = EpisodicMemory(db_path=Path("episodic.db"), pool=get_connection_pool(), config=config)
```

## Como aplicar o schema (quando houver um Postgres/AlloyDB disponível)

```bash
psql "$DATABASE_URL" -f packages/vertice-core/src/vertice_core/memory/schema.sql
```

## Validação executada (25 JAN 2026)

```bash
ruff check --fix packages/vertice-core/src/vertice_core/memory/alloydb_connector.py \
  packages/vertice-core/src/vertice_core/memory/cortex/episodic.py \
  tests/unit/test_alloydb_migration.py

ruff format packages/vertice-core/src/vertice_core/memory/alloydb_connector.py \
  packages/vertice-core/src/vertice_core/memory/cortex/episodic.py \
  tests/unit/test_alloydb_migration.py

pytest tests/unit/test_alloydb_migration.py -v -x
```

Resultado: `2 passed` (sem rede/infra real).

## Addendum (Phase 4 — 25 JAN 2026)
- **Cutover aplicado:** AlloyDB como default + fallback para SQLite quando não há DSN.
- **Embeddings nativos:** memória semântica com `google_ml_integration` (embeddings via SQL).
- **Migração real:** `tools/migrate_memory.py` para mover `.prometheus/prometheus.db` → AlloyDB.
- **Validação (offline):**
  - `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x`
  - Resultado: `14 passed in 0.53s`

## Limitações (intencionais) / próximos passos
- **Cutover ainda não feito:** SQLite segue como default enquanto o resto do sistema migra.
- **Migração de dados** (`prometheus.db` → AlloyDB) não está incluída nesta etapa.
- **Vetores/embeddings/triggers** (pgvector, google_ml_integration, pipelines batch) ficam para PRs futuras.

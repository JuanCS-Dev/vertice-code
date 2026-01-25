# Phase 4 — AlloyDB AI Cutover (Eternidade dos Dados)

## Objetivo
Tornar o **AlloyDB AI** a **Fonte da Verdade única** para memória (episódica + semântica), com **embeddings gerados
dentro do banco** via `google_ml_integration` (SQL: `embedding('text-embedding-005', text)`), mantendo **fallback
para SQLite apenas em dev/local sem DSN**.

## O que foi implementado (backend)
- **Cutover (default AlloyDB):**
  - `EpisodicMemory`: default `backend="alloydb"` com failover para SQLite quando **não existe DSN**.
  - `SemanticMemory`: refeito para **AlloyDB AI + pgvector**, com failover para **SQLite FTS** (sem LanceDB).
- **Embeddings no banco (zero Python overhead):**
  - Inserção e busca semântica usam `embedding(:model, :text)` dentro do SQL.
- **Wiring (MemoryCortex):**
  - Lê DSN via `VERTICE_ALLOYDB_DSN` (ou `ALLOYDB_DSN`) e injeta nos backends.
- **Migração real:**
  - `tools/migrate_memory.py` migra `memories` do SQLite legado (`.prometheus/prometheus.db`) para AlloyDB:
    - `type=episodic` → tabela `episodes`
    - `type=semantic` → tabela `semantic_memories` (embedding via SQL)
- **Correção de durabilidade (SQLite):**
  - `EpisodicMemory` (SQLite fallback) agora faz `commit()` após `INSERT/DELETE` para persistência real em disco.

## Variáveis de ambiente
- `VERTICE_ALLOYDB_DSN`: DSN do Postgres/AlloyDB (ex: `postgresql+asyncpg://user:pass@host:5432/db`)  <!-- pragma: allowlist secret -->
- (fallback) `ALLOYDB_DSN`: alias aceito

## Como rodar a migração
```bash
python -m tools.migrate_memory --dry-run
python -m tools.migrate_memory --types episodic,semantic
```

## Testes e validação (executados nesta etapa)
```bash
ruff format tests/unit/test_alloydb_cutover_behavior.py
ruff check tests/unit/test_alloydb_cutover_behavior.py

pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x
```

### Resultados
- `pytest`: `14 passed in 0.53s` (sem rede/infra AlloyDB real; conectores fakes/mocks)

## Referências de implementação
- Core (cutover + in-db embeddings): `packages/vertice-core/src/vertice_core/memory/cortex/`
- Schema: `packages/vertice-core/src/vertice_core/memory/schema.sql`
- Migração: `tools/migrate_memory.py`

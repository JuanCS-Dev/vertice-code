# PR‑5 — Troca real para Google gerenciado (Vertex AI) (2026)

**Data:** 25 JAN 2026
**Escopo:** Backend + Core Protocol + Testes (sem frontend)

Esta etapa consolida o modo **Google‑managed**: inferência via **Vertex AI** e execução de código via **sandbox gerenciado**
(sem `exec()`/`eval()` local).

---

## 1) Entregáveis

### PR‑5A — Adapter de execução remota (Code Execution / Code Interpreter)

- **Objetivo:** habilitar execução de código **somente** via Vertex AI (sandbox gerenciado).
- **Postura de segurança:** *fail‑closed* — se não estiver habilitado/configurado, retorna erro explícito.
- **Implementação (backend SaaS):**
  - `vertice-chat-webapp/backend/app/sandbox/executor.py`
    - execução local bloqueada (`LocalCodeExecutionDisabledError`)
    - caminho remoto opcional quando `SandboxConfig.remote_executor == "vertex_code_execution"`
  - `vertice-chat-webapp/backend/app/sandbox/vertex_code_execution.py`
    - execução via **Google Gen AI SDK** em Vertex AI (`google.genai`)
    - tool de **Code Execution** (sandbox gerenciado)
  - `vertice-chat-webapp/backend/app/sandbox/mcp_server.py`
    - feature flag por env var para habilitar caminho remoto

### PR‑5B — “Reasoning Engines” (staging) para o Coder

- **Objetivo:** preparar o caminho para migração ao padrão ADK/Reasoning Engines sem depender de `google.adk` já instalado.
- **Implementação (core + deploy tooling):**
  - `packages/vertice-core/src/agents/coder/reasoning_engine_app.py`
  - `packages/vertice-core/src/vertice_core/agents/coder/reasoning_engine_app.py`
  - `tools/deploy_brain.py` aponta `coder` para o novo app.

---

## 2) Modelos permitidos (hard allowlist)

**PROIBIDO:** qualquer modelo fora da allowlist abaixo (fail‑fast).

**Permitidos (Vertex AI):**
- Gemini 3: `gemini-3-pro`, `gemini-3-flash`, `gemini-3-pro-preview`, `gemini-3-flash-preview`
  - Enforced em: `packages/vertice-core/src/vertice_core/providers/vertex_ai.py`
- Claude 4.5 via Vertex AI:
  - `claude-sonnet-4-5@20250929`
  - `claude-opus-4-5@20251101`
  - Enforced em: `packages/vertice-core/src/vertice_core/providers/anthropic_vertex.py`

---

## 3) Configuração (global endpoint)

Defaults e overrides:
- `GOOGLE_CLOUD_LOCATION=global` (preferencial)
- `VERTEX_AI_LOCATION=global` (compat legada)
- `GOOGLE_CLOUD_PROJECT=<project_id>`

**Code Execution (sandbox gerenciado):**
- `VERTEX_CODE_EXECUTION_ENABLED=1` habilita o caminho remoto no MCP server
- `VERTEX_CODE_EXECUTION_MODEL=gemini-3-flash-preview` (default atual)

---

## 4) Validação executada (25 JAN 2026)

### Testes (offline, sem rede)

```bash
pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x
pytest tests/unit/test_coder_reasoning_engine_app.py -v -x
pytest tests/integration/test_vertex_deploy.py -v -x
```

Resultados:
- `test_sandbox_executor.py`: **10 passed**
- `test_coder_reasoning_engine_app.py`: **2 passed**
- `test_vertex_deploy.py`: **2 passed**

### Lint/format (arquivos tocados)

```bash
ruff check --fix <files...>
ruff format <files...>
```

Resultado: **All checks passed** (ruff) + formatação aplicada.

---

## 5) Smoke test (live) — opcional / fora da CI

Os testes “live” com Vertex AI devem ser habilitados explicitamente (evita travar CI/ambiente sem quota):
- `RUN_VERTEX_LIVE_TESTS=1`

---

## Update (25 JAN 2026) — Phase 4 (AlloyDB AI Cutover)

- Memória agora default AlloyDB AI (fallback local sem DSN) + embeddings in-db via `google_ml_integration`.
- Migração real: `tools/migrate_memory.py` (`.prometheus/prometheus.db` → AlloyDB).
- Validação (offline): `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x` → `14 passed in 0.53s`.
- Detalhes: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`.

---

## Update (25 JAN 2026) — PR‑6 (Vertex AI Integration Cutover)

- `agent-gateway` agora suporta streaming **real** via **Vertex Agent Engine** (feature‑flagged).
- Tradução em tempo real: Vertex stream dict events → envelope “ADK‑ish” → schema **AG‑UI** (`delta|tool|final|error`).
- **Fallback ReasoningEngine:** quando o recurso não expõe streaming, usa `query(input=...)` e sintetiza `delta|final`.
- Config principal:
  - `VERTEX_AGENT_ENGINE_ENABLED=1`
  - `GOOGLE_CLOUD_LOCATION=global` (ou `VERTEX_AI_LOCATION=global` para compat)
  - `apps/agent-gateway/config/engines.json` preenchido por `tools/deploy_brain.py`
- Validação (offline):
  - `pytest tests/unit/test_vertex_agent_engine_adapter.py -v -x` → `2 passed`
  - `pytest tests/unit/test_reasoning_engine_app_query_input.py -v -x` → `3 passed`
  - `pytest tests/unit/test_vertex_ai_provider_location.py -v -x` → `2 passed`
  - `pytest tests/unit/test_vertex_reasoning_engine_fallback.py -v -x` → `1 passed`
- Smoke test (live, opt-in): `pytest tests/integration/test_vertex_reasoning_engine_live_smoke.py -v -x` com
  `RUN_VERTEX_LIVE_TESTS=1`.
- Detalhes: `docs/google/PR_6_VERTEX_AI_INTEGRATION_CUTOVER_2026.md`.

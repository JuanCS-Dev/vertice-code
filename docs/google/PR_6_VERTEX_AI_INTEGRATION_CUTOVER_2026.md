# PR‑6 — Vertex AI Integration Cutover (De Mocks para Streaming Real) (2026)

**Data:** 25 JAN 2026
**Escopo:** Backend + Core Protocol + Testes (sem frontend)

Objetivo: substituir o streaming mockado no `agent-gateway` por **streaming real** via **Vertex AI Agent Engine**
(ADK runtime), traduzindo os chunks em tempo real para o schema estável **AG‑UI** (`delta|tool|final|error`).

---

## 1) Entregáveis

### 1.1 Gateway: streaming real (feature‑flagged, fail‑closed)

- `apps/agent-gateway/app/main.py`
  - Troca `_mock_adk_events` → `_upstream_adk_events` com seleção por feature flag.
  - Lookup do engine por agente em `apps/agent-gateway/config/engines.json`.
  - Query param/field novo (backward‑compatible):
    - `agent="coder"` (default)
    - `tool` permanece **apenas** para simulação no modo mock.

### 1.2 Core: adapter Vertex stream → ADK‑ish → AG‑UI

- `packages/vertice-core/src/vertice_core/agui/vertex_agent_engine.py`
  - Normaliza o stream do Vertex (dict events) para o envelope “ADK‑ish” mínimo.
  - Mapeia:
    - `content.parts[].text` → `{"type":"delta"}`
    - `content.parts[].function_call` → `{"type":"tool","status":"call"}`
    - `content.parts[].function_response` → `{"type":"tool","status":"ok"}`
  - Emite `final` sintetizado ao término do stream (concat dos deltas) para garantir terminalidade no AG‑UI.
  - **Fallback ReasoningEngine:** se o recurso não expõe streaming (`async_stream_query`), usa `query(input=...)`
    e sintetiza `delta` + `final` a partir do texto final.

### 1.3 Deploy: runtime empacotado (corrige `ModuleNotFoundError: agents`)

- `tools/deploy_brain.py`
  - Envia o código do monorepo para o runtime via `extra_packages` (default: `packages/vertice-core/src`).
  - Permite configurar explicitamente:
    - `--staging-bucket gs://...`
    - `--requirement <pkg>` (repeatable)
    - `--extra-package <dir|wheel>` (repeatable)
    - `--sys-version 3.11` (opcional)
  - Default de região do runtime: `--location us-central1`

---

## 2) Configuração (2026 / Global Endpoint)

### 2.1 Região obrigatória: `global`

Para modelos “top tier” (Gemini 3 e Claude 4.5 via Vertex AI), a prática recomendada em 2026 é usar **Global Endpoint**:

- `GOOGLE_CLOUD_LOCATION=global` (preferencial; alinhado à doc oficial)
- `VERTEX_AI_LOCATION=global` (compat legada no nosso código)

### 2.2 Região do Reasoning Engine (recurso gerenciado)

**Atenção:** o recurso **Reasoning Engine / Agent Engine** é **regional** (ex.: `us-central1`) e não aceita `location=global`
para criação/serving do runtime.

Isso é **separado** do “global endpoint” usado para inferência de modelos puros.

Recomendação prática:
- `tools/deploy_brain.py --location us-central1`
- `apps/agent-gateway/config/engines.json` deve registrar `location: "us-central1"` para o engine.

Exemplo de deploy (com bucket de staging):
```bash
python tools/deploy_brain.py --agent coder --project "<project>" --location us-central1 \
  --staging-bucket "gs://vertice-ai-reasoning-staging"
```

### 2.2 Feature flag do gateway

- `VERTEX_AGENT_ENGINE_ENABLED=1`
  - Quando **desligado**: gateway continua no modo mock (útil para CI/offline).
  - Quando **ligado**: gateway exige `engines.json` válido e engine configurado (fail‑closed com `error`).

### 2.3 Engines registry

Arquivo: `apps/agent-gateway/config/engines.json`

Entrada mínima por agente:

```json
{
  "engines": {
    "coder": {
      "engine_id": "projects/<p>/locations/us-central1/reasoningEngines/<id>",
      "project": "<p>",
      "location": "us-central1"
    }
  }
}
```

O `tools/deploy_brain.py` continua sendo o caminho suportado para preencher esse registry.

---

## 3) Validação executada (25 JAN 2026, offline)

### Testes unitários (sem rede)

```bash
pytest tests/unit/test_vertex_agent_engine_adapter.py -v -x
pytest tests/unit/test_agents_import_packaging.py -v -x
pytest tests/unit/test_deploy_brain_runtime_packaging.py -v -x
pytest tests/unit/test_reasoning_engine_app_query_input.py -v -x
pytest tests/unit/test_vertex_ai_provider_location.py -v -x
pytest tests/unit/test_vertex_reasoning_engine_fallback.py -v -x
```

Resultados:
- `test_vertex_agent_engine_adapter.py`: **2 passed**
- `test_agui_adk_adapter.py`: **5 passed**
- `test_agents_import_packaging.py`: **1 passed**
- `test_deploy_brain_runtime_packaging.py`: **1 passed**
- `test_reasoning_engine_app_query_input.py`: **3 passed**
- `test_vertex_ai_provider_location.py`: **2 passed**
- `test_vertex_reasoning_engine_fallback.py`: **1 passed**

### Lint/format (arquivos tocados)

```bash
ruff check --fix apps/agent-gateway/app/main.py \
  packages/vertice-core/src/vertice_core/agui/vertex_agent_engine.py \
  packages/vertice-core/src/vertice_core/providers/vertex_ai.py \
  tests/unit/test_vertex_agent_engine_adapter.py

ruff format apps/agent-gateway/app/main.py \
  packages/vertice-core/src/vertice_core/agui/vertex_agent_engine.py \
  packages/vertice-core/src/vertice_core/providers/vertex_ai.py \
  tests/unit/test_vertex_agent_engine_adapter.py
```

Resultado: **All checks passed** (ruff) + formatação aplicada.

---

## 4) Smoke test (live) — opcional / fora da CI

Pré‑requisitos:
- ADC configurado (`gcloud auth application-default login`)
- `VERTEX_AGENT_ENGINE_ENABLED=1`
- `apps/agent-gateway/config/engines.json` com `coder.engine_id`

Execução (exemplo):

```bash
export VERTEX_AGENT_ENGINE_ENABLED=1
export GOOGLE_CLOUD_PROJECT="<project>"
export GOOGLE_CLOUD_LOCATION="global"
uvicorn apps.agent-gateway.app.main:app --port 8000
```

Consumir SSE:

```bash
curl -N "http://localhost:8000/agui/stream?session_id=s1&agent=coder&prompt=hello"
```

Esperado:
- Eventos `delta` durante a geração.
- Eventos `tool` quando houver function calls/responses do runtime ADK.
- Evento terminal `final` (ou `error` fail‑closed).

### 4.1 Smoke test (live) via pytest (recomendado)

Arquivo:
- `tests/integration/test_vertex_reasoning_engine_live_smoke.py`

Rodar (somente local/dev; não roda em CI por padrão):

```bash
export RUN_VERTEX_LIVE_TESTS=1
pytest tests/integration/test_vertex_reasoning_engine_live_smoke.py -v -x
```

Esse teste valida o contrato mínimo do runtime:
- `agent_engines.get(resource_name=engine_id)` resolve
- `.query(input=...)` retorna `{ "output": "<texto>" }`

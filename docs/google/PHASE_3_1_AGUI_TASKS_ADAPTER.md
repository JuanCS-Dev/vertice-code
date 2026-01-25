# Phase 3.1 (Backend-Only): `ag_ui_adk` adapter + `/agui/tasks`

**Date:** January 25, 2026  
**Scope:** Backend-only (Gateway + Core Protocol + Tests)  
**Decisions locked:**
- SSE em `GET /agui/stream` e `GET /agui/tasks/{task_id}/stream`
- Schema MVP estável com eventos `delta|final|tool|error`
- Sem mudanças de frontend nesta etapa

---

## Entregáveis implementados

### 1) Core: Adapter `ag_ui_adk`
- Arquivo: `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py`
- Objetivo: isolar variações do upstream (ADK/Reasoning Engines) e estabilizar o contrato interno em `AGUIEvent`.
- Funções:
  - `adk_event_to_agui(event, session_id=...) -> AGUIEvent`
  - `adk_events_to_agui(events, session_id=...) -> AsyncIterator[AGUIEvent]`
- Suporta payload com campos no topo ou aninhados em `data`.

### 2) Gateway: `/agui/stream` + `/agui/tasks`
- Arquivo: `apps/agent-gateway/app/main.py`
- `GET /agui/stream` (SSE):
  - Query params: `prompt` (required), `session_id` (default `"default"`), `tool` (opcional, MVP)
  - Stream: converte eventos “ADK-ish” para `AGUIEvent` via `adk_event_to_agui()` e serializa via `sse_encode_event()`.
- `POST /agui/tasks`:
  - Body: `{ "prompt": "...", "session_id": "default", "tool": "..."? }`
  - Resposta (201): `task_id`, `status`, `stream_url`, `created_at`, `updated_at`
- `GET /agui/tasks/{task_id}`:
  - Status e metadados do task.
- `GET /agui/tasks/{task_id}/stream` (SSE):
  - Stream por task, baseado em fila in-memory (`TaskState.events`) + `asyncio.Condition`.
  - Termina em `final` ou `error`.

**Nota:** O upstream ainda é mockado (`_mock_adk_events`) para desacoplar “mecânica do stream + protocolo” da integração Vertex (próxima etapa).

---

## Firebase App Hosting (cleanup)

- Arquivo: `firebase.json`
- Objetivo: remover rewrites antigos do backend legado e consolidar no padrão App Hosting.
- Atualização:
  - Removidos rewrites obsoletos para Cloud Run antigo (`/api/**`).
  - Configuração agora usa `apphosting` com `rootDirectory` em `vertice-chat-webapp/frontend`.
  - Região alvo: `us-central1` (backend App Hosting deve ser criado/configurado via CLI em `us-central1`).

---

## Testes e validação executados (25 JAN 2026)

### Unit
- `pytest tests/unit/test_agui_protocol.py -v -x` (1 passed)
- `pytest tests/unit/test_agui_adk_adapter.py -v -x` (5 passed)

### Integration
- `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x` (6 passed)
  - Inclui: criação de task (`POST /agui/tasks`), polling (`GET /agui/tasks/{id}`) e stream (`GET /agui/tasks/{id}/stream`).

### Observação (ambiente)
- `FastAPI/Starlette TestClient` travou neste ambiente; os testes usam `httpx.ASGITransport` para evitar deadlock e garantir fechamento do stream SSE.


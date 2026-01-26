# BACKEND NERVOUS SYSTEM IMPLEMENTATION PLAN (AG-UI v2.0)

**PRIORITY:** CRITICAL (Foundation for Narcissus)
**TECH DEBT:** Atomic Streaming & Granular Event Handoff.

## 1. PROTOCOL UPGRADE (FastAPI SSE)
Refatorado para `apps/agent-gateway/api/stream.py` (usado por `apps/agent-gateway/app/main.py`) com:
- **Headers SSE:** `Cache-Control: no-cache` e `X-Accel-Buffering: no` (constante `STREAM_HEADERS`).
- **Multi-frame (sem quebrar o MVP):** o `event:` continua `delta|final|tool|error`, mas o payload adiciona:
  - `data.frame`: `intent|thought|code_delta|trajectory`
  - `data.channel`: `thought` (apenas para thought frames)

Frames implementados (compatíveis com AG-UI MVP):
- **IntentEvent:** `type="tool"` + `data.name="intent"` + `data.frame="intent"` (emitido no início do stream).
- **ThoughtEvent:** `type="delta"` + `data.frame="thought"` + `data.channel="thought"`.
- **CodeDeltaEvent:** `type="tool"` + `data.frame="code_delta"` (derivado de tools `write_file|create_file|apply_patch|delete_file|edit_file`).
- **TrajectoryUpdate:** `type="tool"` + `data.frame="trajectory"` (tools `trajectory*`).

## 2. ADK ENHANCEMENT (Agent Telemetry)
Update `vertice_core.adk.base.VerticeAgent`:
- Add `self.emit_event(event_type, payload)` method.
- Automate `intent` emission: The moment `query()` is called, the agent must broadcast its "Understanding Frame".

Status: ✅ Implementado
- Implementação em `packages/vertice-core/src/vertice_core/adk/base.py`
  - `emit_event(event_type, payload)` emite `SystemEvent` no `EventBus` global (`vertice_core.messaging.events.get_event_bus()`).
  - Auto-`intent` no início de toda `query()` async via wrapping em `__init_subclass__` (sem exigir mudanças em subclasses).
  - Default `location="global"` no agente base para compatibilidade com inferência Vertex “top-tier” via endpoint global.

## 3. PROVIDER PRECISION (Vertex AI CoT)
Modify `vertice_core.providers.vertex_ai.VertexAIProvider`:
- **Thinking (Google GenAI SDK 2026):** habilita `types.ThinkingConfig(include_thoughts=True)` via:
  - kwarg `include_thoughts=True` (ou env `VERTICE_VERTEX_INCLUDE_THOUGHTS=1`)
- **Split de pensamento:** o provider embrulha thought parts em `<thought>...</thought>` e o gateway faz split incremental.
- **Goal:** Fluid 60fps rendering of the agent's "inner voice".

Segurança:
- Por padrão, o gateway **redige** thought frames (`"[REDACTED]"`) a menos que `VERTICE_STREAM_THOUGHTS=1`.

Status: ✅ Implementado
- Provider: `packages/vertice-core/src/vertice_core/providers/vertex_ai.py`
  - Quando thinking está habilitado e o SDK suporta, thought parts são emitidas como `"<thought>...</thought>"`.
  - Model IDs (Vertex, 2026): defaults para `gemini-3-pro-preview` / `gemini-3-flash-preview` com `location="global"`,
    evitando 404 por usar IDs sem `-preview`.
- Gateway: `apps/agent-gateway/api/stream.py`
  - Split incremental por tags `<thought>` (tolerante a “chunk boundaries”).
  - Final sempre remove blocos de thought do `final.text` (`strip_thought_blocks()`), evitando “vazamento” no output funcional.
  - Redação padrão dos thought frames: **ON** (habilitar explicitamente com `VERTICE_STREAM_THOUGHTS=1`).

## 4. ALLOYDB SYNC (Persistence Audit)
- Every `CodeDeltaEvent` must trigger an async background save to AlloyDB AI to ensure the "Unsaved Changes" indicator in the front is accurate.

Implementado no gateway (sem bloquear o loop):
- Em cada tool frame `code_delta`, o gateway agenda `MemoryCortex.remember(..., memory_type="episodic", event_type="code_delta")`.
- AlloyDB é usado quando `VERTICE_ALLOYDB_DSN`/`ALLOYDB_DSN` está configurado; caso contrário, cai para SQLite local.

Status: ✅ Implementado (com feature flag)
- Implementação: `apps/agent-gateway/api/stream.py`
  - Persistência é assíncrona (background task) para não degradar o streaming.
  - Flag de testes/dev: `VERTICE_PERSIST_CODE_DELTAS=0` desliga persistência (evita tasks pendentes em testes unitários/ASGI).

## Variáveis de Ambiente (Operação)
- `VERTEX_AGENT_ENGINE_ENABLED=1` habilita streaming real do Vertex Agent/Reasoning Engine (caso contrário usa mock).
- `VERTICE_VERTEX_INCLUDE_THOUGHTS=1` habilita thinking no provider (emite `<thought>...</thought>`).
- `VERTICE_STREAM_THOUGHTS=1` permite enviar thought frames ao cliente (por padrão sai `"[REDACTED]"`).
- `VERTICE_PERSIST_CODE_DELTAS=0` desliga persistência de `code_delta` (útil para testes).
- `VERTICE_ALLOYDB_DSN`/`ALLOYDB_DSN` define AlloyDB como destino de persistência (senão usa SQLite local).
- `VERTICE_CORTEX_PATH` (opcional) define onde o `MemoryCortex` escreve o fallback local (default: `/tmp/vertice-cortex`).

## Validação (offline)
Testes adicionados/atualizados:
- `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x`
- `pytest tests/unit/test_thought_stream_splitter.py -v -x`

Resultados (neste ambiente):
- ✅ `tests/integration/test_agent_gateway_agui_stream.py` (8 passed)
- ✅ `tests/unit/test_thought_stream_splitter.py` (2 passed)

## Relatório Executivo (Resumo)
Entrega concluída do “Sistema Nervoso” do backend, mantendo estabilidade do protocolo AG-UI MVP e adicionando granularidade de frames para o frontend Narcissus:
- SSE multi-frame: intent/thought/code_delta/trajectory sem quebrar clientes existentes (envelope estável).
- Telemetria ADK: intent automático no início de `query()` + emissão no EventBus global.
- Thinking no provider Vertex (Gemini 3): suporte a thought parts com gating (redação por default).
- Persistência auditável: `code_delta` dispara persistência assíncrona na memória (AlloyDB se DSN estiver configurado).

Risco/controlos:
- Thought frames redigidos por padrão (`VERTICE_STREAM_THOUGHTS=0`) para evitar vazamento de raciocínio interno.
- Persistência de code_delta pode ser desligada para testes (`VERTICE_PERSIST_CODE_DELTAS=0`).

---
**Assinado,**
*Vertice-MAXIMUS*
*Garantindo que o stream não seja apenas rápido, mas inteligente.*

---

# 5. MCP ON CLOUD RUN (Infra Nervosa 100% Google)

Objetivo: colocar o **MCP Server real** (Prometheus interno) em Cloud Run com build reprodutível, empacotamento
packaging-safe e tool registry funcional, sem confundir com “Prometheus” comercial.

Status: ✅ Infra corrigida + validação local

Entregas:
- `Dockerfile.mcp` agora sobe o server real: `python -m vertice_core.prometheus.mcp_server.run_server`
- `cloudbuild.mcp.yaml` corrigido para usar `Dockerfile.mcp` no contexto `.` (raiz do monorepo)
- MCP server agora é **packaging-safe** (sem `sys.path.insert` e sem imports `prometheus.mcp_server.*`)
- ToolRegistry passa a carregar tools automaticamente (bootstrap no startup)
- Segurança: `enable_execution_tools` agora é **opt-in** via `MCP_ENABLE_EXECUTION_TOOLS=1`

Testes (offline, sem sockets neste ambiente):
- ✅ `pytest tests/unit/prometheus/test_mcp_server_http_smoke.py -v -x` (1 passed)

Relatório detalhado (audit + checklist Cloud Build/Run/Observability):
- `docs/google/MCP_CLOUD_RUN_INFRA_AUDIT_2026.md`

Pendências (testes “real cloud”, bloqueadas por DNS neste ambiente):
- Build/Push via Cloud Build + deploy em Cloud Run (dependem de DNS para APIs Google).
- Smoke tests online (`/health`, JSON-RPC `initialize`, `tools/list`) e verificação de logs/métricas no Cloud Monitoring.

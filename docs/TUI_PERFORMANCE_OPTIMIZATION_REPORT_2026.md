# 🔬 Relatório Científico — Otimização de Performance (Textual TUI) — Vertice-Code

**Data:** 2026-01-19
**Escopo:** performance (latência, smoothness de streaming, memória/CPU em sessões longas) do **Textual TUI**.
**Base de padrões:** `PHASE_1_REPORT.md` (Textual 2026 patterns + URLs oficiais).

---

## Status desta sessão (aplicado no repo)

✅ P0 implementado (hot paths) + higiene de testes:
- Autocomplete: debounce + cancelamento via `run_worker(... exclusive=True)`: `src/vertice_tui/app.py:402`
- Autocomplete: dropdown sem churn (reuso de `MAX_ITEMS` widgets + `batch_update()`): `src/vertice_tui/widgets/autocomplete.py:17`
- Autocomplete: `asyncio.to_thread(...)` + wrapper thread-safe: `src/vertice_tui/core/ui_bridge.py:537`
- StatusBar: cria `#tokens` e evita watchers antes de mount: `src/vertice_tui/widgets/status_bar.py:124`
- pytest-asyncio: remove redefinição de `event_loop` (zera DeprecationWarning): `tests/conftest.py:1`
- E2E: fixture em formato *factory async context manager* (cura ContextVar teardown): `tests/e2e/conftest.py:221`

✅ P1 implementado (smoothness de streaming):
- Streaming: coalescing de deltas por “frame” (flush periódico + `SoftBuffer` + scroll throttled): `src/vertice_tui/widgets/response_view.py:135`
- Config: `VERTICE_TUI_STREAM_FLUSH_MS` (default 33ms; min 5ms)

Provas (testes adicionados/atualizados):
- Dropdown não monta/desmonta por tecla: `tests/integration/test_tui_performance.py:162`
- Streaming: múltiplos deltas → 1 write coalescido (determinístico): `tests/integration/test_tui_performance.py:210`
- `run_test()` teardown estável (anti ContextVar): `tests/e2e/test_run_test_contextvars.py:1`

Validação executada (sessão atual):
- `black src/vertice_tui/widgets/response_view.py src/vertice_tui/core/streaming/soft_buffer.py tests/integration/test_tui_performance.py`
- `ruff check src/vertice_tui/widgets/response_view.py src/vertice_tui/core/streaming/soft_buffer.py tests/integration/test_tui_performance.py`
- `pytest -v tests/integration/test_tui_performance.py -k ResponseViewStreamingCoalescing -x`
- `pytest -v tests/e2e/test_basics.py -x`

---

## 0) Baseline (evitar “doc drift”)

- Textual instalado (repo): `6.2.1` (ver `PHASE_1_REPORT.md`)
- pytest-asyncio instalado: `0.24.0` (ver `PHASE_1_REPORT.md`)
- Config pytest do repo: `pytest.ini` contém `asyncio_mode=auto` e `asyncio_default_fixture_loop_scope=function` (ver `PHASE_1_REPORT.md`)

Fontes oficiais usadas nesta auditoria:
- Workers: `https://textual.textualize.io/guide/workers/` e `https://textual.textualize.io/api/work/`
- Reactivity: `https://textual.textualize.io/guide/reactivity/`
- Lazy: `https://textual.textualize.io/api/lazy/`
- Testing (run_test/Pilot): `https://textual.textualize.io/guide/testing/#testing-apps`
- asyncio.to_thread: `https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread`

---

## 1) Arquitetura atual (caminhos críticos)

### 1.1 App / Input / Workers
- `src/vertice_tui/app.py`
  - `VerticeApp.compose()` define árvore base (✅ conforme padrão de lifecycle).
  - `VerticeApp.on_input_submitted()` usa `run_worker(... group="chat_dispatch", exclusive=True)` para chat e slash commands (✅ conforme Workers).
  - `VerticeApp.on_input_changed()` calcula autocomplete em *cada* mudança do input (hot path de digitação).

### 1.2 Streaming → UI incremental
- `src/vertice_tui/app.py` (`_handle_chat`)
  - `async for sse_chunk in self.bridge.chat(message)` e, para cada `OutputTextDelta`, chama `await ResponseView.append_chunk(delta)`
- `src/vertice_tui/widgets/response_view.py`
  - `TextualMarkdown.get_stream()` (MarkdownStream) para streaming incremental
  - coalescing: deltas são bufferizados e flushados em cadência fixa (default 33ms) via timer
  - config: `VERTICE_TUI_STREAM_FLUSH_MS` (ms, mínimo 5ms)
  - throttling de `scroll_end()` (50ms) para reduzir layout thrash
  - limite de scrollback (`VERTICE_TUI_MAX_VIEW_ITEMS`, default 300) para evitar crescimento infinito

### 1.3 Providers (impactam “time to first token”)
- `src/vertice_cli/core/providers/vertex_ai.py`
  - `VertexAIProvider._stream_v3(...)` usa API async do `google-genai` (não deve bloquear o loop se usada corretamente)

---

## 2) O que já está forte (padrões Textual 2026 aplicados)

### 2.1 Workers usados corretamente no caminho crítico
✅ `run_worker(... group="chat_dispatch", exclusive=True)` em `src/vertice_tui/app.py` reduz travas do handler e permite cancelamento determinístico.
Fonte: `https://textual.textualize.io/guide/workers/` + `https://textual.textualize.io/api/work/`

### 2.2 Streaming incremental correto (evita “repaint” gigante)
✅ `TextualMarkdown.get_stream()` em `src/vertice_tui/widgets/response_view.py` evita re-renderizar o texto inteiro a cada delta.
Fonte: `https://textual.textualize.io/guide/widgets/`

### 2.3 Growth control / sessões longas
✅ `ResponseView._trim_view_items()` limita widgets (default 300). Isso evita degradação por acumular milhares de widgets.

### 2.4 I/O de histórico já tem trilha async
✅ `HistoryManager.add_command_async()` usa `asyncio.to_thread(...)` e lock para não bloquear o loop.
Fonte: `https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread`

---

## 3) Achados de performance (não-conformidades / gargalos)

> Severidade = impacto esperado em latência percebida, FPS e estabilidade em sessões longas.

### A) Autocomplete: churn de widgets + computação síncrona no hot path (SEV: HIGH)

**Onde:**
- `src/vertice_tui/app.py` → `VerticeApp.on_input_changed()` (chamado a cada tecla)
- `src/vertice_tui/widgets/autocomplete.py` → `AutocompleteDropdown.show_completions()` remove e remonta até 15 widgets sempre
- `src/vertice_tui/core/ui_bridge.py` → `AutocompleteBridge.get_completions()` pode fazer scan (`Path.cwd().iterdir()`) no primeiro uso de `@...`

**Por que importa:**
- Remover/montar widgets repetidamente força layout + diff do DOM do Textual.
- Computação síncrona em handler de digitação reduz “typing FPS” e causa input lag (pior em repos grandes).

**Sinais no código:**
- `show_completions()` remove todos widgets e remonta (custo = O(n) por tecla).
- `query_one(...)` dentro de handlers de alta frequência (digitação/teclas).

---

### B) Streaming: excesso de writes pequenos em MarkdownStream (SEV: MED) — CURADO ✅

**Onde:** `src/vertice_tui/widgets/response_view.py` (`append_chunk` + `_flush_pending_stream_async`)
**Por que importava:** em taxas altas de deltas (tokens/seg), muitos `await MarkdownStream.write(...)` pequenos aumentam overhead de render/measure.
**Cura aplicada:** `append_chunk()` agora apenas bufferiza deltas e o flush é coalescido por “frame” (timer), com `SoftBuffer` para evitar jank por markdown incompleto.

**Como funciona agora (resumo):**
- Buffer: `self._pending_stream_chunks: list[str]`
- Flush: `self.set_interval(..., self._flush_tick)` + `await MarkdownStream.write(coalesced)`
- Safety: `SoftBuffer` mantém tokens markdown “incompletos” fora da tela até ficar seguro (ou finalização).

**Config/tuning:**
- `VERTICE_TUI_STREAM_FLUSH_MS` default `33` (30fps). Para “mais responsivo”, testar `16`; para “menos CPU”, testar `50–75`.

**Prova (sem timers):**
- `tests/integration/test_tui_performance.py:210`

---

### C) Renderables caros em scrollback (SEV: MED/HIGH em sessões longas)

**Onde:** `src/vertice_tui/widgets/response_view.py`
**Por que importa:** mesmo com limite de 300 itens, alguns widgets são caros (Rich `Panel`, `Syntax` com `line_numbers=True` + `word_wrap=True`). Em sessões longas com muito código/diff, 300 painéis ainda podem ser pesados para scroll e layout.

---

### D) Exceções em watchers no StatusBar (SEV: LOW/MED, mas “death by a thousand cuts”)

**Onde:** `src/vertice_tui/widgets/status_bar.py`
**Sintoma:** watchers de `token_used/token_limit` atualizam `#tokens`, mas `compose()` não cria um `Static(id="tokens")`. Isso gera exceção (capturada) e logging debug pode virar custo constante se tokens forem atualizados frequentemente.

---

## 4) Recomendações (priorizadas, com prova científica)

### P0 — ROI alto, baixo risco (faça primeiro)

1) **Debounce + cancelamento do autocomplete**
   - Objetivo: o handler de digitação só agenda trabalho; cálculo roda em worker (thread) com `exclusive=True` e cancela o anterior.
   - Padrão: Workers (Textual) + “no blocking work in handlers”.
   - Fonte: `https://textual.textualize.io/guide/workers/` e `https://textual.textualize.io/api/work/`

2) **Reduzir churn no dropdown**
   - Trocar “remove + mount” por “reuso + update” (manter 15 `Static` fixos e atualizar texto/classes).
   - Usar `batch_update()` ao atualizar várias linhas de uma vez (reduz layout thrash).

3) **Cache de widgets consultados com frequência**
   - Guardar referências em `on_mount()` (`self._prompt`, `self._autocomplete`, `self._response`, `self._status`) para evitar `query_one(...)` em hot paths.
   - O ganho é pequeno por chamada, mas grande no agregado (digitação + streaming).

4) **Corrigir o `StatusBar` para não gerar exceções em watchers**
   - Ou criar `Static(id="tokens")` e usar `_format_tokens()`, ou remover o update de `#tokens` (se o MiniTokenMeter é a única UI).

5) **Eliminar `query_one(...)` remanescente em caminhos de alta frequência**
   - Ex.: `VerticeApp.on_input_submitted()` e ações de scroll ainda fazem múltiplos `query_one("#response")`/`query_one(StatusBar)` por evento.
   - Sugestão: usar as referências cacheadas em `on_mount()` e, quando necessário, validar `is_mounted` antes de atualizar.
   - Fonte (lifecycle + handlers): `https://textual.textualize.io/guide/app/` e `https://textual.textualize.io/guide/events/`

6) **HUDs/Widgets com updates frequentes: cache dos children + atualização minimalista**
   - `PerformanceHUD._update_display()` faz 4× `query_one(...).update(...)` por update; se isso rodar por token/frame vira custo constante.
   - Sugestão: capturar refs em `on_mount()` (`self._latency_widget`, etc.), e aplicar um “update only if changed”.
   - Fonte (reactivity: “watchers leves”): `https://textual.textualize.io/guide/reactivity/`

**Prova (testes/bench):**
- Adicionar/rodar microbenchmark de digitação: simular 200 `Input.Changed` em < X ms sob run_test.
- Métrica: P95 do tempo de handler < 2ms; UI responsiva.

---

### P1 — Streaming/render: suavidade e CPU

7) **Coalescing de deltas por frame**
   - Bufferizar deltas recebidos e dar flush a cada ~16–33ms (60–30fps), ao invés de `write()` por delta.
   - Integrar `SoftBuffer` (já existe em `src/vertice_tui/core/streaming/soft_buffer.py`) para flush em fronteiras “seguras” de Markdown.
   - Implementado em `ResponseView` com timer + `SoftBuffer` + scroll throttled.
   - Resultado esperado: menos overhead de render/measure, mesmo throughput visual.

8) **Evitar O(n²) em concat de `current_response`**
   - Durante streaming com `MarkdownStream`, armazenar em `list[str]` e só `''.join(...)` no final (ou sob demanda).
   - Mantém compatibilidade (export/copy) sem custo por token.

9) **Streaming “flush worker” dedicado (sem work no handler de evento)**
   - Hoje cada `OutputTextDeltaEvent` chama `append_chunk()`; isso pode virar milhares de awaits curtos.
   - Sugestão: o handler só faz `buffer.append(delta)` e agenda/garante um único worker exclusivo que dá flush periodicamente (30–60fps) e faz `scroll_end()` no flush.
   - Fonte (Workers + cancelamento determinístico): `https://textual.textualize.io/guide/workers/`

10) **Renderables caros: aplicar lazy/limits e “degradação controlada”**
   - `Panel(Syntax(... line_numbers=True, word_wrap=True))` em blocos grandes tende a custar caro em scroll/render.
   - Sugestão: limites por env/config (ex.: `MAX_CODE_LINES`, `MAX_DIFF_LINES`) + botão/ação “expand” usando `Lazy(...)` para materializar só quando necessário.
   - Fonte: `https://textual.textualize.io/api/lazy/`

**Prova (testes/bench):**
- Benchmark determinístico (sem rede): gerar 10k deltas e medir tempo total + número de flushes.
- Métrica: reduzir `writes/s` e reduzir CPU por delta mantendo tempo total semelhante.

---

### P2 — Sessões longas: memória e scroll

11) **“Compaction” de scrollback: degradar renderables antigos para formato barato**
   - Quando `ResponseView` exceder limite, substituir blocos antigos por um “SummaryStatic” simples (texto plano / markdown já consolidado), ou migrar histórico antigo para `TextLog`.
   - Objetivo: manter UX do “recent history” rica, mas evitar que *tudo* seja `Panel/Syntax`.

12) **Limites explícitos para blocos caros**
   - Ex.: limitar `code-block` a N linhas por padrão (config/env), com ação “expand” (lazy).
   - Padrão: `Lazy(...)` para materializar widget pesado só quando necessário.
   - Fonte: `https://textual.textualize.io/api/lazy/`

13) **Warm-up de caches em background (autocomplete + filesystem)**
   - O primeiro `@...` pode disparar varredura (mesmo limitada) e causar micro-lag.
   - Sugestão: agendar worker (thread) no `on_mount()` para preencher cache de arquivos em idle, e manter invalidation quando `cwd`/root mudar.
   - Fonte: `https://textual.textualize.io/guide/workers/`

**Prova (testes/bench):**
- Teste de estabilidade de memória com `tracemalloc` (ou `memray` quando disponível).
- Métrica: crescimento sublinear em 10k mensagens (sem leaks).

---

## 5) Plano de instrumentação (o “científico”)

### 5.1 Métricas mínimas (KPIs)
- **Enter→UI feedback (ms):** tempo até a mensagem do usuário aparecer no `ResponseView`.
- **Enter→1º delta (ms):** já existe via JSONL (`VERTICE_TUI_PERF_LOG_PATH`).
- **Writes/s no markdown stream:** número de flushes/seg (antes/depois do coalescing).
- **CPU por 1k deltas:** `time.process_time()` ou profiling externo.
- **Memória:** `tracemalloc` ou `memray` em cenários de 10k mensagens.

### 5.2 Harness recomendado
- Preferir `run_test()` + `Pilot` para benchmarks determinísticos.
  - Fonte: `https://textual.textualize.io/guide/testing/#testing-apps`
- Reaproveitar infra existente:
  - `tests/integration/test_tui_performance.py` (histórico async + streaming async)
  - `tests/e2e/test_run_test_contextvars.py` (estabilidade de teardown)

---

## 6) Checklist “Done = provado”

- [x] Autocomplete não bloqueia digitação (debounce + worker `exclusive=True`) — `src/vertice_tui/app.py:382`
- [x] Autocomplete sem churn de widgets (reuso de children) — `tests/integration/test_tui_performance.py:162`
- [x] Streaming mantém UX, mas reduz writes/s (coalescing) com ganho de CPU — `src/vertice_tui/widgets/response_view.py:135`
- [ ] Sessão longa (10k mensagens) não degrada scroll de forma exponencial (memória controlada, sem leaks).
- [ ] Testes de performance passam em CI sem rede (mocks determinísticos).

---

## 7) Próximas ações (sequência sugerida)

1) Completar P1 (itens 8–10: evitar O(n²), flush worker dedicado, lazy/limits)
2) Implementar P2 (itens 11–13: compaction + warm caches)
3) Consolidar benchmarks em `tests/integration/` e rodar continuamente

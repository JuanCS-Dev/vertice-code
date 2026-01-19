# 🔬 Textual TUI Performance Audit (Vertice TUI) — 2026
**Repo:** Vertice-Code (`src/vertice_tui/`)
**Date:** 2026-01-19
**Scope:** performance + responsiveness + long-session stability (render / reactivity / workers / lifecycle / memory).
**Input doc (Phase 1):** `PHASE_1_REPORT.md` (baseline Textual 6.2.1, pytest-asyncio 0.24.0).

> Este documento é um relatório de auditoria + backlog priorizado. Ele **não** implementa mudanças (PRs separadas), mas define o caminho mais científico para otimizar.

---

## 0) Padrões oficiais (Textual) usados como referência

Consolidado em `PHASE_1_REPORT.md`:
- App lifecycle / mounting: https://textual.textualize.io/guide/app/
- Workers (usar para tarefas longas / evitar bloquear a UI): https://textual.textualize.io/guide/workers/ + https://textual.textualize.io/api/work/
- Reactivity (watchers leves; evitar “refresh storm”): https://textual.textualize.io/guide/reactivity/
- Widgets / growth control (evitar crescimento infinito): https://textual.textualize.io/guide/widgets/
- Lazy instantiation (montagem tardia de widgets caros): https://textual.textualize.io/api/lazy/

Regra-guia (derivada dos guias acima):
1) **Nada bloqueante** (disk/network/CPU pesado) no **UI thread** nem em “workers async” (que rodam no mesmo event loop).
2) UI updates devem ser **batched** e **throttled** em caminhos de alta frequência (typing + streaming).

---

## 1) Executive Summary (P0/P1)

### P0 — maiores ganhos, menor risco
1) **Autocomplete**: hoje calcula completions e reconstrói widgets a cada tecla (UI thread) → input lag provável.
2) **Streaming markdown**: `ResponseView.append_chunk()` concatena string por delta (`+=`) e escreve no MarkdownStream por delta → risco de **O(n²)** + “update storm” com modelos rápidos.
3) **Comandos com I/O**: `/read`, `/add`, `/image`, `/pdf` etc fazem `Path.read_text()` / scanning / parsing síncronos dentro de handlers async → UI pode congelar apesar de `run_worker`.

### P1 — ganhos relevantes / mudanças moderadas
4) **Bridge init no on_mount**: `VerticeApp.on_mount()` acessa `self.bridge` (singleton pesado) antes de UI estar estável → tempo de startup e “first interaction delay”.
5) **Evitar exceções em watchers**: `StatusBar.watch_token_*` tenta atualizar `#tokens` (id não existe) → exceção/try/except em hot path se tokens forem atualizados frequentemente.

---

## 2) Observações objetivas (o que já está bom)

### 2.1 Render & scrollback
- `ResponseView` implementa **limite de scrollback** (`VERTICE_TUI_MAX_VIEW_ITEMS`, default 300) via `_trim_view_items()` → controla crescimento em sessões longas. (`src/vertice_tui/widgets/response_view.py`)
- Scroll throttling no stream: `scroll_end` no máximo 20fps (50ms) → reduz thrash de layout. (`src/vertice_tui/widgets/response_view.py`)

### 2.2 Streaming SSE resiliente
- Parsing incremental via `OpenResponsesParser.feed(line)` e fallback para linhas não‑SSE (evita sumir texto). (`src/vertice_tui/app.py`, `src/vertice_tui/core/openresponses_events.py`)

### 2.3 Workers já usados no caminho principal
- Chat/commands são disparados via `run_worker(..., group="chat_dispatch", exclusive=True)` para não travar handler de input. (`src/vertice_tui/app.py`)

---

## 3) Achados e recomendações (por componente)

### 3.1 `VerticeApp` (input + lifecycle)
**Arquivo:** `src/vertice_tui/app.py`

**Achado A — Autocomplete no UI thread**
- `on_input_changed()` chama `self.bridge.autocomplete.get_completions(...)` diretamente e atualiza o dropdown a cada tecla.
- `get_completions()` pode fazer scanning (modo `@`) e fuzzy scoring; mesmo com limites/caches, o pior caso é visível em repos grandes.

**Recomendação A (P0) — Debounce + offload + stale-guard**
- Debounce (ex.: 75–150ms) para typing rápido.
- Offload da computação de completions (principalmente `@`) com `await asyncio.to_thread(...)`.
- Stale-guard: aplicar resultado **somente** se o input atual ainda for o mesmo (evita “autocomplete atrasado”).
- Use `run_worker(..., group="autocomplete", exclusive=True)` para cancelamento determinístico (padrão Workers).

**Achado B — Bridge init pode bloquear**
- `on_mount()` usa `self.bridge` várias vezes (status, dashboard, mensagens iniciais) antes de disparar `bridge.warmup()` (que é background).

**Recomendação B (P1) — Startup em 2 fases**
- Fase 1 (rápida, síncrona): montar UI + banner + focus prompt.
- Fase 2 (worker): `bridge = await asyncio.to_thread(get_bridge)`; depois atualizar StatusBar/TokenDashboard e disparar warmup.
- UI deve mostrar estado “Loading bridge…” até fase 2 concluir.

---

### 3.2 `ResponseView` (streaming / render)
**Arquivo:** `src/vertice_tui/widgets/response_view.py`

**Achado A — concatenação O(n²)**
- `append_chunk()` faz `self.current_response += chunk` por delta, mesmo quando usa `TextualMarkdown.get_stream()` (onde o stream já mantém o estado do render).

**Recomendação A (P0) — Buffer + flush em frequência fixa**
- Trocar `current_response` por **buffer de chunks** (lista/deque) durante streaming.
- “Flush” no máximo 20–30fps (ex.: a cada 33–50ms):
  - juntar chunks (`"".join(buffer)`) e fazer **uma** escrita no MarkdownStream.
  - manter `current_response` apenas no final (via `response.output_text.done`) ou quando necessário (copy/export).
- Resultado esperado: menos repaints, menos GC, throughput mais estável.

**Achado B — `end_thinking()` chamado redundante**
- `ResponseView.handle_open_responses_event()` chama `await end_thinking()` em `response.completed`.
- `VerticeApp._handle_chat()` chama `await view.end_thinking()` no `finally`.

**Recomendação B (P2) — single “finalizer”**
- Definir um único ponto de finalização (UI) para reduzir trabalho duplicado e simplificar invariantes.

---

### 3.3 Autocomplete UI (dropdown)
**Arquivo:** `src/vertice_tui/widgets/autocomplete.py`

**Achado — remount em loop**
- `show_completions()` remove e remonta até 15 widgets a cada update.

**Recomendação (P0) — reciclar widgets**
- Pré-criar N itens (15) no `on_mount`/`compose`, e somente:
  - `update(text)`
  - alternar classes (`selected`, `item-tool`, etc)
  - mostrar/esconder itens não usados
- Evita churn de mount/layout e reduz custo por keystroke.

---

### 3.4 Autocomplete “engine” (file scan / fuzzy)
**Arquivo:** `src/vertice_tui/core/ui_bridge.py` (`AutocompleteBridge`)

**Achado — scanning de arquivos é síncrono**
- `_scan_files()` percorre diretórios e faz `iterdir()`/`is_dir()`/`is_file()` no caminho crítico do autocomplete `@`.
- Mesmo com `MAX_FILES=300` e `MAX_DEPTH=4`, isso pode travar em FS lento / repo grande.

**Recomendação (P0)**
- Pre-warm do cache em background (`bridge.warmup()` ou worker dedicado).
- Offload do primeiro scan com `asyncio.to_thread(self._scan_files)`.
- Cache incremental por query (último `@query` → resultados) para evitar sort/scoring completo a cada tecla.

---

### 3.5 Command handlers (I/O e operações pesadas)
**Arquivos principais:**
- `src/vertice_tui/app.py` (`_read_file`)
- `src/vertice_tui/handlers/basic.py` (`/read`)
- `src/vertice_tui/handlers/context_commands.py` (`/add`)
- `src/vertice_tui/core/context/file_window.py` (`FileContextEntry.from_file`)
- `src/vertice_tui/handlers/operations.py` (`/image`, `/pdf`, etc)

**Achado — “async” com I/O síncrono ainda bloqueia**
- Muitos handlers são `async def`, mas fazem `Path.read_text()` e outras operações síncronas (disk).
- Como os “workers” do Textual são async por padrão, isso **continua** bloqueando o event loop quando executado dentro deles.

**Recomendação (P0)**
- Padronizar: qualquer disk I/O / CPU pesado em handlers → `await asyncio.to_thread(...)`.
- Para operações muito pesadas, usar `run_worker(..., group="ops", exclusive=False)` + progress UI.

---

### 3.6 StatusBar (watchers / hot path)
**Arquivo:** `src/vertice_tui/widgets/status_bar.py`

**Achado — exceções em watchers**
- `watch_token_used()` / `watch_token_limit()` chamam `_update_element("#tokens", ...)`, mas o widget `#tokens` não existe no `compose()`. Isso gera exceção e logging (mesmo que debug), o que é custo desnecessário.

**Recomendação (P1)**
- Ajustar watchers para atualizar apenas elementos existentes (ou adicionar o elemento faltante).
- Evitar `try/except` em caminho quente onde updates podem ser frequentes.

---

### 3.7 InputArea (TextArea / language detection)
**Arquivo:** `src/vertice_tui/widgets/input_area.py`

**Achado — custo por tecla cresce com texto**
- `_detect_language()` faz múltiplos `in` sobre o texto completo.
- `_update_status()` faz `len(text.split("\n"))` a cada mudança.

**Recomendação (P2)**
- Limitar detecção a um “window” (ex.: primeiros/últimos 2–4k chars) em vez do buffer inteiro.
- Contar linhas com `text.count("\\n") + 1` para reduzir alocações.
- Debounce de status/language para typing rápido (mesmo timer do autocomplete, se houver).

---

## 4) Backlog priorizado (mudanças pequenas, mensuráveis)

| ID | Prioridade | Área | Mudança proposta | Métrica-alvo | Validação |
|---:|:--:|---|---|---|---|
| 1 | P0 | Autocomplete | Debounce + `to_thread` + stale-guard + worker `group="autocomplete"` | p95 keystroke→UI < 30ms | benchmark typing + log timings |
| 2 | P0 | Autocomplete UI | Reutilizar 15 itens (sem remove/mount) | 0 “stutter” ao digitar rápido | manual + profiler |
| 3 | P0 | Streaming | Buffer de chunks + flush 30–20fps; remover `+=` por delta | CPU estável; menos GC | ChatPerf + throughput |
| 4 | P0 | Commands I/O | `to_thread` em `/read`, `/add`, `/image`, `/pdf` etc | UI não congela em arquivo grande | teste manual + unit mocks |
| 5 | P1 | Startup | Bridge init em background + UI “loading” | first paint < 200ms | medição `t_submit_to_worker` e tempo de mount |
| 6 | P1 | StatusBar | Remover exceções em watchers (id inexistente) | 0 exceções no hot path | pytest + log sem erros |
| 7 | P2 | InputArea | Otimizar detecção/status | typing estável em inputs grandes | benchmark local |

---

## 5) Plano científico de validação (antes/depois)

### 5.1 Métricas mínimas (sem novas deps)
1) **Latência de streaming (já existe):** `VERTICE_TUI_PERF_LOG_PATH=/tmp/vertice_tui_perf.jsonl`
   - `t_submit_to_worker_ms` (p95)
   - `t_submit_to_first_text_delta_ms` (p95)
   - `t_total_ms`
2) **Autocomplete timing:** adicionar logging (debug/JSONL) para:
   - tempo de `get_completions` (ms)
   - tempo de atualização do dropdown (ms)
3) **Estabilidade de sessão longa:** registrar:
   - `len(ResponseView.children)` (depois do trim)
   - tempo de `append_chunk` (ms) em p95/p99 (amostragem)

### 5.2 Benchmarks recomendados (scripts locais)
- **Typing benchmark:** simular 200–500 eventos Input.Changed com strings crescentes; medir p95.
- **Streaming benchmark:** stream artificial com 10k deltas pequenos vs 1k deltas maiores; comparar CPU/tempo total.
- **Scrollback benchmark:** montar 1k mensagens e confirmar que o trim mantém responsivo (limit 300).

### 5.3 Critérios de aceitação (pragmáticos)
- 0 congelamentos perceptíveis durante:
  - digitação rápida com autocomplete ligado
  - `/read` de arquivo “grande” (ex.: 1–5MB)
  - `/add src/**/*.py` (limitado a 10 arquivos)
- `t_submit_to_first_text_delta_ms` sem spikes (p99 consistente).

---

## 6) Próximos passos (sequência ideal de PRs)
1) PR-1 (P0): Autocomplete (debounce/offload + dropdown recycle) + benchmark typing.
2) PR-2 (P0): ResponseView streaming buffer/flush + benchmark streaming.
3) PR-3 (P0): `to_thread` para disk I/O em handlers (`/read`, `/add`, `/image`, `/pdf`) + smoke tests.
4) PR-4 (P1): Bridge init em background + métricas de startup.
5) PR-5 (P1/P2): StatusBar watchers + InputArea micro-optimizações.

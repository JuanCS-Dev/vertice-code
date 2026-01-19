# Relatório técnico — UI Lag & Streaming (Vertice TUI / Textual)
**Projeto:** Vertice-Code
**Data:** 2026-01-18
**Objetivo:** eliminar o lag (~5s) entre `Enter` e feedback visual/primeiros tokens, corrigir o “streaming cuspido” e estabilizar a TUI para uso diário.

> Nota: este relatório foi produzido a partir da inspeção do codebase local (sem pesquisa web nesta sessão).

---

## 1) Status (o que já melhorou / o que ainda trava)

✅ Já aplicado (no codebase):
- Input retorna rápido e o processamento roda em **Workers** (UI responde imediatamente).
- UI ficou resiliente a chunks “não‑SSE” (não some mais texto emitido fora do protocolo SSE).
- Streaming incremental do Markdown via `TextualMarkdown.get_stream()` (menos repaint) + scroll throttling.
- Warmup em background (tools/provider/system_prompt) + cache do system prompt com stale‑while‑revalidate.
- Instrumentação JSONL de latências (submit→worker, submit→primeiro SSE/delta, total) + scripts de diagnóstico.

🧨 Ainda pendente (causas-raiz que explicam o lag/“stutter”):
- I/O síncrono no histórico (disk write) no começo do chat.
- Streaming Vertex AI (v3/google‑genai) ainda itera um generator **bloqueante** no event loop.
- Inicialização do client Vertex (`genai.Client(...)`) pode bloquear o event loop (ADC/auth/imports).

---

## 2) Mapa do data‑flow (fim‑a‑fim)

### 2.1 Input → Worker (UI thread)
- `src/vertice_tui/app.py:257` (`on_input_submitted`)
  - Sanitiza, limpa prompt, monta mensagem do usuário no `ResponseView`.
  - Dispara processamento via `self.run_worker(..., group="chat_dispatch", exclusive=True)` e chama `self.refresh()`.

### 2.2 Worker → Bridge → ChatController
- `src/vertice_tui/app.py:462` (`_handle_chat_with_timeout`) → `src/vertice_tui/app.py:505` (`_handle_chat`)
- `_handle_chat` consome `async for sse_chunk in self.bridge.chat(message)`:
  - `src/vertice_tui/core/bridge.py:680` (`Bridge.chat`)
    - validação + `await asyncio.sleep(0)` (yield cedo para UI)
    - tool schema em executor quando necessário
    - seleciona provider (`ProviderManager.get_client`)
    - `system_prompt` via cache/refresh assíncrono
    - delega para `src/vertice_tui/core/chat/controller.py:345` (`ChatController.chat`)

### 2.3 Streaming (Open Responses / SSE) → Parser → UI incremental
- `src/vertice_tui/app.py:505` alimenta `OpenResponsesParser.feed(line)` (SSE linha‑a‑linha)
- `src/vertice_tui/widgets/response_view.py:257` (`handle_open_responses_event`) → `OpenResponsesOutputTextDeltaEvent` → `append_chunk(delta)`
- `src/vertice_tui/widgets/response_view.py:214` (`append_chunk`)
  - streaming incremental via `MarkdownStream.write()` (evita `update()` de texto gigante por token)
  - scroll throttled (50ms) para evitar thrash de layout

---

## 3) O que foi feito (mudanças aplicadas)

### 3.1 `src/vertice_tui/app.py`
- `on_input_submitted` (`src/vertice_tui/app.py:257`):
  - migrado para **Worker API** para chat e para `/commands` (retorno rápido do handler).
  - `self.refresh()` após adicionar mensagem do usuário.
  - `ChatPerf` + logging JSONL (env `VERTICE_TUI_PERF_LOG_PATH`).
- `_handle_chat` (`src/vertice_tui/app.py:505`):
  - `view.start_thinking()` + `await asyncio.sleep(0)` para feedback imediato.
  - **passthrough não‑SSE**: linhas que não são `event:`/`data:` e não são vazias viram `await view.append_chunk(line)`.

### 3.2 `src/vertice_tui/widgets/response_view.py`
- `append_chunk` virou `async` (`src/vertice_tui/widgets/response_view.py:214`) e passou a usar `TextualMarkdown.get_stream()`.
- `handle_open_responses_event` virou `async` (`src/vertice_tui/widgets/response_view.py:257`) para propagar `await`.
- Limite de scrollback (`_trim_view_items`) com env `VERTICE_TUI_MAX_VIEW_ITEMS` para evitar degradação em sessões longas.
- `end_thinking` faz flush do `MarkdownStream.stop()` para fechar fragments pendentes.

### 3.3 `src/vertice_tui/core/bridge.py`
- `warmup()` em background (`src/vertice_tui/core/bridge.py:416`) para:
  - tool schemas (`_configure_llm_tools`) em executor
  - provider default em executor
  - build/cache do system prompt sem travar UI
- System prompt:
  - build sync isolado em `_build_system_prompt_sync` (`src/vertice_tui/core/bridge.py:547`)
  - build async com `asyncio.to_thread` + lock + TTL (`VERTICE_SYSTEM_PROMPT_TTL_S`) + stale‑while‑revalidate (`src/vertice_tui/core/bridge.py:638`)
- `Bridge.chat` (`src/vertice_tui/core/bridge.py:680`) dá yield cedo (`await asyncio.sleep(0)`) e configura tools em executor quando necessário.

### 3.4 `src/vertice_tui/core/agentic_prompt.py`
- `get_dynamic_context` (`src/vertice_tui/core/agentic_prompt.py:211`):
  - `git status --porcelain -uno` (ignora untracked) + timeouts curtos via env `VERTICE_GIT_CONTEXT_TIMEOUT_S`.
  - objetivo: não travar o build do system prompt em repos grandes (untracked explode custo do `git status`).

### 3.5 Ajustes de compatibilidade (async append)
- `src/vertice_tui/handlers/agents.py` e `src/vertice_tui/handlers/a2a.py` atualizados para `await view.append_chunk(...)` e `await view.end_thinking()`.

### 3.6 Scripts de diagnóstico adicionados
- `tests/benchmarks/diagnose_enter_lag.py`
- `tests/benchmarks/diagnose_bridge_overhead.py`
- `tests/benchmarks/diagnose_inspect_overhead.py`
- `tests/benchmarks/reproduce_input_lag.py`

---

## 4) Achados (causas‑raiz do lag/streaming)

### 4.1 Worker não salva a UI se o worker bloquear o event loop
Textual Worker roda no mesmo event loop por padrão: qualquer I/O síncrono (disk/network) dentro do worker “congela” a UI.

### 4.2 I/O síncrono no histórico antes do streaming começar (lag antes do 1º token)
- `src/vertice_tui/core/history_manager.py:99` (`_save_history`) usa `Path.write_text(...)` (sync).
- `src/vertice_tui/core/history_manager.py:106` (`add_command`) chama `_save_history()` no caminho crítico.
- `src/vertice_tui/core/chat/controller.py:370` (`ChatController.chat`) chama `self.history.add_command(message)` antes do stream.

Efeito: qualquer lentidão de disco ou arquivo grande “come” o budget de latência do 1º token.

### 4.3 Vertex AI v3: generator bloqueante iterado no event loop (streaming “cuspido” + freeze)
- `src/vertice_cli/core/providers/vertex_ai.py:170` (`_stream_v3`) cria `generate_content_stream(...)` em executor, mas faz:
  - `for chunk in stream_iter:` no event loop.

Se `next(stream_iter)` bloquear (network), a UI trava; tokens chegam “em blocos” quando o loop destrava.

### 4.4 Inicialização de client/provider pode bloquear
- `src/vertice_cli/core/providers/vertex_ai.py:82` (`_init_genai_client`) é sync e pode fazer trabalho pesado (ADC/auth/import).
Mesmo com `run_worker`, isso roda no loop e pode atrasar o feedback inicial.

---

## 5) O que ainda precisamos fazer (para “zerar” o UI lag)

### 5.1 CRÍTICO: tornar histórico não‑bloqueante
Meta: `HistoryManager.add_command()` nunca fazer disk I/O no caminho crítico.
- Implementar flush em background com `asyncio.to_thread(...)` + lock (evitar writes concorrentes).
- Alternativa: buffer em memória e salvar por debounce (ex.: a cada N comandos ou a cada X segundos).

### 5.2 CRÍTICO: tornar streaming Vertex AI realmente assíncrono
Meta: nenhum `next()` de stream bloqueante no event loop.
- Opção A (preferível): usar API async do SDK (se disponível) para stream.
- Opção B: iterar o generator em thread e repassar para o async via `asyncio.Queue` (backpressure + cancelamento).
- Também mover `_init_genai_client()` para executor/to_thread quando rodar sob TUI.

### 5.3 Ajustar testes para não “pegar rede” por acidente
Hoje alguns testes mockam `bridge.llm.stream`, mas o caminho real usa `Bridge.chat()`/Open Responses.
- Atualizar testes para mockar `Bridge._get_client()` e devolver um client fake que gera SSE determinístico.

### 5.4 Adicionar teste “REAL” com Vertex AI (sem mocks)
Criar teste de integração guardado por env (ADC + `GOOGLE_CLOUD_PROJECT`):
- Assert: chega **primeiro chunk** antes de um timeout e chegam **múltiplos chunks** (não 1 blob).

---

## 6) Como medir/validar (comandos e métricas)

### 6.1 Log de performance da TUI (JSONL)
- Set `VERTICE_TUI_PERF_LOG_PATH=/tmp/vertice_tui_perf.jsonl`
- Rodar a TUI e enviar prompts; analisar:
  - `t_submit_to_worker_ms` (meta: <200ms)
  - `t_submit_to_first_text_delta_ms` (meta: consistente, sem spikes de 5s)

### 6.2 Testes rápidos (sem rede)
- `pytest tests/unit/ -v -x --timeout=60`

### 6.3 Teste real Vertex AI (com rede/ADC)
- Pré‑req: `GOOGLE_CLOUD_PROJECT` definido e ADC funcionando.
- Rodar somente os testes de integração Vertex (quando existirem): `pytest -m integration -k vertex_ai -v --timeout=120`

---

## 7) Variáveis de ambiente relevantes
- `VERTICE_TUI_PERF_LOG_PATH`: escreve métricas JSONL por request.
- `VERTICE_TUI_MAX_VIEW_ITEMS`: limita scrollback (default 300).
- `VERTICE_SYSTEM_PROMPT_TTL_S`: TTL do system prompt (default 60s).
- `VERTICE_GIT_CONTEXT_TIMEOUT_S`: timeout de git context (default 0.25s).

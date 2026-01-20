# Vertice-Code: MCP Skills Architecture & Code Agent Best Practices (Report)

**Data:** 2026-01-20
**Escopo realista (dado tempo/IO):** Phase 0 (codebase) completa em nível arquitetural + gaps e roadmap com referência a arquivos; Phase 1 (mercado) referenciada a pesquisas internas já existentes, com recomendações acionáveis.

---

## 1. Executive Summary

O `vertice-code` é um stack Python 3.11+ com **CLI (Typer/Rich)** + **TUI (Textual)** e uma camada de **Tools/Agents** que tenta oferecer “Claude Code parity” (slash commands, contexto, execução, etc.). MCP existe, mas hoje está **fragmentado** em pelo menos **dois caminhos** (TUI `MCPManager` e CLI `integrations/mcp/*`) e, no modo server atual, **não expõe a maior parte dos tools** do registry (por limitação de assinatura/schema).

**Forças**
- TUI sólida e responsiva: execução em background (`run_worker`), streaming SSE “Open Responses” no `ResponseView`, autocomplete, perf logs.
- Bridge (facade) com “graceful degradation” por fases (componentes críticos vs opcionais).
- Tool system interno organizado por categorias (file/terminal/git/web/parity) e execução com validação via `_execute_validated`.

**Fraquezas críticas (impacto imediato)**
- MCP server atual registra basicamente **shell tools** (+ Prometheus/Daimon), não o set completo do `ToolRegistry`. (`src/vertice_cli/integrations/mcp/tools.py`)
- Há indícios de **inconsistências/bugs** em entry points MCP e execução de tools (ex.: `serve` chama `run_async` em função sync; `cli_mcp.py` importa símbolo não exportado; `MCPClient.call_tool` aguarda `execute()` mesmo quando pode ser sync). (`src/vertice_cli/main.py`, `src/vertice_cli/cli_mcp.py`, `src/vertice_cli/core/mcp.py`)
- Duas (ou mais) “fontes de verdade” para MCP/adapters/gateway/manager geram drift e tech debt.

---

## 2. Project Structure (alto nível)

**Entrypoints (Python)**
- `vertice`, `vtc`, `vertice-cli` → `vertice_cli.main:cli_main` (`pyproject.toml`)

**Diretórios relevantes ao “code agent”**
- `src/vertice_cli/` — CLI, tool system, agentes (muitos), integrações (incl. MCP via FastMCP).
- `src/vertice_tui/` — TUI Textual, Bridge/facades, handlers de slash commands, streaming adapter.
- `src/agents/` — “core agents” (orchestrator/coder/reviewer/etc.) apontados no registry do TUI.
- `skills/` — skills em markdown (ex.: `git-ops`, `code-review`, `code-generation`) usadas como “policy/procedimento”.
- `tests/` — suíte grande (unit/integration/e2e/etc.).

**Infra/deploy (sinais)**
- `Dockerfile*`, `docker-compose.yml`, `cloudbuild*.yaml`, `k8s/`, `terraform/`, `istio-1.28.2/`.
- Repositório também contém frontend/webapp (`frontend/`, `vertice-chat-webapp/`, etc.) — fora do foco deste relatório, mas afeta contexto e discovery de tools.

---

## 3. CLI/TUI Implementation (Phase 0)

### 3.1 CLI (Typer)

**Arquivo:** `src/vertice_cli/main.py`
**Papel:** entrypoint unificado com modos:
- default → TUI (`_run_tui()` → `vertice_cli.ui_launcher.launch_tui()`)
- headless (`-p/--prompt`) → `_run_headless()` usa Bridge para streaming de resposta
- subcommands: `serve`, `shell`, `chat`, `status`, `agents`, `tools`

**Padrões**
- “Lazy imports” para reduzir ciclos (`vertice_cli/ui_launcher.py`).
- Headless coleta streaming e pode emitir `json` / `stream-json` / `text`.

**Debt/risco observado**
- `serve()` chama `run_async(mcp_main())`, mas `cli_mcp.main()` é sync e retorna `None` (quebra em runtime). (`src/vertice_cli/main.py`)

### 3.2 TUI (Textual)

**Arquivo:** `src/vertice_tui/app.py`
**Papel:** UI principal (Header/ResponseView/Input/Autocomplete/StatusBar/TokenDashboard).

**Fluxo de interação (usuário → resposta)**
1. `on_input_submitted()` valida/sanitiza input, salva histórico, atualiza UI e dispara worker.
2. Se começa com `/` → `_handle_command()` → `CommandRouter.dispatch()` → handlers por domínio.
3. Caso contrário → `_handle_chat_with_timeout()` → `_handle_chat()`:
   - Consome `bridge.chat(message)` (SSE Open Responses + fallback texto)
   - `OpenResponsesParser` transforma eventos e `ResponseView` renderiza incrementalmente.

**State management**
- UI state: `reactive is_processing`, `StatusBar.mode`, histórico local (até 1000 itens), controle de operações concorrentes (até 3).
- `Bridge` centraliza estado de tools/agents/history/governance/providers.

**Command structure**
- Slash commands roteados por `src/vertice_tui/handlers/router.py` em handlers:
  - `basic`, `agents`, `session`, `operations`, `context_commands`, `claude_parity`, `a2a`, `autoaudit`.

---

## 4. MCP Implementation (Phase 0)

### 4.1 Onde MCP aparece hoje

**(A) TUI MCP lifecycle**
- `src/vertice_tui/core/managers/mcp_manager.py`
  - Start/stop de “server local”
  - “connect_external” é placeholder (sem client real; tools importados vazios)
  - Inicializa server via `vertice_cli.integrations.mcp.server.QwenMCPServer`

**(B) CLI MCP server (FastMCP)**
- `src/vertice_cli/integrations/mcp/server.py`
  - Usa `fastmcp.FastMCP`
  - Transport atual: `stdio` (hard-coded no `start()`)
  - Registra:
    - `MCPToolsAdapter` (mas ele só registra shell tools)
    - `DaimonMCPAdapter` (sempre)
    - `PrometheusMCPAdapter` (opcional)

**(C) Tool execution adapter chamado “MCPClient” (interno)**
- `src/vertice_cli/core/mcp.py`
  - É um adapter do `ToolRegistry` usado pelos agentes (não é MCP protocol real).
  - Implementa circuit breaker e timeouts.

### 4.2 Registro/descoberta de tools via MCP server (estado atual)

**Arquivo:** `src/vertice_cli/integrations/mcp/tools.py`
**Achado chave:** comentário explícito:
- “CLI tools usam `**kwargs` que MCP não suporta”
- portanto: “Only shell tools have explicit signatures and can be registered”

Resultado prático:
- MCP server (hoje) expõe `create_shell`, `execute_shell`, `close_shell`, `list_shell_sessions`
- + tools do Prometheus adapter (se ativo)
- + tools do Daimon adapter
- **não expõe** file ops / search / git / etc diretamente via MCP protocol.

### 4.3 Fluxo atual de execução (TUI → tools)

**Caminho dominante hoje (sem MCP):**
`TUI (VerticeApp)` → `Bridge.chat()` → `ChatController/ToolBridge.execute_tool()` → `vertice_cli.tools.*`

**MCP serve mode (quando funciona):**
MCP client externo → `FastMCP` → shell/prometheus/daimon tools

---

## 5. Skills/Tools Inventory (Phase 0)

### 5.1 “Skills” (policy/procedimento)
- `skills/git_ops/SKILL.md` — commit/branch/PR/conflitos
- `skills/code_review/SKILL.md` — checklist de review (segurança/perf/qualidade)
- `skills/code_generation/SKILL.md` — padrão de geração de código + scripts/references

### 5.2 Tool system (implementação)

**Base/registry**
- `src/vertice_cli/tools/base.py` — `BaseTool`, `ToolRegistry`, `ToolResult`
- `src/vertice_cli/tools/registry_helper.py` — registry “pequeno” (file ops + search + git status/diff + terminal + prometheus subset)
- `src/vertice_cli/tools/registry_setup.py` — factory “curada” + cria `MCPClient` interno

**TUI carrega tools via**
- `src/vertice_tui/core/tools_bridge.py` — carrega ~47 tools (file/terminal/exec/search/git/context/web/parity)

### 5.3 Agents

**Registro central**
- `src/vertice_tui/core/agents/registry.py` — ~20 agents (14 “CLI agents” + 6 “core agents”)

**Risco**
- Alguns `module_path`/`class_name` parecem inconsistentes com a árvore atual (provável drift). Ex.: `vertice_cli.agents.planner` não aparece no `find` de arquivos (validar).

---

## 6. Pain Points & Technical Debt (Phase 0)

### Críticos
1. **MCP “de verdade” não está alinhado com ToolRegistry**: não há geração de wrappers com schema/assinatura tipada para expor tools via MCP server. (`src/vertice_cli/integrations/mcp/tools.py`)
2. **Entry point MCP parece quebrado**:
   - `src/vertice_cli/cli_mcp.py` importa `run_mcp_server` de `vertice_cli.integrations.mcp`, mas `__init__.py` não exporta esse símbolo.
   - `src/vertice_cli/main.py:serve()` executa `run_async(mcp_main())` contra função sync.
3. **Dualismo MCP**: `vertice_tui` tem `MCPManager` e `vertice_cli` tem `MCPGateway`/adapters/servidor — mas o servidor real não usa o gateway unificado.

### Estruturais
- Múltiplos registries/factories (ToolBridge vs registry_helper vs registry_setup) podem divergir em tool sets.
- “MCPClient” interno é um adapter de ToolRegistry; o nome colide com “MCP protocol” e confunde arquitetura.
- `MCPManager.connect_external()` é placeholder; não há discovery/import real de tools remotos.

---

## 7. Market Research (Phase 1) — usando pesquisas internas já no repo

Este repositório já contém pesquisas relevantes em `docs/research/`:
- `docs/research/PHASE_2_2_INTEGRATION_RESEARCH.md` — tool registry/execution (Copilot CLI, Cursor, Claude Code)
- `docs/research/PHASE_3_2_WORKFLOW_RESEARCH.md` — workflow orchestration (dependency graph, checkpoints, rollback)
- `docs/research/PHASE_4_INTELLIGENCE_RESEARCH.md` — suggestion engine (context fusion, ranking)

**Síntese aplicável ao vertice-code (direto ao ponto)**
- Adotar **permission model defense-in-depth** por tool + por argumento + por sessão (e “trust levels”).
- Migrar de “registry estático” para **tool discovery dinâmico** (ex.: detectar `package.json`, `Dockerfile`, `pyproject.toml` e habilitar tools/context específicos).
- Implementar **checkpoint/rollback transaction log** para edições multi-arquivo.

---

## 8. Gap Analysis (Phase 2) — matriz resumida

| Capability | vertice-code (hoje) | “market pattern” (pesquisas internas) | Prioridade |
|---|---|---|---|
| MCP tool exposure completo | Parcial (shell + adapters) | Tools tipados + schema + wrappers | Alta |
| External MCP connections | Placeholder | Client real + import/list tools | Alta |
| Permission model | Existem sinais (sandbox/governance), mas disperso | Allow/deny + approvals + session trust | Alta |
| Workflow orchestration | Existe (plan/parallel/executor) | DAG + checkpoints + rollback | Média |
| Tool discovery dinâmica | Majoritariamente estático | Context-based discovery | Média |
| Observability | Logging/perf JSONL no TUI | tracing + audit timeline | Média |

---

## 9. Implementation Roadmap (Phase 3) — específico para arquivos do vertice-code

### Semanas 1–2: MCP “Single Source of Truth”
1. **Unificar a superfície MCP**
   - Fonte: `src/vertice_tui/core/managers/mcp_manager.py` (lifecycle)
   - Server: `src/vertice_cli/integrations/mcp/server.py`
   - Gateway: `src/vertice_cli/integrations/mcp/gateway.py`
   - Meta: o server **usar o gateway** (ou remover gateway, escolhendo 1 caminho).

2. **Corrigir entrypoint MCP**
   - `src/vertice_cli/cli_mcp.py` (exports/imports)
   - `src/vertice_cli/main.py` (serve mode: não chamar `run_async()` em função sync; ou tornar async de verdade)

3. **Exposição automática de tools via MCP**
   - Implementar “wrapper generator” que lê `BaseTool.get_schema()` e cria funções com assinatura estática compatível com FastMCP.
   - Alvo: `src/vertice_cli/integrations/mcp/tools.py`
   - Testes: `tests/cli/` ou `tests/integration/` criando server local e listando tools registrados.

### Semanas 3–4: Skills essenciais (Git + FS + Exec) via MCP
1. Expandir adapters MCP para:
   - file ops: `src/vertice_cli/tools/file_ops.py`, `src/vertice_cli/tools/file_mgmt.py`
   - search: `src/vertice_cli/tools/search.py`
   - git: `src/vertice_cli/tools/git_ops.py` (e/ou `src/vertice_cli/tools/git/*`)
2. Integrar listagem/uso no TUI:
   - `src/vertice_tui/handlers/claude_parity.py` (comandos `/mcp tools`, etc.)
   - `src/vertice_tui/core/managers/mcp_manager.py` (import real de tools remotos)

### Semanas 5–6: Segurança/Reliability
1. Permission gates unificados antes de executar tools “dangerous”
   - Centralizar decisão em 1 módulo (ex.: `src/vertice_tui/core/governance.py` + `src/vertice_tui/core/safe_executor.py`)
2. Rate limits/timeouts por tool no MCP server (não só no client interno)

### Semanas 7–8: DX e Qualidade
1. Documentar “MCP contract” (schemas, tool naming, error envelope) em `docs/architecture/`.
2. Criar template de MCP server + testes de conformidade (list_tools, call_tool, error shape).

---

## 10. Checklist de validação (para quando começar a codar)
- `pytest tests/unit/ -v -x --timeout=60`
- Smoke test de server MCP: `python -c "from vertice_cli.integrations.mcp.server import QwenMCPServer; print('ok')"`
- Rodar TUI: `vtc` e testar `/mcp status`, `/tools`, execução de um tool exposto via MCP.

---

## 11. Próximos passos sugeridos (precisa confirmação)
1. Eu implemento as correções mínimas de entrypoint (`cli_mcp.py` + `main.py:serve`) e adiciono 1 teste de smoke.
2. Eu implemento o gerador de wrappers MCP a partir de `BaseTool.get_schema()` (primeiro só para tools simples: file read/search/git status).

---

## Update (2026-01-20) — Correções aplicadas

**Concluído**
- Corrigido `vertice serve` para chamar corretamente o entrypoint sync do MCP (sem `run_async()`): `src/vertice_cli/main.py`.
- Corrigido import do runner MCP para apontar para os módulos corretos (evita depender de exports implícitos): `src/vertice_cli/cli_mcp.py`.
- Corrigida execução de tools sync no “MCPClient” interno (agora sempre usa `_execute_validated()`): `src/vertice_cli/core/mcp.py`.
- Tornado MCP server import-safe em ambientes com dependências opcionais/incompatíveis (lazy import de `fastmcp` e Prometheus adapter): `src/vertice_cli/integrations/mcp/server.py`, `src/vertice_cli/integrations/mcp/tools.py`.
- Adicionado smoke test que garante que o MCP server pode ser importado/instanciado sem quebrar o app: `tests/unit/test_mcp_entrypoint_smoke.py`.

**Validação executada**
- `pytest tests/unit/test_mcp_entrypoint_smoke.py -v -x`

---

## Notas de ambiente (descobertas durante a correção)

- `pytest --timeout=...` falhou por falta do plugin `pytest-timeout` (o `pytest.ini` não habilita esse flag). Ajuste rápido: usar `pytest ... -v -x` ou adicionar o plugin no extra `dev` quando fizer sentido.
- Import do `fastmcp` pode falhar por incompatibilidade com `rich` (erro observado: `RichHandler.__init__()` com argumento inesperado). Mitigação aplicada: lazy import + erro explícito ao inicializar/iniciar server.
- Import chain via `prometheus`/`networkx` pode falhar em alguns ambientes (erro observado em `importlib.metadata`: `PathDistribution` sem `_normalized_name`). Mitigação aplicada: Prometheus adapter virou import opcional (não quebra o server por default).

## Follow-ups recomendados (baixo risco)

1. Fixar/alinhar versões `fastmcp` ↔ `rich` (e, se necessário, `networkx`/`importlib_metadata`) para voltar a permitir `fastmcp` real sem lazy fallback.
2. Separar “MCP protocol server” de “prometheus/agents” para evitar cascata de imports pesados no caminho crítico.
3. Adicionar um teste de import para `vertice_cli.cli_mcp.main()` (sem iniciar loop) e outro teste para o erro “fastmcp incompatível” (assert em mensagem), para impedir regressão.

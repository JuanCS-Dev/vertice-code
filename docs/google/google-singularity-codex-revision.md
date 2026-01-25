# Google Singularity Codex — Revision 2026

> **Fonte primária:** [VERTICE_GOOGLE_SINGULARITY_BLUEPRINT_2026.md](./VERTICE_GOOGLE_SINGULARITY_BLUEPRINT_2026.md)
> **Complementos:** project_structure.txt, ARCHITECTURAL_DEEP_DIVE_REPORT_2026.md, documentação Claude Code Parity e código verificado em `agents/`, `vertice_cli/`, `vertice_tui/`, `vertice-chat-webapp/`.

Este documento descreve, com granularidade de implementação, como executar a transmutação completa do Vertice-Code para o estado **Google Native + AG-UI**. Cada fase inclui objetivos, entregáveis técnicos, código-alvo, riscos e critérios de aceite.

## 1. Diagnóstico Honesto (Cláudio vs Realidade)

| Sintoma | Evidência no código | Consequência |
| --- | --- | --- |
| Acoplamento SaaS ↔ CLI | `vertice-chat-webapp/backend/app/core/security.py` importa `src.vertice_cli.agents.security.patterns` | Containers enormes, dependências compartilhadas inseguras |
| Diretório fantasma | `src/vertice-chat-webapp/` contém restos do antigo frontend | Builds confusos e imports quebrados |
| Core hipertrofiado | `src/vertice_cli/` concentra agentes, TUI, MCP, CLI | Impossível liberar lib reutilizável |
| Paridade incompleta com Claude Code | `agents/coder/agent.py` sem execução real, fallback regex; `vertice_cli/agents/reviewer/rag_engine.py` é stub; ferramentas de parity espalhadas | Qualidade menor, riscos de alucinação |
| Testes críticos pendentes | `tests/e2e/parity/test_claude_parity.py` possui skips por funcionalidades incompletas | Sem validação automática |

## 2. Visão Alvo (Google Singularity)

1. **Cérebro** — Agentes Python puros rodando em Vertex AI Reasoning Engines via Google ADK.
2. **Sistema Nervoso** — Protocolo **AG-UI + CopilotKit** garantindo streaming nativo entre agente e interface.
3. **Memória** — **AlloyDB AI** com embeddings nativos (`embedding('text-embedding-005', content)`), ScaNN para busca.
4. **Face** — Next.js 16 hospedado em **Firebase App Hosting** com SSR em Cloud Run gerenciado.
5. **Estrutura** — Monorepo `apps/` (deployables) + `packages/` (bibliotecas reutilizáveis) + `infra/` (IaC Google Cloud).

## 3. Fases de Implementação

Cada fase termina com entregáveis verificáveis. As atividades dependem entre si; não avance sem checklist concluída.

### Fase 1 — Saneamento Estrutural (Semana 1)

**Objetivo:** parar o sangramento. Remover acoplamentos óbvios e preparar o repo para migração controlada.

1. **Incinerar Fantasma**
   - Remover `src/vertice-chat-webapp/` (confirmar ausência em CI).
   - Atualizar `.gitmodules`/scripts que referenciem o diretório.

2. **Packages Core**
   - Mover `src/vertice_cli/` → `packages/vertice-core/src/vertice_core/`.
   - Criar `packages/vertice-core/pyproject.toml` (hatch/poetry) com export de `vertice_core`.
   - Ajustar imports: `src.vertice_cli.*` → `vertice_core.*`. Priorizar módulos citados em `project_structure.txt` (agents, memory, governance, tools).
   - Atualizar `setup.cfg`/`pyproject.toml` raiz para usar editable install (`pip install -e packages/vertice-core`).

3. **CLI/TUI como Apps**
   - Criar `apps/cli-tool/` contendo entrypoint Typer que importa `vertice_core.cli`.
   - Criar `apps/tui/` (Textual) com wrapper leve que consome `vertice_core.tui`.
   - Atualizar pipelines de testes (commands em AGENTS.md) para apontar para novos caminhos.

4. **SaaS isolado**
   - Em `vertice-chat-webapp/backend/requirements.txt`, substituir `../src` por `-e ../../packages/vertice-core`.
   - Remover `sys.path.append("../../src")` e equivalentes.
   - Validar imports: rotas `app/llm/*.py` devem usar `vertice_core.interfaces.*`.

**Critérios de aceite**
- `pip install -e packages/vertice-core` funciona isoladamente.
- `pytest tests/unit -v` roda sem acessar `src/` legado.
- Nenhum arquivo do SaaS referencia `src.vertice_cli`.

### Fase 2 — Transplante Cerebral (Semanas 2-4)

**Objetivo:** migrar agentes críticos para Vertex AI Reasoning Engine usando ADK.

1. **Biblioteca de Agentes (ADK)**
   - Converter `agents/coder/agent.py`, `agents/reviewer/*`, `agents/orchestrator/*` para classes puras (sem dependências de CLI/TUI).
   - Adotar padrões do Google ADK (`ReasoningEngine.create(AgentClass)`), definindo `@tool`/`@workflow` conforme doc Vertex.

2. **Execução Real e Segurança**
   - Implementar sandbox (`vertice_cli/tools/exec_hardened.py`) dentro do novo `vertice_core.execution`.
   - Remover fallback regex (linhas 184-198) em `agents/coder/agent.py` (já verificado).
   - Integrar type-checking (mypy wrapper) e security scan (bandit/semgrep) conforme `CLAUDE_CODE_PARITY_PLAN.md`.

3. **Script de Deploy**
   - Criar `tools/deploy_brain.py` que:
     1. Empacota `vertice-core` (Wheel + metadata ADK).
     2. Chama `vertexai.preview.reasoning_engines.ReasoningEngine.create` com agentes selecionados.
     3. Atualiza registro (`apps/agent-gateway/config/engines.json`).
   - Adicionar testes de fumaça (`tests/integration/test_vertex_deploy.py`).

4. **Observabilidade**
   - Instrumentar agentes com `Google Cloud Logging` e `Cloud Trace` via hooks no ADK.
   - Persistir métricas de custo usando `VERTICE_GOOGLE_SINGULARITY_BLUEPRINT_2026.md` (referência de pricing).

**Critérios de aceite**
- `deploy_brain.py --agent coder` publica agente e retorna ID.
- `tests/e2e/parity/test_claude_parity.py` atualizado roda sem skips para comandos que dependem do agente.
- Métricas de custo agora usam Vertex billing (substituir `MODEL_PRICING` hardcoded).

### Fase 3 — Reconexão Nervosa (Semanas 5-6)

**Objetivo:** abandonar WebSocket/SSE ad-hoc e adotar AG-UI + CopilotKit do blueprint.

1. **Backend Runtime (apps/agent-gateway/)**
   - FastAPI minimal que converte eventos do ADK em eventos AG-UI (`ag_ui_adk` wrapper).
   - Endpoints: `/agui/stream`, `/agui/tasks`, `/healthz`.
   - Autenticação via Google IAM + Service Accounts.

2. **Frontend (apps/web-console/)**
   - Atualizar para Next.js 16 + CopilotKit (`@copilotkit/react-core`, `@copilotkit/react-ui`).
   - Substituir `chat-interface.tsx` por `<CopilotSidebar>` + `<CopilotTextarea>` consumindo runtime `/api/copilot`.
   - Implementar middleware `src/app/api/copilot/route.ts` que proxia para agent-gateway (Cloud Run).

3. **Streaming Markdown (TUI)**
   - Seguir plano `docs/planning/CLAUDE_CODE_WEB_RENDERING.md`: atualizar dependency `textual>=4.0.0`, criar widgets `StreamingMarkdownWidget`, `BlockDetector`, etc.
   - Garantir parity visual com Claude Code desktop.

4. **Protocol Compliance**
   - Definir contrato AG-UI (schemas JSON) em `packages/vertice-core/agui/protocol.py`.
   - Adicionar testes de contrato (`tests/e2e/agui/test_protocol_conformance.py`).

**Critérios de aceite**
- Frontend CopilotKit streaming sem fallback manual.
- TUI roda 30 FPS com fallback automático <25 FPS.
- Documentação AG-UI publicada (`docs/agui-runtime.md`).

### Fase 4 — Eternidade dos Dados (Semanas 7-8)

**Objetivo:** migrar memória e persistência para AlloyDB AI.

1. **Infraestrutura**
   - `infra/terraform/alloydb/` cria instância com `pgvector` + `google_ml_integration` habilitado.
   - Scripts de migração `tools/migrate_memory.py` movem `prometheus.db` → AlloyDB.

2. **Embeddings Nativos**
   - Atualizar `vertice_core.memory.cortex.*` e `vertice_cli/agents/reviewer/rag_engine.py` para usar SQL:
     ```sql
     INSERT INTO code_embeddings(file_path, embedding)
     VALUES ($1, embedding('text-embedding-005', $2));
     ```
   - Configurar triggers que geram embeddings ao inserir/atualizar registros de código.

3. **Busca ScaNN**
   - Implementar índices `USING ivfflat` combinados com `google_ml_integration`. Documentar tuning (lista K=100, probes=10).
   - Adaptar `RAG` para usar `ORDER BY embedding <=> query_embedding LIMIT 20`.

4. **Backups & DR**
   - `infra/cloudbuild.yaml` adiciona job noturno de snapshot AlloyDB + export para GCS.

**Critérios de aceite**
- `tests/unit/test_rag_engine.py` cobre busca real (sem stub).
- Consultas RAG respondem <50ms p95 (medido via `pytest -k rag --duration`).
- Planos de backup restauram banco em ambiente de staging.

### Fase 5 — Governança e DevEx (Semanas 9-10)

1. **Turbo/Nx Orchestration**
   - Adicionar `turbo.json` com pipelines: `lint`, `test`, `build`, `deploy` para apps/pacotes.
   - Configurar caches remotos (Cloud Storage) para acelerar CI.

2. **Segurança e Compliance**
   - Integrar `Secrets Manager` em apps (Firebase Hosting + Cloud Run) para chaves LLM.
   - Revisar `vertice_governance/justica` para operar como serviço isolado (API) consumindo AlloyDB.

3. **Doc & Runbooks**
   - Atualizar `docs/CLAUDE.md`, criar `docs/google_singularity_operating_manual.md`.
   - Incluir runbook de incidentes para Vertex AI/AG-UI/AlloyDB.

4. **Test Matrix**
   - Atualizar comandos obrigatórios do AGENTS.md: `black`, `ruff`, `pytest`, `mypy`, `pip install -e . && vtc --help` para rodarem via monorepo tasks (`turbo run lint`, etc.).

### Fase 6 — Narcissus: UX/UI Imersiva (Semanas 11-12)

**Objetivo:** Transmutar o frontend em uma experiência imersiva "Agent-First" baseada no design do Google Stitch.

1. **Immersive Landing (Stitch Base)**
   - Implementar `vertice-lading-page/code.html` como porta de entrada.
   - Foco: Input central massivo "Command the Agent" com feedback de status "SYSTEM ONLINE".

2. **Agentic Stream & CoT Dashboard**
   - Implementar `refined_agentic_stream_dashboard` e `refined_cot_logic_stream`.
   - Streaming de pensamento (Chain-of-Thought) com renderização de blocos de decisão e sub-tarefas.

3. **Advanced Command Center**
   - Implementar `advanced_command_center/code.html` para monitoramento da malha de agentes (Telemetry, Tokens, Latency).

4. **Artifact Gallery**
   - Implementar `artifact_gallery/code.html` para exibição e gestão de código/UI gerado.

**Critérios de Aceite**
- Interface Next.js 16 reflete 100% dos rascunhos do Stitch.
- Performance: 60fps no streaming de CoT.
- Integração nativa com CopilotKit/AG-UI Runtime.

## 4. Cronograma Sugerido

| Semana | Foco | Principais entregas |
| --- | --- | --- |
| 1 | Fase 1 | Repo reestruturado, core empacotado |
| 2-4 | Fase 2 | Agentes ADK, deploy script, execução real/testes |
| 5-6 | Fase 3 | CopilotKit + AG-UI runtime + TUI streaming |
| 7-8 | Fase 4 | AlloyDB AI em produção, RAG real |
| 9-10 | Fase 5 | Turbo/Nx, governança, docs finais |
| 11-12 | Fase 6 | Narcissus UI (Stitch), Landing Page, Command Center |

## 5. Riscos & Mitigações

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Falta de isolamento durante migração | Deploys quebrados | Feature flags + progressive cutover (CI valida ambos caminhos) |
| Atualização Textual v4 quebra TUI | Experiência CLI degradada | Branch dedicado, fallback plain text automatizado |
| Limits Vertex AI Reasoning Engine | Custos inesperados | Configurar quotas, monitorar via Cloud Monitoring dashboards |
| AlloyDB triggers custosos | Latência ↑ | Batches assíncronos + testes de carga antes do cutover |

## 6. Métricas de Sucesso

- **Escalabilidade:** builds CI paralelos via Turbo; agentes escalam automaticamente em Vertex.
- **Latência:** streaming CopilotKit < 100ms entre eventos.
- **Qualidade:** `tests/e2e/parity/test_claude_parity.py` e `tests/unit/test_claude_parity.py` sem skips; cobertura RAG >80% statements.
- **Custo Ocioso:** Cloud Run + Vertex com scale-to-zero; monitoramento mostra queda >70% vs VMs atuais.

## 7. Próximos Passos Imediatos

1. Aprovar e executar **Fase 1** (scripts de limpeza + criação de `packages/vertice-core`).
2. Definir squad responsável por **Fase 2** (agentes ADK) e iniciar proof-of-concept com `CoderAgent`.
3. Agendar sessão com equipe frontend para alinhar CopilotKit/AG-UI (Fase 3) e revisar `docs/planning/CLAUDE_CODE_WEB_RENDERING.md`.

**ESTE PLANO SUBSTITUI qualquer blueprint anterior. Todas as implementações devem seguir as fases descritas acima.**

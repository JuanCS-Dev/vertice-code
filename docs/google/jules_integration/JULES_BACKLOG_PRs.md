# Backlog para o Jules (PRs pequenas)

Este backlog assume as decisões travadas em `docs/google/google-singularity-gpt52-review.md`:
- AlloyDB desde o início
- `agent-gateway`
- execução 100% remota (Google gerenciado)
- KMS desde o início

Regra: cada item abaixo vira **uma PR pequena** (ideal 1–2h) e respeita `docs/google/JULES_WORKFLOW.md`.

## Status de Execução (25 JAN 2026)

- **PR‑0 (RCE sandbox):** ✅ implementado (bloqueio fail‑closed + regressão `exec(`/`eval(`).
- **PR‑1 (KMS/GDPR):** ✅ implementado (master key obrigatória via env var ou KMS; sem chave efêmera).

## PR-0 — Bloquear RCE (sandbox)

### PR-0A: Remover fallback `exec()` (fail-closed)
- **Arquivos-alvo (máx):** `vertice-chat-webapp/backend/app/sandbox/executor.py`
- **Não fazer:** refactor amplo / mover diretórios
- **Aceite:**
  - `rg -n "exec\\(open\\(" vertice-chat-webapp/backend/app/sandbox/executor.py` retorna vazio
  - execução “sem isolamento” retorna erro explícito (mensagem clara)
 - **Status:** ✅ DONE (25/01/2026)

### PR-0B: Ajustar testes do sandbox (sem execução local)
- **Arquivos-alvo (sugestão):** `vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py`
- **Aceite:** `pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x`
 - **Status:** ✅ DONE (25/01/2026)
 - **Validação adicional:** `pytest vertice-chat-webapp/backend/tests/unit/test_no_local_rce.py -v -x`

## PR-1 — KMS desde o início (GDPR crypto)

### PR-1A: Fail-fast quando KMS não configurado (exceto teste)
- **Arquivos-alvo:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`
- **Aceite:**
  - iniciar app sem `GDPR_MASTER_KEY`/config equivalente falha (modo normal)
  - teste unitário atualizado cobre o comportamento
 - **Status:** ✅ DONE (25/01/2026)

### PR-1B: Interface de Key Provider (KMS) + stub de teste
- **Arquivos-alvo:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py` (ou novo módulo pequeno em `app/core/`)
- **Não fazer:** integrar SDK GCP completo se isso explodir escopo; criar somente interface e “plug point”
- **Aceite:** testes unitários passam e o código não gera key efêmera em runtime normal
 - **Status:** ✅ DONE (25/01/2026)

## PR-2 — Desacoplamento SaaS↔CLI (core instalável)

### PR-2A: Criar `packages/vertice-core` (skeleton mínimo)
- **Arquivos-alvo (novos):**
  - `packages/vertice-core/pyproject.toml`
  - `packages/vertice-core/src/vertice_core/__init__.py`
- **Aceite:** `python -c "import vertice_core; print('OK')"` (com env configurado)

### PR-2B: Mover apenas “security patterns” para `vertice_core`
- **Arquivos-alvo (sugestão):**
  - origem: `src/vertice_cli/agents/security/patterns.py` (ou equivalente)
  - destino: `packages/vertice-core/src/vertice_core/agents/security/patterns.py`
- **Aceite:** import funciona via `vertice_core...`

### PR-2C: Backend passa a importar `vertice_core` (sem `src.*`)
- **Arquivos-alvo:** `vertice-chat-webapp/backend/app/core/security.py` (+ ajuste mínimo de requirements/pyproject do backend se existir)
- **Aceite:**
  - `rg -n "from src\\.|import src\\." vertice-chat-webapp/backend` retorna vazio
  - backend ainda mantém fallback patterns local (não quebra segurança)

### PR-2D: Plumbing da Fase 2 (deploy/registry + compat imports) — ✅ DONE (25/01/2026)
- **Entregáveis:**
  - `tools/deploy_brain.py` + `apps/agent-gateway/config/engines.json`
  - `packages/vertice-core/src/agents/` (import `agents.*`)
  - `packages/vertice-core/src/vertice_agents/` (import `vertice_agents.*`)
- **Aceite (executado):**
  - `pytest tests/integration/test_vertex_deploy.py -v -x`
  - `pytest tests/integration/test_orchestrator_prometheus.py -v -x`
  - `pytest tests/agents/test_registry.py -v -x`
  - `pytest tests/agents/test_coordinator.py -v -x`

## PR-3 — `apps/agent-gateway` (MVP) + contrato de streaming

### PR-3A: Criar `apps/agent-gateway` com `/healthz`
- **Arquivos-alvo:** `apps/agent-gateway/app/main.py`
- **Status:** ✅ DONE (25/01/2026)
- **Aceite (executado):** `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x` (valida `/healthz` via ASGI)

### PR-3B: Contrato AG‑UI mínimo (schemas) no `vertice_core`
- **Arquivos-alvo:** `packages/vertice-core/src/vertice_core/agui/protocol.py`
- **Status:** ✅ DONE (25/01/2026)
- **Aceite (executado):** `pytest tests/unit/test_agui_protocol.py -v -x`

### PR-3C: Endpoint `/agui/stream` com “mock agent” (sem Vertex ainda)
- **Arquivos-alvo:** `apps/agent-gateway/app/main.py` + `packages/vertice-core/src/vertice_core/agui/protocol.py`
- **Status:** ✅ DONE (25/01/2026)
- **Aceite (executado):** `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x`

## PR-4 — AlloyDB desde o início (fundação)

### PR-4A: Config + conector AlloyDB (sem triggers pesadas)
- **Arquivos-alvo (preferência):** `packages/vertice-core/src/vertice_core/memory/` (novos módulos pequenos)
- **Status:** ✅ DONE (25/01/2026)
- **Entregue:**
  - `packages/vertice-core/src/vertice_core/memory/alloydb_connector.py`
- **Aceite (executado):** `pytest tests/unit/test_alloydb_migration.py -v -x` (sem rede)

### PR-4B: Schema mínimo (migrations ou SQL inicial)
- **Arquivos-alvo:** `packages/vertice-core/.../schema.sql` (ou migrations leves)
- **Status:** ✅ DONE (25/01/2026)
- **Entregue:**
  - `packages/vertice-core/src/vertice_core/memory/schema.sql`
  - `docs/google/PR_4_ALLOYDB_MEMORY_FOUNDATION_2026.md` (como aplicar + validação)
- **Aceite (executado):** `pytest tests/unit/test_alloydb_migration.py -v -x`

## PR-5 — Troca para Google gerenciado (Vertex)

### PR-5A: Adapter de execução remota (Code Interpreter) — interface
- **Objetivo:** formalizar a capacidade “executar código” sem implementação local
- **Aceite:** nenhuma dependência do executor local permanece no caminho principal
- **Status:** ✅ DONE (25/01/2026)
- **Entregue:**
  - `vertice-chat-webapp/backend/app/sandbox/vertex_code_execution.py`
  - `vertice-chat-webapp/backend/app/sandbox/executor.py` (fail‑closed + caminho remoto opcional)
  - `vertice-chat-webapp/backend/app/sandbox/mcp_server.py` (flag por env)
- **Validação executada (offline):**
  - `pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x`

### PR-5B: Integração real com Vertex (mínimo viável)
- **Pré‑req:** credenciais e permissões já alinhadas fora do repo
- **Aceite:** um comando/documento para “smoke test” que prova que o agente responde via Google gerenciado
- **Status:** ✅ DONE (25/01/2026)
- **Entregue:**
  - `packages/vertice-core/src/agents/coder/reasoning_engine_app.py`
  - `packages/vertice-core/src/vertice_core/agents/coder/reasoning_engine_app.py`
  - `tests/unit/test_coder_reasoning_engine_app.py`
  - `tools/deploy_brain.py` (mapping `coder`)
- **Validação executada (offline):**
  - `pytest tests/unit/test_coder_reasoning_engine_app.py -v -x`
  - `pytest tests/integration/test_vertex_deploy.py -v -x`

Detalhes completos (PR‑5): `docs/google/PR_5_GOOGLE_MANAGED_VERTEX_2026.md`

## Stop conditions (para evitar travar)
- Se a PR tocar **>25 arquivos** ou tiver **>600 linhas**: dividir.
- Se aparecer necessidade de rename/move massivo: criar “Epic” separada (não fazer no Jules).

---

## PRs de Manutenção (Google Cloud / SRE) — backlog sugerido

Objetivo: preparar manutenção automatizável (pós-frontend) seguindo padrões oficiais do Google Cloud
(Architecture Framework + Cloud Operations), com PRs pequenas e verificáveis.

### PR-M1: Runbook “Manutenção Google Cloud 2026” (docs)
- **Arquivos-alvo (novos):**
  - `docs/google/GOOGLE_CLOUD_MAINTENANCE_BEST_PRACTICES_2026.md`
- **Aceite:** arquivo publicado com checklist “diário/semanal/mensal” + links oficiais.

### PR-M2: Playbook do Jules para manutenção automatizada (docs)
- **Arquivos-alvo (novos):**
  - `docs/google/jules_integration/JULES_GCP_MAINTENANCE_AUTOMATION_2026.md`
- **Aceite:** contém prompts prontos + guardrails (read-only first, sem chaves long-lived).

### PR-M3: Checklist de “GCP inventory” (scripts read-only)
- **Arquivos-alvo (novos):**
  - `tools/gcloud/inventory_cloud_run.sh`
  - `tools/gcloud/inventory_gke.sh`
  - `tools/gcloud/inventory_iam.sh`
- **Não fazer:** comandos `create/update/delete`.
- **Aceite:**
  - scripts rodam sem erro com `gcloud auth application-default login` (local)
  - outputs redigidos (não imprimir secrets)

### PR-M4: “Operações” para Cloud Run (docs + validação)
- **Arquivos-alvo (novos ou update mínimo):**
  - doc curto com como configurar: logs/metrics, alertas, SLO, rollbacks, traffic splitting
- **Aceite:** checklist “antes do deploy” e “pós-deploy”.

### PR-M5: Modelo de SLO + alertas (Infra-as-Code recomendado)
- **Arquivos-alvo:** Terraform/Config (se já existir) OU doc para criação manual
- **Aceite:** 1 SLO exemplo (latência/erro) + 1 alerta (burn rate).

### PR-M6: Política “sem basic roles” + service accounts por serviço (docs)
- **Arquivos-alvo:** doc e tabela de IAM mínimo por serviço
- **Aceite:** checklist aplicável às recomendações do Recommender (least privilege).


## PR-3.1: AG‑UI adapter + `/agui/tasks` (backend-only) — concluída (25 JAN 2026)

- Entregue:
  - `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py`
  - `apps/agent-gateway/app/main.py` (`/agui/tasks/*` + SSE)
  - `tests/unit/test_agui_adk_adapter.py`
  - `tests/integration/test_agent_gateway_agui_stream.py` (inclui tasks)
- Como validar (rápido):
  - `pytest tests/unit/test_agui_adk_adapter.py -v -x`
  - `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x`

Detalhes completos: `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

---

## Phase 4: AlloyDB AI Cutover (Eternidade dos Dados) — concluída (25 JAN 2026)

- Entregue:
  - `tools/migrate_memory.py` (migração `.prometheus/prometheus.db` → AlloyDB)
  - `packages/vertice-core/src/vertice_core/memory/cortex/episodic.py` (default AlloyDB + fallback sem DSN)
  - `packages/vertice-core/src/vertice_core/memory/cortex/semantic.py` (pgvector + embeddings in-db)
  - `tests/unit/test_alloydb_cutover_behavior.py` (testes adicionais)
- Como validar (rápido):
  - `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x`
  - Resultado esperado: `14 passed` (offline)

Detalhes completos: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`

---

## PR-L (Launch) — wiring + produção (26 JAN 2026)

Objetivo: fechar o lançamento com Cloud Run canônico e hardening (sem drift, sem serviços públicos desnecessários).

### PR-L0: Documentar e executar correção de drift do `vertice-agent-gateway`
- **Contexto:** no GCP, o `vertice-agent-gateway` responde `/openapi.json` 200 mas `/healthz` 404 (drift de imagem).
- **Entregáveis (docs):**
  - atualizar `docs/google/LAUNCH_ROADMAP_GOOGLE_STACK_2026.md` (M0.1) com comandos exatos de build/deploy.
  - registrar evidências em `docs/google/EXECUTION_REPORT_WIRING_FRONTEND_BACKEND_2026-01-26.md`.
- **Aceite (read-only):**
  - `curl $AG_URL/openapi.json` = 200
  - `curl $AG_URL/healthz` = 200

### PR-L1: Hardening IAM do Cloud Run (gateway privado, frontend público)
- **Regra:** não executar sem aprovação explícita do owner.
- **Entregáveis (docs):**
  - comandos `gcloud run services add/remove-iam-policy-binding` + rollback.
- **Aceite:** `/dashboard` e `/artifacts` funcionam via `vertice-frontend` com `vertice-agent-gateway` privado.

### PR-L2: Pipeline do frontend canônico (`apps/web-console`)
- **Problema atual:** configs de Cloud Build apontam para frontends legados (`vertice-chat-webapp/frontend`).
- **Entregáveis:**
  - `apps/web-console/Dockerfile` (Next.js production)
  - `cloudbuild.web-console.yaml` (build/push)
  - doc curto em `docs/google/` com comandos de deploy para `vertice-frontend`.
- **Aceite:**
  - build Cloud Build gera imagem
  - `vertice-frontend` serve rotas do `apps/web-console`

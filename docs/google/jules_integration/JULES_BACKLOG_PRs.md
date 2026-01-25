# Backlog para o Jules (PRs pequenas)

Este backlog assume as decisões travadas em `docs/google/google-singularity-gpt52-review.md`:
- AlloyDB desde o início
- `agent-gateway`
- execução 100% remota (Google gerenciado)
- KMS desde o início

Regra: cada item abaixo vira **uma PR pequena** (ideal 1–2h) e respeita `docs/google/JULES_WORKFLOW.md`.

## PR-0 — Bloquear RCE (sandbox)

### PR-0A: Remover fallback `exec()` (fail-closed)
- **Arquivos-alvo (máx):** `vertice-chat-webapp/backend/app/sandbox/executor.py`
- **Não fazer:** refactor amplo / mover diretórios
- **Aceite:**
  - `rg -n "exec\\(open\\(" vertice-chat-webapp/backend/app/sandbox/executor.py` retorna vazio
  - execução “sem isolamento” retorna erro explícito (mensagem clara)

### PR-0B: Ajustar testes do sandbox (sem execução local)
- **Arquivos-alvo (sugestão):** `vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py`
- **Aceite:** `pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x`

## PR-1 — KMS desde o início (GDPR crypto)

### PR-1A: Fail-fast quando KMS não configurado (exceto teste)
- **Arquivos-alvo:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`
- **Aceite:**
  - iniciar app sem `GDPR_MASTER_KEY`/config equivalente falha (modo normal)
  - teste unitário atualizado cobre o comportamento

### PR-1B: Interface de Key Provider (KMS) + stub de teste
- **Arquivos-alvo:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py` (ou novo módulo pequeno em `app/core/`)
- **Não fazer:** integrar SDK GCP completo se isso explodir escopo; criar somente interface e “plug point”
- **Aceite:** testes unitários passam e o código não gera key efêmera em runtime normal

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
- **Arquivos-alvo (novos):** `apps/agent-gateway/main.py` (+ `pyproject.toml`/`requirements.txt` mínimos)
- **Aceite:** rodar localmente e responder `200` em `/healthz` (comando/documentado)

### PR-3B: Contrato AG‑UI mínimo (schemas) no `vertice_core`
- **Arquivos-alvo:** `packages/vertice-core/src/vertice_core/agui/protocol.py`
- **Aceite:** teste unitário de schema/serialização (arquivo único)

### PR-3C: Endpoint `/agui/stream` com “mock agent” (sem Vertex ainda)
- **Arquivos-alvo:** `apps/agent-gateway/main.py` + `packages/vertice-core/...`
- **Aceite:** curl/cliente recebe stream com eventos estáveis (documentar 1 comando)

## PR-4 — AlloyDB desde o início (fundação)

### PR-4A: Config + conector AlloyDB (sem triggers pesadas)
- **Arquivos-alvo (preferência):** `packages/vertice-core/src/vertice_core/memory/` (novos módulos pequenos)
- **Aceite:** teste/“smoke import” do conector + validação de config (sem rede)

### PR-4B: Schema mínimo (migrations ou SQL inicial)
- **Arquivos-alvo:** `packages/vertice-core/.../schema.sql` (ou migrations leves)
- **Aceite:** doc de “como aplicar” + checagem de consistência (lint/format do arquivo)

## PR-5 — Troca para Google gerenciado (Vertex)

### PR-5A: Adapter de execução remota (Code Interpreter) — interface
- **Objetivo:** formalizar a capacidade “executar código” sem implementação local
- **Aceite:** nenhuma dependência do executor local permanece no caminho principal

### PR-5B: Integração real com Vertex (mínimo viável)
- **Pré‑req:** credenciais e permissões já alinhadas fora do repo
- **Aceite:** um comando/documento para “smoke test” que prova que o agente responde via Google gerenciado

## Stop conditions (para evitar travar)
- Se a PR tocar **>25 arquivos** ou tiver **>600 linhas**: dividir.
- Se aparecer necessidade de rename/move massivo: criar “Epic” separada (não fazer no Jules).

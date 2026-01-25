# Google Singularity — GPT‑5.2 Review (2026-01-24)

Escopo analisado:
- `docs/google/ARCHITECTURAL_DEEP_DIVE_REPORT_2026.md`
- `docs/google/DETAILED_SURGERY_PREP_REPORT_2026.md`
- `docs/google/google-singularity-antigravity-revision.md`
- `docs/google/google-singularity-codex-revision.md`
- `docs/google/project_structure.txt`
- `docs/google/VERTICE_GOOGLE_SINGULARITY_BLUEPRINT_2026.md`
- `docs/google/WEBAPP_GOOGLE_NATIVE_MIGRATION_2026.md`

## Decisões travadas (2026-01-24)
1. **Memória:** AlloyDB desde o início.
2. **Backend runtime:** `agent-gateway`.
3. **Execução:** tudo remoto (Google gerenciado), zero execução local.
4. **Chaves:** Cloud KMS desde o início.

## TL;DR (o que fazer primeiro)
1. **Bloquear RCE hoje:** remover o fallback `exec()` do sandbox e garantir que não exista caminho de execução “sem sandbox”.
2. **Evitar perda irreversível de dados:** parar de gerar chave efêmera para GDPR; exigir chave (fail-fast) ou migrar para KMS/Secret Manager.
3. **Cortar o acoplamento SaaS↔CLI:** parar import de `src.*` dentro do backend e empacotar um core instalável (`packages/vertice-core`).
4. **Escolher “fonte de verdade” do plano:** padronizar nomenclatura + árvore alvo (apps/packages) e registrar decisões em um único doc.

## Achados confirmados no código (não teóricos)
- **Acoplamento SaaS↔CLI via import:** `vertice-chat-webapp/backend/app/core/security.py` importa `src.vertice_cli...` (com fallback local).
- **RCE explícito no sandbox:** `vertice-chat-webapp/backend/app/sandbox/executor.py` contém `exec(open('{code_file}').read())` (mesmo com gVisor opcional).
- **Risco de “crypto-shredding acidental”:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py` gera chave efêmera quando `GDPR_MASTER_KEY` não existe.
- **Evidência de dependência em `src` fora do SaaS:** existem testes/scripts com `sys.path.append("/media/juan/DATA/Vertice-Code/src")` (isso vira dívida técnica quando tentar empacotar/migrar).

---

## Update (25 JAN 2026) — Validação do “plumbing” (Fase 2)

Implementado e validado offline:
- `tools/deploy_brain.py` + `apps/agent-gateway/config/engines.json` (registry local de engines; `--dry-run`).
- Pacotes importáveis para manter compatibilidade durante a migração:
  - `agents.*` (em `packages/vertice-core/src/agents/`).
  - `vertice_agents.*` (em `packages/vertice-core/src/vertice_agents/`).

Comandos executados:
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_orchestrator_prometheus.py -v -x
pytest tests/agents/test_registry.py -v -x
pytest tests/agents/test_coordinator.py -v -x
```

## Update (25 JAN 2026) — Fase 3 (AG‑UI) Backend‑Only MVP

Implementado e validado offline:
- `GET /agui/stream` (SSE) em `apps/agent-gateway/app/main.py` com eventos MVP estáveis: `delta|final|tool|error`.
- Contrato de protocolo em `packages/vertice-core/src/vertice_core/agui/protocol.py` (+ exports em `packages/vertice-core/src/vertice_core/agui/__init__.py`).
- Testes:
  - `tests/unit/test_agui_protocol.py`
  - `tests/integration/test_agent_gateway_agui_stream.py`

Comandos executados:
```bash
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
```

## Convergência entre os documentos (o núcleo está alinhado)
Os 7 docs apontam para a mesma sequência macro:
- **Fase 1 (Saneamento):** eliminar diretório fantasma `src/vertice-chat-webapp`, desacoplar imports e criar `packages/vertice-core`.
- **Fase 2 (Agentes Google):** migrar agentes para ADK/Reasoning Engines (Vertex AI) e abandonar orquestração manual.
- **Fase 3 (UX/Streaming):** AG‑UI + CopilotKit como “sistema nervoso”.
- **Fase 4 (Memória):** AlloyDB AI como memória/indexação (vs alternativa Firestore “lite”).

## Inconsistências / decisões pendentes (precisa 1 decisão cada)
- **Nome do serviço backend:** `apps/api-gateway` (Deep Dive) vs `apps/agent-gateway` (Blueprint/Codex). Escolher 1 e manter.
- **Status dos docs:** o `google-singularity-codex-revision.md` diz “substitui qualquer blueprint anterior”, mas o `BLUEPRINT_2026` se declara “a lei”. Definir oficialmente qual é o canonical (minha recomendação: **Codex Revision** como canonical e o Blueprint como “visão”).
- **Estratégia de migração do WebApp:** alguns trechos assumem manter `vertice-chat-webapp/` por um tempo; outros assumem mover para `apps/web-console/` cedo. Definir *quando* vira rename.
- **Memória “AlloyDB vs Firestore”:** o plano alterna. Escolher com base no requisito: “indexar todo repo” → AlloyDB; “histórico simples” → Firestore.

## Lacunas que impedem execução segura (antes de “mexer em tudo”)
- **Threat model e boundary:** quais capacidades de execução de código existirão após remover `executor.py`? (nenhuma local? execução remota? whitelists?)
- **Plano de rollout/cutover:** feature flags, dual-path temporário (antigo/novo), e rollback explícito.
- **Contrato AG‑UI:** schemas/versões/eventos mínimos (ex.: `delta`, `tool_call`, `final`) + testes de conformidade.
- **Política de chaves/segredos:** KMS vs Secret Manager, como versionar, como rotacionar, e como evitar “ephemeral key” em prod.
- **Critérios de aceite por fase em CI:** quais comandos rodam e onde (repo root vs apps/pacotes).

## Caminho crítico sugerido (7 dias, entregáveis verificáveis)
Dia 0–1 (Segurança)
- Remover o fallback `exec()` e fazer o executor falhar de forma segura quando gVisor/isolamento não estiver disponível.
- Alterar GDPR para **fail-fast** sem `GDPR_MASTER_KEY` (ou já integrar Secret Manager/KMS).
- Critério de aceite: testes unitários do backend passam e nenhum endpoint executa código via `exec()`.

Dia 1–3 (Desacoplamento mínimo)
- Criar `packages/vertice-core` com `pyproject.toml` e mover apenas os módulos necessários para destravar o WebApp (ex.: `agents.security.patterns`).
- Ajustar `vertice-chat-webapp/backend` para depender de `-e ../../packages/vertice-core` e remover `sys.path` hacks.
- Critério de aceite: backend importa apenas `vertice_core.*` (sem `src.*`).

Dia 3–5 (Estrutura e compatibilidade)
- Introduzir um **shim temporário** para não quebrar o mundo (ex.: `src/vertice_cli` reexportando `vertice_core`) *até* todos os imports migrarem.
- Padronizar nomes: decidir `agent-gateway` vs `api-gateway` e registrar.
- Critério de aceite: `pytest` do repo roda com ambos caminhos (temporário) e sem duplicidade de módulos.

Dia 5–7 (PoC Google Native)
- PoC mínimo: um “gateway” que chama um agente (mock/local) e emite um stream no formato alvo (AG‑UI), sem reescrever toda a app.
- Critério de aceite: frontend/TUI conseguem renderizar streaming com contrato estável (mesmo que o backend ainda não seja Vertex).

## Riscos principais (e mitigação prática)
- **Risco:** migração estrutural quebrar imports em cascata. **Mitigação:** shim + migração por módulo + CI por pacote.
- **Risco:** remover `executor.py` quebrar features existentes. **Mitigação:** substituir por “capacidade” (tool/extension) e/ou desativar feature com flag até PoC.
- **Risco:** custos/quota/preview API (Vertex Reasoning Engines). **Mitigação:** PoC isolado + quotas + observabilidade antes de cutover.
- **Risco:** AlloyDB triggers/embeddings virarem gargalo. **Mitigação:** pipeline assíncrono (batch) e benchmark antes de produção.

## Perguntas rápidas (se você responder, eu fecho o plano com precisão)
1. Quer **AlloyDB como obrigatório** (repo-index total) ou aceita começar com Firestore e migrar depois?
2. O “gateway” deve se chamar **`api-gateway`** ou **`agent-gateway`**? (escolha 1)
3. O requisito é **zero execução de código local** no backend (só remoto/Vertex), ou precisa manter execução local (bem isolada) para dev?
4. Preferência para gestão de chaves: **Secret Manager** (simples) agora e KMS depois, ou KMS desde o dia 1?

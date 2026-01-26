# Workflow para o Jules (PRs curtas e confiáveis)

Objetivo: fazer o Jules manter o repo com **tarefas bem delimitadas**, evitando mudanças grandes (100+ arquivos) que tendem a travar/ficar lentas.

## Regras de escopo (HARD LIMITS)
- **1 PR = 1 objetivo** (bugfix, refactor mínimo, ou doc).
- **≤ 25 arquivos tocados** por PR (ideal: ≤ 10).
- **≤ 600 linhas de diff** por PR (ideal: ≤ 250).
- **Proibido** “arrumar tudo”, “cleanup geral”, “renomear pastas em massa”.
- Se estourar qualquer limite: **parar**, abrir “PR‑N‑B” (continuação) e manter a PR original pequena.

## Como pedir uma tarefa (template de prompt)
Copie/cole isto no Jules:

```
Objetivo (1 frase):
- ...

Escopo permitido:
- Arquivos-alvo: <lista explícita>
- Pode criar no máximo: <N> arquivos

Escopo proibido:
- Não tocar em: <pastas/arquivos>
- Não reformatar/lint global
- Não mover/renomear diretórios

Critério de aceite (comandos objetivos):
- <comando 1> deve retornar ...
- <comando 2> deve retornar ...

Limites:
- <=25 arquivos tocados
- <=600 linhas de diff
Se estourar: pare e peça para dividir.
```

## Checkpoints (como evitar “task creep”)
1. **Plano**: antes de aprovar, verifique se:
   - lista de arquivos é curta e explícita;
   - existem critérios de aceite executáveis;
   - o plano não contém “refactor broad”, “cleanup”, “rename/move”.
2. **Durante**: se o diff crescer, peça **split** imediatamente.
3. **Final**: exija “diffstat + comandos rodados + resultado”.

## Validação “barata” (preferir sempre)
Use validação por arquivo ou por subpasta antes de rodar suites grandes.

Exemplos úteis para este repo:
- Buscar imports proibidos no SaaS: `rg -n "from src\\.|import src\\." vertice-chat-webapp/backend`
- Buscar execução perigosa: `rg -n "exec\\(|eval\\(" vertice-chat-webapp/backend/app`
- Garantir que diretório fantasma não existe: `test ! -d src/vertice-chat-webapp && echo OK`

Se a mudança for Python (preferir):
- `ruff check <alvo> --fix` e `ruff format <alvo>` (quando disponível)
- `pytest <teste_específico> -v -x`

Exemplos reais (rodados na Fase 2, 25/01/2026):
- `pytest tests/integration/test_vertex_deploy.py -v -x`
- `pytest tests/integration/test_orchestrator_prometheus.py -v -x`
- `pytest tests/agents/test_registry.py -v -x`
- `pytest tests/agents/test_coordinator.py -v -x`

Exemplos reais (rodados na Fase 3, 25/01/2026):
- `pytest tests/unit/test_agui_protocol.py -v -x`
- `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x`

Exemplos reais (rodados em hardening de segurança, 25/01/2026):
- `pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x`
- `pytest vertice-chat-webapp/backend/tests/unit/test_no_local_rce.py -v -x`
- `pytest vertice-chat-webapp/backend/tests/unit/test_gdpr_crypto.py -v -x`

## Setup (evitar tempo morto)
- Se o Jules permitir: usar **setup script** no repo para padronizar ambiente.
- Se precisar de segredos/keys: **não hardcode** e **não commitar**. Preferir:
  - **Google Cloud ADC** (Application Default Credentials) para rodar localmente; e
  - **Workload Identity Federation (OIDC)** para CI/CD (evitar chaves long-lived).
- Se a tarefa pedir qualquer mudança em GCP (IAM/Cloud Run/GKE/etc): o Jules deve operar em modo **read-only primeiro**
  (inventário/describe/list) e só executar `create/update/delete` com confirmação explícita.

Referências (oficiais):
- ADC: https://cloud.google.com/docs/authentication/provide-credentials-adc
- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation

## Política de branches/PR
- Nome da branch: `jules/<tema-curto>-<yyyy-mm-dd>`
- Título da PR: `fix(google-singularity): ...` / `docs(jules): ...`
- Descrição sempre inclui:
  - “Objetivo”
  - “O que mudou”
  - “Como validar” (2–5 comandos)
  - “Limites respeitados” (files/diff)
  - “Impacto GCP” (se existir): `read-only` / `update` e o(s) comando(s) `gcloud` usados

---

## Exemplo recente (25 JAN 2026): Fase 3.1 (AG‑UI)

- “O que mudou”: adapter ADK->AG-UI + `/agui/tasks/*` + cleanup App Hosting.
- “Como validar”:
  - `pytest tests/unit/test_agui_adk_adapter.py -v -x`
  - `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x`

Detalhes completos: `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

---

## Exemplo recente (25 JAN 2026): Phase 4 (AlloyDB AI Cutover)

- “O que mudou”: cutover AlloyDB AI (default) + embeddings in-db + migração `.prometheus/prometheus.db` → AlloyDB.
- “Como validar”:
  - `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x`
  - Resultado esperado: `14 passed` (offline)

Detalhes completos: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`

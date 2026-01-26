# Jules + Google Cloud — Manutenção Automatizada (Padrão 2026)

Objetivo: usar o Jules para manter **código + operação** com PRs curtas, auditáveis e alinhadas ao padrão oficial do
Google Cloud (Architecture Framework + Cloud Operations), sem introduzir riscos de credenciais ou mudanças destrutivas.

Pré-requisitos (Google padrão):
- Local: **ADC** (Application Default Credentials) — https://cloud.google.com/docs/authentication/provide-credentials-adc
- CI/CD: **Workload Identity Federation (OIDC)** (evitar chaves long-lived) — https://cloud.google.com/iam/docs/workload-identity-federation
- Cloud Run service identity (service accounts por serviço) — https://cloud.google.com/run/docs/securing/service-identity

---

## Guardrails (HARD)

- Nunca colar/armazenar segredos no repo, em PRs, em logs ou em prompts.
- Preferir **read-only first**:
  - comandos `gcloud ... list/describe` para inventário/diagnóstico;
  - só executar `create/update/delete` com aprovação explícita e com plano + rollback.
- Sempre gerar artefatos de auditoria em `docs/google/`:
  - inventário (recursos + regiões);
  - validações executadas (comandos e resultados);
  - diffs de configuração quando aplicável (YAML exportado / describe).

---

## Rotina automatizável (o que o Jules deve manter)

### 1) Observabilidade e SLOs
Tarefas típicas:
- Propor/atualizar SLOs (latência e taxa de erro) por serviço.
- Criar/ajustar alertas (burn rate) e dashboards.

Docs oficiais:
- Cloud Monitoring docs: https://cloud.google.com/monitoring/docs
- Alerting: https://cloud.google.com/monitoring/alerts

### 2) IAM e “least privilege”
Tarefas típicas:
- Mapear service accounts por serviço e revisar papéis mínimos.
- Converter serviços que ainda usam “basic roles” para papéis específicos.
- Aplicar recomendações do IAM Recommender quando fizer sentido.

Docs oficiais:
- IAM secure usage: https://cloud.google.com/iam/docs/using-iam-securely
- Recommender: https://cloud.google.com/recommender/docs

### 3) Confiabilidade (GKE backups + manutenção)
Tarefas típicas (exigem aprovação):
- Criar/ajustar Backup for GKE (backup plan, retenção).
- Definir maintenance windows / exclusions.
- Validar que o backup agendado está realmente rodando (listar backups e estados).

Docs oficiais:
- Backup for GKE: https://cloud.google.com/kubernetes-engine/docs/add-on/backup-for-gke
- Maintenance windows: https://cloud.google.com/kubernetes-engine/docs/how-to/maintenance-windows

### 4) Custos, cotas e proteção
Tarefas típicas:
- Criar alertas de orçamento (Billing budgets).
- Criar alertas para quotas críticas.
- Propor ajustes de autoscaling (Cloud Run / GKE) com base em métricas.

Docs oficiais:
- Budgets: https://cloud.google.com/billing/docs/how-to/budgets
- Quotas: https://cloud.google.com/docs/quotas

---

## Estado atual (observado em 2026-01-26, projeto `vertice-ai`)
Este bloco serve para o Jules “entender o terreno” antes de propor mudanças:
- Cloud Run em `us-central1`: `vertice-frontend`, `vertice-backend`, `vertice-mcp`, `vertice-agent-gateway`, `ssrverticeai`
- IAM (observado): todos os serviços acima com `roles/run.invoker` para `allUsers` (**públicos**)
- GKE Autopilot: `vertice-cluster` (maintenance window diária 22:00Z→04:00Z)
- Backup for GKE: `vertice-backup-plan` com retenção 14 dias e cron `10 2 * * *` (UTC)
- Firebase: Hosting `vertice-ai.web.app` e App Hosting backends `us-central1`/`vertice-us` (aparenta legado vs Cloud Run atualizado)

---

## Checks “baratos” (copiar/colar) — só leitura

### Cloud Run (inventário + acesso público)
```bash
gcloud run services list --platform managed --region us-central1
gcloud run services get-iam-policy vertice-frontend --region us-central1
gcloud run services get-iam-policy vertice-backend --region us-central1
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1
```

### GKE maintenance + backup (provar que está funcionando)
```bash
gcloud container clusters describe vertice-cluster --region us-central1 --format='yaml(maintenancePolicy)'
gcloud beta container backup-restore backup-plans describe vertice-backup-plan --location us-central1
gcloud beta container backup-restore backups list --location us-central1 --backup-plan vertice-backup-plan
```

### Quota SSD (risco de saturação)
```bash
gcloud compute regions describe us-central1 --format=json | jq '.quotas[] | select(.metric=="SSD_TOTAL_GB")'
```

### Firebase (detectar legado)
```bash
firebase hosting:channel:list --project vertice-ai
firebase apphosting:backends:list --project vertice-ai
```

---

## Prompts prontos (copiar/colar no Jules)

### Prompt A — Inventário read-only (Cloud Run + GKE + IAM)
```

### Prompt B — Hardening PR: Cloud Run invoker (sem executar mudanças)
```
Objetivo (1 frase):
- Propor um PR/documento com o plano de hardening para Cloud Run (tornar backends privados), sem executar comandos que mudem IAM.

Saída esperada:
- Um arquivo em docs/google/ descrevendo:
  - qual serviço fica público (frontend)
  - quais serviços ficam privados (agent-gateway/backend/mcp)
  - comandos gcloud exatos para remover `allUsers` e adicionar `serviceAccount:` correto para `roles/run.invoker`
  - plano de rollback

Escopo permitido:
- Criar/atualizar apenas arquivos em:
  - docs/google/
  - docs/google/jules_integration/
```
Objetivo (1 frase):
- Gerar inventário read-only do projeto GCP (Cloud Run, GKE e IAM) e salvar um relatório em docs/google/.

Escopo permitido:
- Criar/atualizar apenas arquivos em:
  - tools/gcloud/
  - docs/google/
  - docs/google/jules_integration/

Escopo proibido:
- Não executar comandos gcloud com create/update/delete.
- Não tocar em .env/segredos/credenciais.

Critério de aceite:
- Script(s) em tools/gcloud/ rodam com gcloud autenticado (ADC) e não imprimem segredos.
- Relatório em docs/google/ inclui: data, projeto, regiões, lista de serviços e status.
```

### Prompt B — “Aplicar recomendações do Recommender” (planejamento)
```
Objetivo (1 frase):
- Traduzir recomendações do Recommender em um plano executável (sem aplicar mudanças), com riscos e rollback.

Escopo permitido:
- Apenas docs em docs/google/.

Escopo proibido:
- Não executar mudanças em GCP.

Critério de aceite:
- Documento inclui links oficiais para cada tipo de recomendação (IAM, GKE backup, maintenance windows, quotas).
- Inclui checklist de validação pós-mudança.
```

### Prompt C — Cloud Run “operational hardening” (docs + checks)
```
Objetivo (1 frase):
- Criar/atualizar um runbook operacional do Cloud Run (deploy, rollback, health checks, observability) para os serviços do Vertice.

Escopo permitido:
- Apenas docs/google/ e docs/google/jules_integration/.

Critério de aceite:
- Runbook referencia documentação oficial (Cloud Run deploy/traffic, monitoring, service identity).
- Inclui smoke test mínimo e critérios de rollback.
```

---

## Onde o Jules deve escrever relatórios

- `docs/google/` (relatórios e runbooks principais)
- `docs/google/jules_integration/` (workflow/padrões e prompts)

Base de referência do padrão do repo:
- `docs/google/GOOGLE_CLOUD_MAINTENANCE_BEST_PRACTICES_2026.md`
- `docs/google/jules_integration/JULES_WORKFLOW.md`

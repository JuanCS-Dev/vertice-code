# Google Cloud — Validação das Recomendações vs Estado Real (2026-01-26)

Data: **2026-01-26**
Projeto: **`vertice-ai`**

Objetivo: validar se a lista do Recommender ainda faz sentido após o redeploy, comparando com o estado real obtido via
`gcloud` (read-only).

## Fontes (evidência)

Inventários gerados (read-only) em:
- `docs/google/_inventory/cloud_run_vertice-ai_summary_2026-01-26T16-27-43Z.md`
- `docs/google/_inventory/gke_clusters_vertice-ai_summary_2026-01-26T16-26-26Z.md`
- `docs/google/_inventory/iam_vertice-ai_summary_2026-01-26T16-26-15Z.md`

Comandos pontuais usados (read-only):
- `gcloud container clusters describe vertice-cluster --region us-central1 --format=json`
- `gcloud beta container backup-restore backup-plans list --location us-central1 --format=json`
- `gcloud compute disks list --format=json` (para estimar consumo de storage na região)
- `gcloud beta quotas preferences list --project vertice-ai` (para confirmar solicitações de quota)

---

## 1) Reliability — GKE: “Create a backup plan” (vertice-cluster / us-central1)

Status real:
- Cluster `vertice-cluster` existe e está `RUNNING` em `us-central1`.
- Backup plan existente: `vertice-backup-plan` (estado: `READY`).

Conclusão:
- Recomendação **endereçada** (há Backup Plan configurado).

---

## 2) Reliability — GKE: “Set maintenance window” (vertice-cluster / us-central1)

Status real:
- `maintenancePolicy` configurada com janela recorrente **diária** (UTC): **22:00 → 04:00**.

Conclusão:
- Recomendação **endereçada**.

---

## 3) Security — Cloud Run: “Create new service account with minimal permissions”

Serviços Cloud Run encontrados (us-central1):
- `ssrverticeai`
- `vertice-agent-gateway`
- `vertice-backend`
- `vertice-frontend`
- `vertice-mcp`

Status real:
- Os serviços de aplicação (`vertice-agent-gateway`, `vertice-backend`, `vertice-mcp`, `vertice-frontend`) usam **service
  accounts dedicadas** por serviço (least privilege).
- `ssrverticeai` também está configurado com SA dedicada, porém o serviço está `Ready=False` por drift de imagem (ver nota
  abaixo).

Conclusão:
- Recomendação **endereçada** para os serviços ativos do backend.

Observação sobre itens “-us” / outras regiões:
- No estado atual, **não foram encontrados** serviços `vertice-backend-us` e `vertice-frontend-us` na região `us-central1`
  via `gcloud run services list`.
- Também não foram encontrados serviços em `southamerica-east1` via `gcloud run services list`.
- Portanto, essas entradas do Recommender parecem **desatualizadas** (provável stack antigo).

Notas de dependências observadas (para IAM mínimo):
- `vertice-agent-gateway`: usa Secret Manager (`vertice-alloydb-dsn:1`) + Serverless VPC Access (`vertice-vpc-conn`).
- `vertice-backend`: usa Secret Manager (`stripe-secret-key:latest`).
- `ssrverticeai`, `vertice-frontend`, `vertice-mcp`: sem secrets por env var no momento.

### 3.1 Security extra (fora do Recommender): Cloud Run Invoker público
Status real (2026-01-26):
- Todos os serviços Cloud Run listados em `us-central1` estão com `roles/run.invoker` atribuído a `allUsers`
  (públicos).

Impacto:
- Mesmo com auth no app, endpoints públicos aumentam superfície (bots, scraping, custo).
- Para o padrão “Google” em produção: manter **apenas** o frontend público e restringir backend/gateway/mcp via IAM
  (invocação por service account).

Nota importante: `ssrverticeai`
- Apesar de responder `200` no endpoint público, o serviço está `Ready=False` porque o **latest created revision** falha
  com “Image not found” (Artifact Registry). Isso impede novas revisões/escala segura até um redeploy restaurar a imagem.

---

## 4) Reliability — Quotas: `compute.googleapis.com` SSD-TOTAL-GB-per-project-region (us-central1)

Status real (via Cloud Quotas):
- Quota `SSD-TOTAL-GB-per-project-region` (Persistent Disk SSD (GB)) em `us-central1`:
  **limite = 250 GB**.

Estimativa de consumo atual (via `gcloud compute disks list` em `us-central1`):
- Discos encontrados: **2x `pd-balanced` de 100 GB** (total **200 GB**).
- Isso bate com o alerta do Recommender (~**80%** de 250 GB).

Conclusão:
- Recomendação **ainda aplicável**: com o cluster crescendo (mais nós/discos), existe risco real de bater a quota e
  causar falhas de provisionamento/escala.

---

## 5) Reliability — Quotas: `run.googleapis.com` CpuAllocPerProjectRegion (us-central1)

Status real (via QuotaPreferences / Cloud Quotas):
- `CpuAllocPerProjectRegion` (Cloud Run) em `us-central1`:
  **granted = 20000m (20 vCPU)**.
- Há QuotaPreferences registradas no projeto solicitando aumento (ainda não concedido automaticamente).

Limitação de validação:
- O Recommender reportou **110%**; este snapshot não confirmou o percentual de uso diretamente via CLI.

Conclusão:
- Item **provavelmente aplicável**, mas precisa confirmação adicional (console/metricas) para evitar ações erradas.

Mitigação segura (sem risco imediato):
- Reduzir `maxScale`/CPU onde estiver exagerado para o momento, **ou**
- Solicitar aumento de quota para `CpuAllocPerProjectRegion` em `us-central1`.

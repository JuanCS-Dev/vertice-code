# Google Cloud — Plano de Ação (Recommender) (2026-01-26)

Data: **2026-01-26**
Projeto: **`vertice-ai`**

Este plano é derivado do relatório:
- `docs/google/GOOGLE_CLOUD_RECOMMENDER_VALIDATION_REPORT_2026-01-26.md`

## 0) Pré-check (read-only)

```bash
export GOOGLE_CLOUD_PROJECT="vertice-ai"
./tools/gcloud/inventory_cloud_run.sh
./tools/gcloud/inventory_gke.sh
./tools/gcloud/inventory_iam.sh
```

---

## 1) GKE — Criar Backup Plan (Backup for GKE)

Decisões necessárias (antes de aplicar):
- **Schedule**: horário UTC (cron) ou RPO em minutos.
- **Retenção**: `backup-retain-days` (ex.: 14/30).
- **Escopo**: `--all-namespaces` (recomendado para início).
- **Conteúdo**:
  - `--include-secrets` (normalmente sim, para restores completos)
  - `--include-volume-data` (sim se houver PVC/PD a preservar)

Comando sugerido (diário 03:10 UTC, retenção 14 dias; ajuste conforme decisão):
```bash
gcloud beta container backup-restore backup-plans create vertice-backup-plan \
  --project=vertice-ai \
  --location=us-central1 \
  --cluster=projects/vertice-ai/locations/us-central1/clusters/vertice-cluster \
  --all-namespaces \
  --cron-schedule="10 3 * * *" \
  --backup-retain-days=14 \
  --include-secrets \
  --include-volume-data
```

Validação:
```bash
gcloud beta container backup-restore backup-plans list --project=vertice-ai --location=us-central1
gcloud beta container backup-restore backups list --project=vertice-ai --location=us-central1
```

---

## 2) GKE — Definir Maintenance Window

Decisões necessárias:
- Janela (start/end) e recorrência (RRULE).
- Fuso: o comando aceita timestamps com offset (`-03:00`, `Z`, etc).

Opção A (simples): janela diária de 4h começando em um horário (UTC)
```bash
gcloud container clusters update vertice-cluster \
  --project=vertice-ai \
  --region=us-central1 \
  --maintenance-window="03:00"
```

Opção B (recorrente): 22:00–04:00 UTC diariamente (exemplo)
```bash
gcloud container clusters update vertice-cluster \
  --project=vertice-ai \
  --region=us-central1 \
  --maintenance-window-start="2000-01-01T22:00:00Z" \
  --maintenance-window-end="2000-01-02T04:00:00Z" \
  --maintenance-window-recurrence="FREQ=DAILY"
```

Validação:
```bash
gcloud container clusters describe vertice-cluster --project=vertice-ai --region=us-central1 --format=json | jq '.maintenancePolicy'
```

---

## 3) Cloud Run — Service Account por serviço (least privilege)

Estado atual: todos os serviços usam `239800439060-compute@developer.gserviceaccount.com`.

Alvo:
- Criar **uma service account por serviço**.
- Conceder somente papéis necessários (principalmente Vertex AI + Secret Manager quando usado).

### 3.1 Criar service accounts (sugestão de nomes)
```bash
gcloud iam service-accounts create cr-vertice-agent-gateway \
  --project=vertice-ai \
  --display-name="Cloud Run SA - vertice-agent-gateway"

gcloud iam service-accounts create cr-vertice-backend \
  --project=vertice-ai \
  --display-name="Cloud Run SA - vertice-backend"

gcloud iam service-accounts create cr-vertice-mcp \
  --project=vertice-ai \
  --display-name="Cloud Run SA - vertice-mcp"

gcloud iam service-accounts create cr-vertice-frontend \
  --project=vertice-ai \
  --display-name="Cloud Run SA - vertice-frontend"

gcloud iam service-accounts create cr-ssrverticeai \
  --project=vertice-ai \
  --display-name="Cloud Run SA - ssrverticeai"
```

### 3.2 Conceder papéis mínimos

Vertex AI (necessário para backend e agent-gateway quando Vertex estiver habilitado; mcp se usar execução remota):
```bash
gcloud projects add-iam-policy-binding vertice-ai \
  --member="serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding vertice-ai \
  --member="serviceAccount:cr-vertice-backend@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding vertice-ai \
  --member="serviceAccount:cr-vertice-mcp@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

Secret Manager (apenas nos segredos usados):
```bash
gcloud secrets add-iam-policy-binding vertice-alloydb-dsn \
  --project=vertice-ai \
  --member="serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding stripe-secret-key \
  --project=vertice-ai \
  --member="serviceAccount:cr-vertice-backend@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3.3 Atualizar Cloud Run para usar as SAs
```bash
gcloud run services update vertice-agent-gateway \
  --project=vertice-ai --region=us-central1 \
  --service-account="cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com"

gcloud run services update vertice-backend \
  --project=vertice-ai --region=us-central1 \
  --service-account="cr-vertice-backend@vertice-ai.iam.gserviceaccount.com"

gcloud run services update vertice-mcp \
  --project=vertice-ai --region=us-central1 \
  --service-account="cr-vertice-mcp@vertice-ai.iam.gserviceaccount.com"

gcloud run services update vertice-frontend \
  --project=vertice-ai --region=us-central1 \
  --service-account="cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com"

gcloud run services update ssrverticeai \
  --project=vertice-ai --region=us-central1 \
  --service-account="cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com"
```

Validação:
```bash
gcloud run services list --project=vertice-ai --region=us-central1 --format="table(metadata.name,spec.template.spec.serviceAccountName,status.conditions[0].status)"
```

---

## 4) Quotas — SSD (us-central1) e Cloud Run CPU (us-central1)

### 4.1 SSD-TOTAL-GB-per-project-region (Compute) — us-central1

Evidência:
- limite atual: `250 GB`
- discos em `us-central1`: `200 GB` (2x `pd-balanced` de 100 GB)

Opção recomendada: solicitar aumento via QuotaPreference.
Exemplo (solicitar 2000 GB; ajuste conforme projeção):
```bash
gcloud beta quotas preferences create \
  --project=vertice-ai \
  --service=compute.googleapis.com \
  --quota-id=SSD-TOTAL-GB-per-project-region \
  --dimensions=region=us-central1 \
  --preferred-value=2000 \
  --preference-id=vertice-ssd-us-central1-2000 \
  --justification="GKE Autopilot cluster scaling + PV usage; avoid capacity disruption."
```

### 4.2 CpuAllocPerProjectRegion (Cloud Run) — us-central1

Limite atual:
- `20000m` (20 vCPU)

Como a recomendação do Recommender indicou 110%, a ação mais segura é:
- confirmar o uso/risco (console/metricas), e
- solicitar aumento preventivo se for necessário manter scaling alto.

Exemplo (solicitar 100000m = 100 vCPU; ajuste conforme necessidade):
```bash
gcloud beta quotas preferences create \
  --project=vertice-ai \
  --service=run.googleapis.com \
  --quota-id=CpuAllocPerProjectRegion \
  --dimensions=region=us-central1 \
  --preferred-value=100000 \
  --preference-id=vertice-run-cpu-us-central1-100000 \
  --justification="Cloud Run services scaling for SaaS launch; avoid throttling/deploy failures."
```

Validação do status das solicitações:
```bash
gcloud beta quotas preferences list --project=vertice-ai --reconciling-only
```

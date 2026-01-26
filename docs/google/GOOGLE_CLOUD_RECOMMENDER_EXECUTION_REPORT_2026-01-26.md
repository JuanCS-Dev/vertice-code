# Google Cloud — Execução das Ações (Recommender) (2026-01-26)

Data: **2026-01-26**
Projeto: **`vertice-ai`**
Região principal: **`us-central1`**

Este documento registra o que foi **aplicado** no GCP para endereçar as recomendações (Reliability/Security/Quota).

Planos e validação prévia:
- `docs/google/GOOGLE_CLOUD_RECOMMENDER_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/GOOGLE_CLOUD_RECOMMENDER_ACTION_PLAN_2026-01-26.md`

Inventário pós-mudança (evidência):
- `docs/google/_inventory/cloud_run_vertice-ai_summary_2026-01-26T16-27-43Z.md`
- `docs/google/_inventory/gke_clusters_vertice-ai_summary_2026-01-26T16-26-26Z.md`
- `docs/google/_inventory/iam_vertice-ai_summary_2026-01-26T16-26-15Z.md`

---

## 1) GKE — Backup Plan (Backup for GKE)

Aplicado:
- Backup plan criado: `vertice-backup-plan`
- Schedule (UTC): `10 3 * * *`
- Retenção: `14` dias
- Escopo: `--all-namespaces`
- Inclui: `--include-secrets` e `--include-volume-data`

Evidência (estado atual):
- `gcloud beta container backup-restore backup-plans describe vertice-backup-plan --location us-central1`
- Estado observado: `READY`
- Próximo backup agendado: `2026-01-27T03:10:00Z`

---

## 2) GKE — Maintenance Window (recorrente)

Aplicado:
- Janela recorrente diária (UTC): **22:00 → 04:00**
- Recorrência: `FREQ=DAILY`

Evidência:
- `gcloud container clusters describe vertice-cluster --region us-central1 --format=json | jq '.maintenancePolicy'`

---

## 3) Cloud Run — Service Accounts por serviço (least privilege)

Aplicado:
- Criadas service accounts dedicadas:
  - `cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
  - `cr-vertice-backend@vertice-ai.iam.gserviceaccount.com`
  - `cr-vertice-mcp@vertice-ai.iam.gserviceaccount.com`
  - `cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com`

IAM aplicado (mínimo necessário observado):
- `roles/aiplatform.user` no projeto para:
  - `cr-vertice-agent-gateway`, `cr-vertice-backend`, `cr-vertice-mcp`
- Secret Manager:
  - `vertice-alloydb-dsn`: `roles/secretmanager.secretAccessor` para `cr-vertice-agent-gateway`
  - `stripe-secret-key`: `roles/secretmanager.secretAccessor` para `cr-vertice-backend`

Cloud Run atualizado para usar SAs dedicadas:
- `vertice-agent-gateway`: OK (Ready=True)
- `vertice-backend`: OK (Ready=True)
- `vertice-mcp`: OK (Ready=True)
- `vertice-frontend`: OK (Ready=True)

⚠️ `ssrverticeai`:
- O serviço segue **respondendo 200** no endpoint público, porém está `Ready=False` porque:
  - o **latest created revision** falha com “Image not found” (Artifact Registry), impedindo novas revisões/escala segura.
  - o tráfego permanece em uma revisão pronta anterior (100%), o que mascara o risco até o próximo scale-out/rollout.
- Evidência:
  - `gcloud run revisions list --service ssrverticeai` mostra última revisão pronta, mas o “latest created” falha.
  - `python -c 'import urllib.request; print(urllib.request.urlopen(\"https://ssrverticeai-nrpngfmr6a-uc.a.run.app/\").status)'`
    retorna `200`.

Próxima ação recomendada (para fechar a recomendação com segurança):
- **Re-deploy** do `ssrverticeai` a partir da origem (para restaurar uma imagem existente no registry) e então reaplicar:
  - `--service-account=cr-ssrverticeai@...`

---

## 4) Quotas — solicitações via QuotaPreferences

Aplicado (solicitações criadas; não aprovadas automaticamente):

### 4.1 Compute SSD (us-central1)
- QuotaPreference criada: `vertice-ssd-us-central1-2000`
- Preferred: `2000` GB
- Granted atual: `250` GB
- Status: `stateDetail` indica que o valor preferido **não foi concedido** no momento.

### 4.2 Cloud Run CPU allocation (us-central1)
- QuotaPreference criada: `vertice-run-cpu-us-central1-100000`
- Preferred: `100000` mCPU (100 vCPU)
- Granted atual: `20000` mCPU (20 vCPU)
- Status: `stateDetail` indica que o valor preferido **não foi concedido** no momento.

Evidência:
- `gcloud beta quotas preferences describe <id> --project=vertice-ai`

---

## Smoke checks (pós-mudança)

- `vertice-agent-gateway`: `/openapi.json` OK
- `vertice-backend`: `/health` OK
- `vertice-mcp`: `/health` OK
- `vertice-frontend`: `GET /` OK
- `ssrverticeai`: `GET /` OK (mas com o risco de imagem ausente para novas revisões)

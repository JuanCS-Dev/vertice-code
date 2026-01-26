# Jules + Google Cloud — Incremento de Manutenção (2026-01-26)

Data: **2026-01-26**

Objetivo: preparar o repo para, após o frontend, configurar o Jules como “maintenance agent” com padrões oficiais do
Google Cloud (2026) e com guardrails de segurança.

## O que foi adicionado/atualizado

- Padrão de manutenção Google Cloud (runbooks/checklists):
  - `docs/google/GOOGLE_CLOUD_MAINTENANCE_BEST_PRACTICES_2026.md`
- Padrão Jules para manutenção automatizada (prompts + guardrails):
  - `docs/google/jules_integration/JULES_GCP_MAINTENANCE_AUTOMATION_2026.md`
  - `docs/google/jules_integration/JULES_WORKFLOW.md` (ADC + WIF, read-only first, impacto GCP em PR)
  - `docs/google/jules_integration/JULES_BACKLOG_PRs.md` (backlog de PRs de manutenção)
- Scripts read-only para inventário (para relatórios e auditoria contínua):
  - `tools/gcloud/inventory_cloud_run.sh`
  - `tools/gcloud/inventory_gke.sh`
  - `tools/gcloud/inventory_iam.sh`
  - outputs em `docs/google/_inventory/`

## Como usar (local, sem CI ainda)

Pré-requisitos:
- `gcloud` autenticado via ADC: https://cloud.google.com/docs/authentication/provide-credentials-adc
- `jq`

Comandos:
```bash
export GOOGLE_CLOUD_PROJECT="vertice-ai"
./tools/gcloud/inventory_cloud_run.sh
./tools/gcloud/inventory_gke.sh
./tools/gcloud/inventory_iam.sh
```

## Referências oficiais (Google Cloud)

- Architecture Framework:
  https://cloud.google.com/architecture/framework
- Cloud Operations:
  https://cloud.google.com/products/operations
- Cloud Run service identity:
  https://cloud.google.com/run/docs/securing/service-identity
- Workload Identity Federation:
  https://cloud.google.com/iam/docs/workload-identity-federation

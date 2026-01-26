# tools/gcloud (read-only)

Scripts de inventário e auditoria **read-only** para Google Cloud.

Princípios:
- Não executam `create/update/delete`.
- Não imprimem segredos.
- Geram relatórios em `docs/google/` com timestamp.
- Inventário de Cloud Run **redige valores** de env vars (guarda apenas nomes e `valueFrom`).

Pré-requisito (Google padrão):
- Autenticar localmente via ADC: https://cloud.google.com/docs/authentication/provide-credentials-adc

Uso rápido:
```bash
export GOOGLE_CLOUD_PROJECT="vertice-ai"   # opcional (ou gcloud config set project ...)
# Opcional: limitar regiões (csv) se Cloud Asset API não estiver habilitado
# export REGIONS="us-central1,southamerica-east1"
./tools/gcloud/inventory_cloud_run.sh
./tools/gcloud/inventory_gke.sh
./tools/gcloud/inventory_iam.sh
./tools/gcloud/inventory_cloud_functions_v2.sh
```

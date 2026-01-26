# Google Cloud — Checklist de Validação Contínua (2026)

Objetivo: reduzir risco operacional e “surpresas” (quebra, quota, custo, permissões) com validações frequentes e
automatizáveis.

Referências oficiais:
- Architecture Framework: https://cloud.google.com/architecture/framework
- Cloud Operations: https://cloud.google.com/products/operations
- Quotas: https://cloud.google.com/docs/quotas
- Budgets: https://cloud.google.com/billing/docs/how-to/budgets
- Cloud Run monitoring: https://cloud.google.com/run/docs/monitoring
- Backup for GKE: https://cloud.google.com/kubernetes-engine/docs/add-on/backup-for-gke
- Maintenance windows (GKE): https://cloud.google.com/kubernetes-engine/docs/how-to/maintenance-windows
- Cloud Run service identity: https://cloud.google.com/run/docs/securing/service-identity

---

## A) Diário (pós-deploy e “saúde”)

- Cloud Run: confirmar `Ready=True` (serviços críticos) e checar endpoints de saúde/smoke.
- Error Reporting: verificar novos erros agregados.
- Monitoring: verificar alertas abertos e tendências de latência/erro.
- Logs: verificar picos de 5xx/4xx e erros de conexão (ex.: VPC connector / DB).

Automação sugerida (read-only):
- Gerar inventário e status:
  - `./tools/gcloud/inventory_cloud_run.sh`
  - `./tools/gcloud/inventory_cloud_functions_v2.sh` (cobre Firebase/App Hosting SSR functions como `ssrverticeai`)

---

## B) Semanal (confiabilidade + segurança + custo)

- Recommender: revisar recomendações (Security/Reliability/Cost) e priorizar as “high impact”.
- IAM: revisar permissões excessivas (especialmente `roles/editor`), service accounts por serviço, e acessos a secrets.
- Quotas: revisar uso e tendência para evitar interrupção.
- Budgets: revisar alertas e gasto acumulado.

Automação sugerida (read-only):
- IAM snapshot:
  - `./tools/gcloud/inventory_iam.sh`
- GKE snapshot:
  - `./tools/gcloud/inventory_gke.sh`

---

## C) Mensal (dados + DR + governança)

- Backup/restore drill (ideal): restaurar backup em ambiente isolado e validar integridade.
- Rotação de segredos (Secret Manager/KMS) conforme política.
- Revisão de SLOs/alertas (ruído x cobertura).

---

## D) Tradução prática das recomendações vistas no console (17 JAN 2026)

### 1) GKE — “Create a backup plan” / “Set maintenance window”
Quando aplicar:
- cluster com workloads importantes (produção / pré-prod com dados) e risco de interrupção.

Ações:
- Criar Backup Plan (Backup for GKE) e definir retenção.
- Definir maintenance windows e exclusions.

### 2) Cloud Run — “Create new service account with minimal permissions”
Quando aplicar:
- serviços em produção ou com acesso a dados/segredos (backend, mcp, agent-gateway, frontend).

Ações:
- Criar 1 service account por serviço.
- Conceder apenas papéis necessários (ex.: secretAccessor apenas para segredos usados).
- Atualizar Cloud Run para usar a service account dedicada.

### 3) Quotas — `compute.googleapis.com` SSD e `run.googleapis.com` CPU alloc por região
Quando aplicar:
- quando a quota está alta (80%+) ou já excedida.

Ações:
- Identificar recursos que consomem quota.
- Ajustar autoscaling/recursos quando possível.
- Solicitar aumento de quota quando necessário.
- Configurar alertas proativos.

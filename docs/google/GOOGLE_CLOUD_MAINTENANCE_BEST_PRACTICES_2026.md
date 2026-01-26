# Google Cloud — Manutenção e Operação (Padrão 2026)

Este documento consolida práticas oficiais do Google Cloud para operar e manter o stack (Cloud Run, GKE, AlloyDB,
IAM, Secret Manager, Observability). Ele é o “padrão” para o sistema nervoso do backend e para automações futuras.

Base oficial (leitura recomendada):
- Google Cloud Architecture Framework (Operational Excellence / Reliability / Security / Cost):
  - https://cloud.google.com/architecture/framework
- Cloud Operations (Logging/Monitoring/Alerting):
  - https://cloud.google.com/products/operations
- Authentication: ADC (local) e Workload Identity Federation (CI/CD):
  - https://cloud.google.com/docs/authentication/provide-credentials-adc
  - https://cloud.google.com/iam/docs/workload-identity-federation

---

## 1) Identidade, credenciais e “least privilege”

Checklist:
- Preferir identidades gerenciadas (Service Accounts) e ADC; **evitar API keys** e **evitar chaves long-lived**.
- Para Cloud Run: usar **1 Service Account por serviço** (backend, agent-gateway, mcp, frontend) e conceder apenas os
  papéis mínimos necessários.
- Evitar “basic roles” (`roles/editor`, `roles/owner`) em workloads.
- Revisar com frequência: IAM Recommender, Policy Analyzer, Audit Logs.

Docs oficiais:
- Cloud Run Service Identity / Service Accounts:
  https://cloud.google.com/run/docs/securing/service-identity
- IAM best practices:
  https://cloud.google.com/iam/docs/using-iam-securely

---

## 2) Segredos e chaves (Secret Manager + KMS)

Checklist:
- Armazenar segredos em **Secret Manager** (não em `.env` no repo, não em variáveis de build, não em chat).
- Preferir **CMEK** quando exigido por compliance (KMS).
- Rotacionar segredos com política (ex.: mensal/trimestral) e registrar dono/impacto.
- Garantir que workloads só tenham `roles/secretmanager.secretAccessor` para os segredos necessários.

Docs oficiais:
- Secret Manager overview + best practices:
  https://cloud.google.com/secret-manager/docs/overview
- Cloud KMS:
  https://cloud.google.com/kms/docs

---

## 3) Observabilidade (Logs, métricas, tracing, erros)

Checklist (mínimo para produção):
- Logging: logs estruturados, correlação por `trace/span`, retenção e exclusões quando necessário.
- Monitoring: dashboards para taxa de erro, latência (p50/p95/p99), saturação e filas.
- Alerting: políticas por SLO/burn-rate (evitar alertas por “spike” isolado).
- Error Reporting + Trace + Profiler (quando aplicável).
- Uptime checks para endpoints críticos e “synthetics” simples (smoke).

Docs oficiais:
- Cloud Logging:
  https://cloud.google.com/logging/docs
- Cloud Monitoring:
  https://cloud.google.com/monitoring/docs
- Alerting policies:
  https://cloud.google.com/monitoring/alerts
- Cloud Trace:
  https://cloud.google.com/trace/docs
- Error Reporting:
  https://cloud.google.com/error-reporting/docs

---

## 4) Cloud Run (operação, deploys e rollback)

Checklist:
- Definir health endpoints e validar via **Uptime checks** + “smoke” pós-deploy.
- Configurar limites de autoscaling (min/max instances) e CPU/memória alinhados à carga.
- Usar tráfego por revisões (canary/gradual rollout) quando fizer sentido.
- Configurar acesso a recursos privados via Serverless VPC Access apenas quando necessário (egress controlado).
- Garantir que o serviço exponha métricas/telemetria e logs suficientes para troubleshooting rápido.

Docs oficiais:
- Deploying / revisions / traffic management:
  https://cloud.google.com/run/docs/deploying
- Monitoring Cloud Run:
  https://cloud.google.com/run/docs/monitoring
- Serverless VPC Access:
  https://cloud.google.com/vpc/docs/serverless-vpc-access

---

## 5) GKE (confiabilidade: backups e manutenção)

Checklist:
- Definir janela de manutenção (maintenance window) e exclusões (ex.: datas críticas).
- Configurar **Backup for GKE** (backup plan) com retenção alinhada a RPO/RTO.
- Definir estratégia de upgrade (surge, max unavailable) e validar compatibilidade.

Docs oficiais:
- Backup for GKE:
  https://cloud.google.com/kubernetes-engine/docs/add-on/backup-for-gke
- Maintenance windows:
  https://cloud.google.com/kubernetes-engine/docs/how-to/maintenance-windows

---

## 6) AlloyDB (dados: backup, alta disponibilidade, DR)

Checklist:
- Confirmar estratégia de backup e retenção (e.g., PITR se habilitado).
- Confirmar conectividade segura (privado via VPC) e controle de acesso.
- Monitorar: conexões, latência, storage, erros.

Docs oficiais:
- AlloyDB for PostgreSQL:
  https://cloud.google.com/alloydb/docs

---

## 7) Cotas, custos e proteção contra surpresa

Checklist:
- Monitorar cotas críticas (Cloud Run CPU alloc per region, SSD total por região, etc.) e criar alertas.
- Configurar budgets e alertas de billing (com notificação).
- Revisar Recommender (security/reliability/cost) semanalmente.

Docs oficiais:
- Budgets & alerts (Billing):
  https://cloud.google.com/billing/docs/how-to/budgets
- Quotas:
  https://cloud.google.com/docs/quotas
- Recommender:
  https://cloud.google.com/recommender/docs

---

## 8) Rotina operacional (checklists)

### Diário (10–15 min)
- Verificar erros/alertas (Monitoring + Error Reporting).
- Verificar taxa de erro e latência dos serviços críticos (Cloud Run / gateway).
- Verificar “deploys das últimas 24h” e rollback readiness.

### Semanal (30–60 min)
- Revisar Recommender (Security/Reliability/Cost).
- Revisar IAM (mudanças, permissões excessivas, service accounts).
- Revisar quotas (tendência de consumo) e budgets.

### Mensal
- Rotação de segredos conforme política (Secret Manager/KMS).
- Revisão de SLOs e tuning de alertas.
- Revisão de DR/backup restore drills (ao menos “tabletop”, idealmente restore real em ambiente isolado).

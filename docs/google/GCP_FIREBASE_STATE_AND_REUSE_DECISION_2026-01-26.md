# GCP/Firebase State Audit + Reuse vs Rebuild Decision (2026-01-26)

## Objetivo
Validar o que **realmente existe** no Google Cloud/Firebase (pós-redeploy) e decidir:
- Reaproveitar Firebase antigo vs configurar do zero
- O que é “legado” e pode virar candidato a desativação (sem deletar agora)

> Política: nenhuma ação destrutiva (delete/limpeza) sem confirmação explícita.

---

## Contexto (gcloud/firebase CLI)
- Projeto ativo (gcloud): `vertice-ai`
- Conta ativa (gcloud): `juancs.d3v@gmail.com`
- Firebase projects visíveis no CLI:
  - `vertice-ai` (current)
  - `protovolt-studio`
  - `clinica-genesis-os-e689e`

---

## Inventário — Cloud Run (us-central1)
Serviços encontrados:
- `vertice-frontend` (atualizado em **2026-01-26**)
- `vertice-backend`
- `vertice-mcp`
- `vertice-agent-gateway`
- `ssrverticeai`

Observações:
- `vertice-frontend` e `vertice-backend` estão **públicos** (`roles/run.invoker` para `allUsers`).
  - Isso pode ser aceitável se o backend exige auth forte (JWT/OIDC) e há proteção adicional (Cloud Armor / rate limit),
    mas é um ponto de hardening a planejar.
- Service Accounts dedicados já existem (bom sinal):
  - `cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `cr-vertice-backend@vertice-ai.iam.gserviceaccount.com`
  - `cr-vertice-mcp@vertice-ai.iam.gserviceaccount.com`

IAM (visão parcial por policy do projeto):
- `cr-vertice-backend` → `roles/aiplatform.user`
- `cr-vertice-mcp` → `roles/aiplatform.user`
- `cr-vertice-frontend` → (nenhum role no nível do projeto detectado via filtro)

Conclusão: a recomendação “Create new service account with minimal permissions” **faz sentido como hardening**, mas
**não é urgente** se o sistema já está funcional. O próximo passo seguro é inventariar exatamente quais recursos
(Secret Manager/Firestore/Vertex/etc) cada serviço acessa e reduzir para “least privilege” com testes/smoke.

---

## Inventário — GKE (Autopilot) + Backups
Cluster:
- `vertice-cluster` em `us-central1` (RUNNING, canal `REGULAR`)

Maintenance window:
- Recorrente diária configurada: **22:00Z → 04:00Z**
  - Portanto a recomendação “Set maintenance window” está **OK** (já aplicado).

Backup for GKE:
- Backup plan existe: `vertice-backup-plan`
- Retenção: **14 dias**
- Escopo: all namespaces + inclui secrets + inclui volume data
- **Ação aplicada (safe minimum):** definido cron schedule **UTC**: `10 2 * * *`
  - Próximo backup agendado: `2026-01-27T02:10:00Z`
- Backup manual disparado para validação:
  - `manual-20260126-1720` → **SUCCEEDED** (2026-01-26)

---

## Inventário — Quotas (Compute SSD)
Região `us-central1`:
- Quota `SSD_TOTAL_GB`: **200 GB usados / 250 GB limite (80%)**
  - Discos observados: 2× `pd-balanced` de 100GB (provavelmente ligados ao GKE).

Recomendação: faz sentido monitorar (e potencialmente pedir aumento) antes de crescer o cluster/volumes.

---

## Inventário — Firebase (vertice-ai)
Firebase Hosting:
- Site: `vertice-ai` → `https://vertice-ai.web.app`
- Canal `live` com último release em: **2026-01-16 15:12:12**

Firebase App Hosting:
- Backends:
  - `us-central1` → `https://us-central1--vertice-ai.us-central1.hosted.app` (updated 2026-01-09)
  - `vertice-us` → `https://vertice-us--vertice-ai.us-central1.hosted.app` (updated 2026-01-10)

Config no repo (sinal forte de “legado”):
- `firebase.json` (raiz) aponta App Hosting para `vertice-chat-webapp/frontend` (Next antigo),
  não para `apps/web-console`.

Conclusão: Firebase Hosting/App Hosting parecem **legado ativo (mas mais antigo)**; Cloud Run frontend foi atualizado
hoje (2026-01-26), então provavelmente a “fonte de verdade” mudou para Cloud Run.

---

## Decisão recomendada (sem destruir nada)

### Opção A — Manter Cloud Run como padrão (recomendado agora)
- Pros:
  - Já está atualizado hoje (2026-01-26), consistente com o redeploy.
  - Evita duplicidade (Cloud Run + App Hosting fazendo a mesma coisa).
- Contras:
  - Você carrega custos/complexidade do Firebase legado até cortar.

### Opção B — Voltar para Firebase App Hosting (rebuild para o novo frontend)
- Pros:
  - Deploy/rollouts de Next mais “opinionated”, com integração nativa Firebase.
- Contras:
  - Exige recriar App Hosting backend para `apps/web-console`, ajustar secrets/env e cortar tráfego.

### “Limpar Firebase”
Não recomendado fazer agora. O caminho seguro é:
1) Confirmar qual URL/domínio está em produção (Cloud Run vs Firebase).
2) Congelar recursos legados (sem novos deploys).
3) Fazer cutover controlado (DNS/Traffic) e monitorar.
4) Só então, com checklist, aprovar deletar (site/backend/apps) um por um.

---

## Comandos (read-only) para revalidar
- Cloud Run inventory: `gcloud run services list --platform managed --region us-central1`
- Cloud Run public access: `gcloud run services get-iam-policy <service> --region us-central1`
- GKE maintenance: `gcloud container clusters describe vertice-cluster --region us-central1 --format='yaml(maintenancePolicy)'`
- Backup plan: `gcloud beta container backup-restore backup-plans describe vertice-backup-plan --location us-central1`
- Backup status: `gcloud beta container backup-restore backups list --location us-central1 --backup-plan vertice-backup-plan`
- Firebase hosting channels: `firebase hosting:channel:list --project vertice-ai`
- Firebase App Hosting: `firebase apphosting:backends:list --project vertice-ai`

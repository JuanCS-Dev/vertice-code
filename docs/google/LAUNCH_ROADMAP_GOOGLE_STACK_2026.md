# Launch Roadmap (Executável) — Vertice SaaS na Google Stack (2026-01-26)

Objetivo: lançar o SaaS com **wiring production-ready** (frontend ↔ backend ↔ auth ↔ multi-tenant), eliminando caminhos
legados por um cutover controlado, seguindo o padrão oficial do Google Cloud/Firebase.

## Segurança operacional (regras “não negociáveis”)

- Nunca coloque chaves/tokens/JSON de service account no repo ou em docs. Use **ADC** no local e **Secret Manager**
  (com IAM) em produção.
- Mudanças em IAM/Cloud Run/GKE devem ter:
  - inventário antes/depois em `docs/google/_inventory/`
  - rollback em 1–2 comandos
  - validação (smoke) imediata

## Como executar (protocolo para um executor “menos capaz”, ex.: GPT‑5.1)

Regras (para não quebrar produção):
1) **Read-only primeiro.** Antes de mudar qualquer coisa no GCP, gere um inventário e compare com este documento.
2) **Mudanças em PRs pequenas.** Um bloco de trabalho = 1 PR (ou 1 “execução” em produção) com critérios de aceite claros.
3) **Sem deletes sem aprovação explícita.** “Decommission” só em `M6` e com confirmação humana.
4) **Sempre com rollback definido.** Toda etapa que mexe em Cloud Run/IAM deve ter rollback em 1 comando.
5) **Fixar por data.** Se algo conflitar, use datas absolutas e atualize o roadmap (não “assuma”).

Quickstart (inventário mínimo, barato):
```bash
gcloud config get-value project
gcloud run services list --platform managed --region us-central1
gcloud run services list --platform managed --region southamerica-east1
gcloud run services get-iam-policy vertice-frontend --region us-central1
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1
gcloud container clusters list --region us-central1
```

Regra de inventário: salve outputs em `docs/google/_inventory/` com timestamp UTC (para diff/rollback).
Exemplo:
```bash
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
gcloud run services list --platform managed --region us-central1 --format=json > "docs/google/_inventory/run_services_us-central1_${TS}.json"
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1 --format=json > "docs/google/_inventory/iam_vertice-agent-gateway_${TS}.json"
```

## Índice rápido (marcos e PRs)

Legenda:
- `M*` = marco (sequência recomendada / dependências).
- `PR-L*` = launch infra/wiring.
- `PR-F*` = frontend.
- `PR-M*` = manutenção/ops (SRE).

Ordem recomendada (execução):
1) `M0` → `M0.1` (drift + freeze)
2) `M1` → `M1.1` (auth + IAM)
3) `M2` (wiring UX + stream + artifacts)
4) `M3` (multi-tenant “real” + dados)
5) `M4` (ops hardening em paralelo)
6) `M5` (cutover)
7) `M6` (decommission, só após aprovação)

Mapa (marco → PRs):
| Marco | PRs principais |
|---|---|
| `M0/M0.1` | `PR-L0` |
| `M1/M1.1` | `PR-L1`, `PR-F2` |
| `M2` | `PR-F4`, `PR-F4.1`, `PR-F5` |
| `M3` | `PR-L3` (+ decisões Firestore/AlloyDB) |
| `M4` | `PR-M1..PR-M6`, `PR-L4` |
| `M5` | (cutover runbook) |
| `M6` | (decommission runbook) |

Backlog canônico (fonte única): seção `PR-INDEX` neste arquivo.

## Status (o que já foi concluído neste repo) — 2026-01-26

Este bloco existe para que outro modelo (ex.: GPT‑5.1) consiga continuar sem “redescobrir” o que já está pronto.

✅ Concluído (código + validação local)
- Frontend `apps/web-console`: login Google (Firebase Auth), sessão via cookie `__session`, rotas protegidas, proxy
  `/api/gateway/*` com service-to-service ID token (Cloud Run), org selection via cookie `vertice_org`.
- Frontend `apps/web-console`: hardening web básico — headers de segurança (HSTS, CSP mínimo, XFO, etc), remoção de
  `X-Powered-By` e bloqueio de POST cross-origin (Origin/Referer) em rotas cookie-auth.
- Frontend `apps/web-console`: Cloud Run service-to-service auth preferindo `X-Serverless-Authorization` (deixa
  `Authorization` livre para auth de usuário final quando necessário).
- Backend `apps/agent-gateway`: auth (`X-Vertice-User` ou `Authorization: Bearer <Firebase ID token>`), tenancy
  (org/workspace), store (Memory local + Firestore em Cloud Run), endpoints `/v1/me`, `/v1/orgs`, `/v1/runs`,
  `/agui/stream`.
- Validações rodadas:
  - `cd apps/web-console && npx tsc -p tsconfig.json --noEmit && npm run lint`
  - `ruff check`/`ruff format --check` nos arquivos do gateway + `pytest tests/integration/test_agent_gateway_agui_stream.py`

✅ Concluído (auditoria read-only no GCP)
- Cloud Run (us-central1): `vertice-frontend`, `vertice-agent-gateway`, `vertice-backend`, `vertice-mcp`, `ssrverticeai`
- GKE Autopilot: maintenance window configurada; Backup for GKE com backup plan existente.
- Recommender: itens de GKE (backup/maintenance) endereçados; quota SSD em `us-central1` permanece risco real.

✅ Concluído (execução em produção — 2026-01-26)
- Corrigido drift do `vertice-agent-gateway`:
  - Cloud Build (us-central1): `741e1269-237b-4fe2-94f5-6c1e4995e90b`, `d81276ba-492d-4d3b-9488-ba9ab9620176`,
    `99ad288a-ad54-4f40-9ae7-b932a0ce89a1`
  - Imagem final (pin): `agent-gateway@sha256:babb430ea06f55fd71d6f7d9bfa2b8ab0ea472a89915f7e66060ee45c34c0c1e`
  - Revision final: `vertice-agent-gateway-00007-kmb`
  - Smoke (antes do hardening IAM ou autenticado): `GET /healthz/` e `GET /readyz/` retornam **200** (nota: usar sempre o `/` final).
- Hardening IAM (Cloud Run):
  - `vertice-agent-gateway`, `vertice-backend`, `vertice-mcp`: removido `allUsers` (privados)
  - `vertice-frontend`: mantido público
  - Inventário antes/depois: `docs/google/_inventory/iam-*-{before,after}-2026-01-26.json`

⚠️ Pendente (próximas execuções / para outro executor)
- Validar service-to-service “real” (frontend SA → gateway, gateway SA → backend, backend SA → mcp) com chamada assinada
  (não foi possível gerar ID token via impersonation local por falta de permissão no operador).
- Decidir destino do legado (`ssrverticeai` e Firebase/App Hosting) após redeploy do frontend novo.

Relatórios relacionados:
- `docs/google/EXECUTION_REPORT_WIRING_FRONTEND_BACKEND_2026-01-26.md`
- `docs/google/GOOGLE_CLOUD_POST_DEPLOY_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/GOOGLE_CLOUD_RECOMMENDER_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/FRONTEND_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/FRONTEND_UX_DRAFTS_IMPLEMENTATION_AUDIT_2026-01-26.md` (drafts UX vs wiring real)

Referências internas (estado real já auditado):
- `docs/google/GCP_FIREBASE_STATE_AND_REUSE_DECISION_2026-01-26.md`
- `docs/google/GOOGLE_CLOUD_POST_DEPLOY_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/GOOGLE_CLOUD_RECOMMENDER_ACTION_PLAN_2026-01-26.md`
- `docs/google/FRONTEND_VALIDATION_REPORT_2026-01-26.md`
- `docs/google/jules_integration/JULES_GCP_MAINTENANCE_AUTOMATION_2026.md`
- `docs/google/EXECUTION_REPORT_WIRING_FRONTEND_BACKEND_2026-01-26.md`

Docs oficiais (Google) usadas como base (links no **Anexo Z**):
- Cloud Run (end-users, public access, service-to-service, Binary Authorization)
- Secret Manager + Cloud Run
- Firebase Auth/Identity Platform (ID tokens + session cookies)
- Cloud Monitoring (uptime checks)
- Cloud Armor (rate limiting; opcional)
- IAM (Workload Identity Federation; recomendado para CI/CD)

---

## 0) Estado atual (resumo do que “existe de verdade”)

Projeto: `vertice-ai`

Cloud Run (observado em 2026-01-26, `us-central1`):
- `vertice-frontend` (atualizado 2026-01-26)
- `vertice-agent-gateway`
- `vertice-backend`
- `vertice-mcp`
- `ssrverticeai` (candidato a legado)
Nota de segurança (IMPORTANTE): em 2026-01-26 o padrão foi aplicado: **frontend público** e **backends privados**
(`vertice-agent-gateway`, `vertice-backend`, `vertice-mcp`) invocáveis apenas por service accounts.

Nota de engenharia (IMPORTANTE): houve drift no `vertice-agent-gateway` (rodando imagem `vertice-cloud/backend`), e
`GET /healthz` retornava **404** no edge. O drift foi corrigido em 2026-01-26 com a imagem dedicada do gateway e a rota
padronizada para `GET /healthz/` (com `/` final).

GKE (observado em 2026-01-26, `us-central1`):
- `vertice-cluster` (Autopilot)
- Maintenance window já configurada (22:00Z → 04:00Z)
- Backup for GKE com cron diário configurado e backup manual validado “SUCCEEDED”

Firebase (observado em 2026-01-26):
- Hosting `vertice-ai.web.app` e App Hosting backends (`us-central1`, `vertice-us`) com updates **mais antigos**
- `firebase.json` da raiz aponta para `vertice-chat-webapp/frontend` (Next antigo), não para `apps/web-console`

Conclusão operacional para o lançamento: **Cloud Run é o caminho primário**; Firebase/App Hosting ficam como
**legado ativo (congelado)** até cutover + validação.

---

## 1) Arquitetura alvo v1 (safe minimum para lançar)

Decisões confirmadas (2026-01-26):
- Frontend canônico: **Cloud Run** (manter `vertice-frontend` como fonte de verdade e evitar migração agora).
- Auth MVP: **Google-only** (Identity Platform / Firebase Auth).
- SaaS MVP: **multi-tenant SIM** (org/workspace + RBAC mínimo).

Padrão (Google):
- Frontend público: `apps/web-console` (Next) servido por `vertice-frontend` (Cloud Run).
- API pública (por enquanto): `vertice-agent-gateway` (Cloud Run) com endpoints streaming (SSE/AG-UI).
  - **Hardening recomendado**: tornar `vertice-agent-gateway` privado e invocável apenas pelo frontend (IAM invoker).
- Autenticação de usuários finais: **Identity Platform (ou Firebase Authentication equivalente)** no mesmo projeto.
  - Frontend obtém ID token e chama API via `Authorization: Bearer <ID_TOKEN>`.
  - Backend valida ID token (Admin SDK/JWT) em cada request (stateless).
  - Nota: Cloud Run não garante session affinity; trate o backend como stateless e use store externo quando necessário.
- Segredos: Secret Manager (sem chaves long-lived no repo; preferir ADC local e WIF no CI).
- Observabilidade mínima: Cloud Logging + Monitoring (latência/erros) + alertas de orçamento/cotas.

---

## 2) Roadmap por marcos (comandos + critérios de aceite)

### M0 — Freeze + inventário “fonte da verdade” (0.5 dia)
Objetivo: impedir drift e travar o que é “produção”.

Checklist:
- [ ] Definir explicitamente “prod URL” atual (Cloud Run vs Firebase) e documentar em `docs/google/`.
- [ ] Validar “imagem correta” por serviço Cloud Run (evitar drift):
  - `vertice-agent-gateway` deve apontar para a imagem do gateway (monorepo / `Dockerfile.backend`), não para a imagem
    do backend legado.
- [ ] Congelar deploys no caminho legado (sem deletar nada):
  - parar de usar `vertice-chat-webapp/deploy-gcp.sh` para produção.
  - evitar `firebase deploy` para o site `vertice-ai` até o cutover.
- [ ] Marcar Cloud Run como canônico para o frontend (decisão aplicada neste roadmap).

Comandos (read-only):
```bash
gcloud config get-value project
gcloud run services list --platform managed --region us-central1
gcloud run services get-iam-policy vertice-frontend --region us-central1
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1
firebase hosting:channel:list --project vertice-ai
firebase apphosting:backends:list --project vertice-ai
```

Aceite:
- Produção tem **um** caminho “canônico” documentado (Cloud Run recomendado no estado atual).
- Legado está “read-only / sem deploy” (por processo, não por delete).

---

### M0.1 — Corrigir drift do `vertice-agent-gateway` (prioridade P0) (0.5 dia)

Objetivo: garantir que o serviço Cloud Run `vertice-agent-gateway` rode a **imagem do gateway** (monorepo) e volte a
expor endpoints esperados (`/healthz/` 200), antes de endurecer IAM.

Pré-checagens (read-only):
```bash
gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.url)'
gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.latestReadyRevisionName)'
gcloud run revisions describe "$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.latestReadyRevisionName)')" \
  --region us-central1 --format='value(spec.containers[0].image)'
```

Smoke test (read-only) — preferir `/healthz/` (com `/` final):
```bash
python - <<'PY'
import subprocess, urllib.request, urllib.error
ag = subprocess.check_output(
  ["gcloud","run","services","describe","vertice-agent-gateway","--region","us-central1","--format","value(status.url)"]
).decode().strip()
for path in ["/openapi.json","/healthz/","/readyz/"]:
  try:
    with urllib.request.urlopen(ag + path, timeout=20) as resp:
      print(path, resp.status)
  except urllib.error.HTTPError as e:
    print(path, e.code)
PY
```

Plano de execução (produção) — **recomendado criar imagem dedicada**
1) Build & push (Cloud Build) de uma imagem **separada** para o gateway:
   - Nome sugerido: `us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/agent-gateway:latest`
2) Deploy do Cloud Run `vertice-agent-gateway` apontando para essa imagem.

Comandos (execução) — recomendado (reprodutível) via `cloudbuild.agent-gateway.yaml`:
```bash
# (A) build + push (Cloud Build)
gcloud builds submit --region us-central1 --config cloudbuild.agent-gateway.yaml .

# (B) deploy (pinar digest; preserva SA/secret/vpc já configurados no serviço)
DIGEST="$(gcloud builds describe <BUILD_ID> --region us-central1 --format='value(results.images[0].digest)')"
gcloud run services update vertice-agent-gateway \
  --region us-central1 \
  --image "us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/agent-gateway@${DIGEST}"
```

Aceite:
- `GET /openapi.json` = 200
- `GET /healthz/` = 200
- `GET /readyz/` = 200
- `/agui/stream` retorna SSE (com token, após hardening; antes do hardening pode validar “estrutura” em ambiente dev)

Rollback (rápido):
```bash
# Capture a revisão anterior ANTES do deploy:
# PREV_REV="$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.latestReadyRevisionName)')"
#
# Se o deploy quebrar, volte tráfego para a revisão anterior:
gcloud run services update-traffic vertice-agent-gateway \
  --region us-central1 \
  --to-revisions "$PREV_REV=100"
```

---

### M1 — Autenticação (Identity Platform/Firebase Auth) + proteção de API (1–2 dias)
Objetivo: login real + proteger endpoints do backend (SaaS-ready).

Decisões mínimas:
- Provedor inicial: **Google-only**.
- Multi-tenant: adiar para M3, a menos que seja requisito imediato.

Passos:
1) Habilitar Identity Platform no projeto (console) e configurar provedores.
2) Frontend (`apps/web-console`):
   - adicionar fluxo de login/logout com Firebase Auth client.
   - obter ID token (web) e anexar em todas as chamadas para a API.
3) Backend (`vertice-agent-gateway`):
   - middleware para validar ID token em requests (SSE incluído) e rejeitar sem token.
   - diferenciar endpoints públicos (ex.: `/healthz/` quando o serviço for público) de endpoints protegidos.

Critérios de aceite:
- [ ] Usuário não autenticado recebe 401 ao chamar endpoints protegidos.
- [ ] Usuário autenticado consegue iniciar stream (SSE) e receber eventos.
- [ ] Auditoria mínima: logar `uid` (não PII sensível), latency e erros.

Smoke tests (exemplos):
```bash
# OBS (2026-01-26): antes do hardening IAM (`M1.1`), `GET /healthz/` era acessível publicamente.
# Após `M1.1` (gateway privado), chamadas anônimas devem retornar 401/403.
#
# 1) Antes do hardening IAM (ou em ambiente de teste público)
curl -i "$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.url)')/healthz/"

# 2) endpoint protegido sem token deve falhar
curl -i "$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.url)')/agui/stream"
```

Status em 2026-01-26:
- ✅ Frontend tem login Google + session cookie `__session` e proteção de rotas (`apps/web-console/middleware.ts`).
- ✅ Backend suporta `Authorization: Bearer <Firebase ID token>` (fallback) e `X-Vertice-User` (proxy).
- ✅ IAM do Cloud Run endurecido (backend privado) — ver M1.1.

---

### M1.1 — Hardening Cloud Run IAM (padrão Google) (P0) (0.5–1 dia)

Objetivo: deixar **apenas o frontend público** e restringir invocação do `vertice-agent-gateway` (e opcionalmente
`vertice-backend`/`vertice-mcp`) apenas a service accounts necessárias.

Dependências (estado atual do código):
- `apps/web-console` faz chamadas server-side ao gateway e já anexa **ID token** para audiência Cloud Run.

Pré-checagens (read-only):
```bash
gcloud run services get-iam-policy vertice-frontend --region us-central1
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1
gcloud run services describe vertice-frontend --region us-central1 --format='value(spec.template.spec.serviceAccountName)'
```

Plano recomendado (executável, com rollback):
1) Adicionar invoker permitido (SA do frontend).
2) Remover `allUsers` do gateway.
3) Validar `/dashboard` (stream) e `/artifacts` (runs).
4) Repetir para outros serviços somente quando houver certeza de dependência.

Comandos (execução) — **gateway**
```bash
FRONTEND_SA="$(gcloud run services describe vertice-frontend --region us-central1 --format='value(spec.template.spec.serviceAccountName)')"

gcloud run services add-iam-policy-binding vertice-agent-gateway \
  --region us-central1 \
  --member="serviceAccount:${FRONTEND_SA}" \
  --role="roles/run.invoker"

gcloud run services remove-iam-policy-binding vertice-agent-gateway \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

Validação pós-mudança (smoke):
```bash
AG_URL="$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.url)')"
curl -sS -o /dev/null -w '%{http_code}\n' "$AG_URL/openapi.json"   # deve virar 403/401 sem credencial
```

Rollback (se quebrar produção):
```bash
gcloud run services add-iam-policy-binding vertice-agent-gateway \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

Aplicado em 2026-01-26 (estado atual)
- `vertice-agent-gateway` invokers:
  - `serviceAccount:cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com`
- `vertice-backend` invokers:
  - `serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com`
- `vertice-mcp` invokers:
  - `serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-vertice-backend@vertice-ai.iam.gserviceaccount.com`
- Inventário antes/depois (commitável):
  - `docs/google/_inventory/iam-vertice-agent-gateway-before-2026-01-26.json`
  - `docs/google/_inventory/iam-vertice-agent-gateway-after-2026-01-26.json`
  - `docs/google/_inventory/iam-vertice-backend-before-2026-01-26.json`
  - `docs/google/_inventory/iam-vertice-backend-after-2026-01-26.json`
  - `docs/google/_inventory/iam-vertice-mcp-before-2026-01-26.json`
  - `docs/google/_inventory/iam-vertice-mcp-after-2026-01-26.json`

Validação pós-hardening (para outro executor)
- Checagem rápida (anon deve dar 403):
  - gateway/backend: `GET /healthz/` → 403
- Checagem service-to-service “real”:
  - Rodar a chamada a partir do runtime do `vertice-frontend` (server) para `vertice-agent-gateway` e validar `200`
    (confirma ID token + IAM).
  - Se for indispensável validar local via impersonation, o operador precisa de `roles/iam.serviceAccountTokenCreator`
    no `cr-vertice-frontend@...` (evitar por padrão; preferir validação via runtime ou Cloud Run Job).

---

### M2 — Wiring do frontend para “claude-code-web style” (2–4 dias)
Objetivo: tornar o app usável end-to-end (UI + stream + artifacts).

Passos (mínimo):
- [ ] Implementar “adapter” no frontend (API route ou client) para:
  - criar task, iniciar SSE, reconectar (backoff) e renderizar stream
  - exibir artifacts e status
- [ ] Estados de UX (carregando, erro, offline, reconexão)
- [ ] Hardening básico de UI:
  - headers (CSP / X-Frame-Options / etc) conforme padrão Next/Cloud Run
  - sanitização ao renderizar conteúdo gerado (markdown/artifacts)

Aceite:
- [ ] `/dashboard` inicia uma execução real via `vertice-agent-gateway`.
- [ ] Stream funciona por pelo menos 10 minutos sem quebrar (reconexão ok).
- [ ] Artifacts persistem em UI pelo menos durante a sessão (armazenamento local ou backend).

Status em 2026-01-26:
- ✅ `/dashboard` inicia stream real via `/api/gateway/stream` (proxy → `vertice-agent-gateway`).
- ✅ `/artifacts` lista “Recent Runs” (proxy → `/v1/runs`).
- ✅ `/settings` gerencia orgs (list/create/select) e define org ativo (cookie `vertice_org`).

Próximo “pacote executável” (para GPT‑5.1):
- Implementar reconexão/retries no SSE (backoff) e “resume” por `run_id` (backend já expõe `/v1/runs/{run_id}`).
- Implementar artifacts persistentes (no backend) e renderização segura (sanitização).

---

### M3 — Dados + multi-tenant + billing “MVP SaaS” (3–7 dias)
Objetivo: suportar usuários reais com isolamento e cobrança.

Sugestão (safe minimum):
- [ ] “Org”/workspace + membership (owner/admin/member)
- [ ] Modelo de autorização mínimo:
  - toda entidade persistida deve carregar `org_id`
  - o backend resolve `org_id` a partir do `uid` autenticado e valida acesso em todas as queries
- [ ] Persistência (ex.: Firestore/AlloyDB) para:
  - users/orgs
  - runs (tasks), artifacts, billing state

Status em 2026-01-26:
- ✅ Modelo multi-tenant mínimo implementado no backend (Org + Membership + Run).
- ✅ Store com fallback (Memory local; Firestore em Cloud Run).
- ⚠️ Billing e artifacts persistentes ainda não implementados (somente runs + final_text).
- [ ] Billing (Stripe) com gating simples (limites de uso)
- [ ] Logs de auditoria (ações principais)

Aceite:
- [ ] Usuário A não acessa runs do usuário B.
- [ ] Plano free/pro limita acessos.
- [ ] Export mínimo de dados (para suporte).

---

### M4 — Hardening operacional (em paralelo, 1–3 dias)
Objetivo: reduzir risco (segurança, custo, confiabilidade) sem re-arquitetar tudo.

Itens (prioridade alta):
- [ ] Least privilege por Cloud Run service account (Recommender → ação manual com validação).
  - Mapear exatamente quais APIs cada serviço usa e reduzir papéis.
- [ ] Secret Manager para todos os segredos (não usar `.env` em produção).
  - Service account do serviço deve ter `roles/secretmanager.secretAccessor` para secrets necessários.
- [ ] Alertas:
  - Budget alert (billing)
  - Quota alerts (SSD_TOTAL_GB e CPU Alloc do Cloud Run em `us-central1`)
- [ ] Hardening web do frontend (Cloud Run/Next) — sem novas features:
  - headers de segurança via `next.config.js` (`headers()`).
  - CSRF mínimo em rotas cookie-auth: validar `Origin`/`Referer` e rejeitar cross-origin (ver Firebase Auth session
    cookies).

Itens (prioridade média):
- [ ] Rate limiting / proteção DDoS:
  - Cloud Armor via HTTPS Load Balancer (se necessário).
- [ ] Monitoramento externo (uptime):
  - criar uptime check para a URL pública do frontend (e/ou Cloud Run Revision) e alertas:
    (ver Cloud Monitoring uptime checks).
  - nota operacional: para o gateway, padronizar probes em `GET /healthz/` (com `/` final).
- [ ] Supply-chain hardening (Cloud Run):
  - avaliar/pilotar Binary Authorization para Cloud Run (política e atestado).
- [ ] “Enterprise hardening” opcional:
  - IAP + Identity Platform na frente do frontend/admin console (quando fizer sentido).

Aceite:
- [ ] Rotação de segredos possível sem redeploy (preferir mount por volume).
- [ ] Quotas monitoradas com ação clara (request increase vs reduzir consumo).

---

### M5 — Cutover controlado (produção) (0.5–1 dia)
Objetivo: migrar tráfego para o caminho canônico (Cloud Run) com rollback fácil.

Passos:
- [ ] Definir domínio(s) e origem (Cloud Run) de forma explícita.
- [ ] Validar CORS e cookies (se usados) com HTTPS.
- [ ] Medir: latência, taxas de erro, custo por request.

Aceite:
- [ ] Rollback definido (ex.: voltar DNS/origem) e testado.
- [ ] SLO mínimo atendido (ex.: <1% erro 5xx em 24h).

---

### M6 — Decommission de legado (somente após cutover + aprovação explícita) (1–2 dias)
Objetivo: simplificar e reduzir custo/risco removendo duplicidade.

**NÃO EXECUTAR sem aprovação explícita (lista de “aprováveis”).**

Candidatos (baseado no inventário 2026-01-26):
- Firebase Hosting: site `vertice-ai` (se não for mais usado em produção)
- Firebase App Hosting backends: `us-central1`, `vertice-us`
- Cloud Run: `ssrverticeai`
- Repo: `vertice-chat-webapp/` (após migração completa do que for necessário)
- `firebase.json` da raiz (se Firebase não for mais parte do pipeline)

Plano seguro de remoção:
1) Provar “zero tráfego” / não-uso (logs + DNS + owners).
2) Desabilitar deploy path (CI/CD) antes de deletar recurso.
3) Deletar um recurso por vez, com janela de mudança e rollback disponível.
4) Registrar no relatório “o que foi removido e por quê”.

---

### M7 — Monetization & Billing (Stripe Hybrid Model) (2–4 dias)
Objetivo: Implementar cobrança real (SaaS) com modelo híbrido (Assinatura Base + Usage-based para AI compute).

**Estratégia de Pricing (2026):**
- **Modelo:** Híbrido. "Start Cheap" para reduzir barreira de entrada.
- **Tiers:**
  - **Free/Hobby:** Acesso limitado (ex: 50 requests/dia, modelos Flash).
  - **Pro ($19/mês):** Acesso prioritário, modelos Pro/Ultra, armazenamento estendido + Usage Overage (se passar da cota inclusa).
- **Tech Stack:** Stripe Checkout (Hosted) para segurança + Webhooks para provisionamento.

**Backend (`apps/agent-gateway`):**
- [ ] Dependência: `stripe` (Python SDK).
- [ ] Config: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (Secret Manager).
- [ ] Endpoints:
  - `POST /v1/billing/checkout`: Cria sessão do Stripe Checkout (mode=subscription) e retorna URL.
  - `POST /v1/billing/portal`: Cria sessão do Customer Portal (para cancelar/upgradear).
  - `POST /v1/webhooks/stripe`: Recebe eventos (`checkout.session.completed`, `customer.subscription.updated`).
- [ ] Persistência: Tabela `subscriptions` no Firestore (org_id, stripe_sub_id, status, current_period_end).
- [ ] Gating: Middleware `SubscriptionGuard` que checa `subscriptions` antes de liberar acesso a modelos caros.

**Frontend (`apps/web-console`):**
- [ ] Página `/pricing` (Pública & Autenticada):
  - Design "Obsidian/Neon": Cards escuros (`surface-card`) com bordas sutis (`border-dim`).
  - Destaque no plano "Pro" com `box-shadow: glow-cyan`.
  - Toggle Mensal/Anual (desconto no anual).
- [ ] Integração:
  - Botão "Upgrade" chama `/v1/billing/checkout`.
  - Redirecionamento automático para Stripe.
- [ ] Settings > Billing:
  - Mostrar status da assinatura atual.
  - Botão "Manage Subscription" (abre Stripe Customer Portal).

**Critérios de Aceite:**
- [ ] Usuário consegue assinar plano Pro via cartão de crédito (Test Mode).
- [ ] Webhook atualiza Firestore em < 5s.
- [ ] Usuário Free é bloqueado ao tentar usar recurso Pro.
- [ ] Portal do Cliente funciona para cancelamento.

---

### M8 — Documentation Portal & DevEx (Docs-as-Code) (2–3 dias)
Objetivo: Criar uma área de documentação **integrada, interativa e bonita** (`/docs`) para educar usuários e desenvolvedores sobre como criar Agentes e usar o SDK.

**Conceito (Docs 2026):**
- **Nada de PDF ou Wiki separada:** A doc vive dentro do `apps/web-console` (Next.js).
- **Interactive:** Exemplos de código que podem ser copiados ou até executados (se possível).
- **Design:** Mesma identidade "Obsidian" do app (dark mode, code blocks com syntax highlighting neon).

**Frontend (`apps/web-console`):**
- [ ] Engine: Configurar `@next/mdx` ou `next-mdx-remote` para renderizar markdown.
- [ ] Styling: Usar `rehype-pretty-code` para blocos de código com tema "One Dark" ou similar ao Obsidian.
- [ ] Estrutura (`/docs` layout):
  - Sidebar de navegação (resiliência em mobile).
  - Table of Contents (ToC) flutuante na direita.
  - Breadcrumbs.
- [ ] Conteúdo Inicial (Migrar de `docs/Agents-sdk`):
  - **Getting Started:** Instalação do SDK (`pip install vertice-mcp`), Autenticação.
  - **Core Concepts:** O que é um Agente, Tool, MCP.
  - **Tutorials:** "Building your first Analyst Agent".
  - **API Reference:** Detalhes dos endpoints (gerado ou manual).
- [ ] Integração:
  - Adicionar link "Docs" no Header principal (`DashboardClient` / Layout).

**Critérios de Aceite:**
- [ ] Rota `/docs` acessível publicamente (SEO-friendly).
- [ ] Code blocks têm syntax highlighting e botão de cópia.
- [ ] Link "Docs" visível no Header da aplicação.
- [ ] Mobile view da documentação é navegável.

---

### M9 — Data Protection & Privacy (GDPR/LGPD) (1–2 dias)
Objetivo: Implementar criptografia de dados sensíveis e controles de privacidade (Direito ao Esquecimento / Exportação), reaproveitando a lógica robusta de criptografia validada na fase de transição.

**Backend (`apps/agent-gateway` + `packages/vertice-core`):**
- [ ] **Crypto Engine:** Portar/Ativar `gdpr_crypto` (AES-GCM + Key Rotation) para o novo gateway.
  - Campos a encriptar no Firestore: `prompt`, `final_text`, `artifacts` (se sensível).
  - Integração com Google Cloud KMS (opcional para M9, mas recomendado).
- [ ] **Data Erasure (Right to be Forgotten):**
  - Endpoint `POST /v1/me/erasure`: Soft-delete imediato, hard-delete agendado (30 dias).
  - Limpar logs associados ao `uid` (onde possível).
- [ ] **Data Export (Portability):**
  - Endpoint `GET /v1/me/export`: Gera JSON com todos os dados do usuário (Runs, Orgs, Artifacts).

**Frontend (`apps/web-console`):**
- [ ] **Privacy Dashboard (`/settings/privacy`):**
  - Botão "Download My Data" (chama `/export`).
  - Botão "Delete Account" (zona de perigo, confirmação dupla).
  - Toggles para "Allow AI Training" (se aplicável).

**Critérios de Aceite:**
- [ ] Dados sensíveis aparecem encriptados no console do Firestore (mas legíveis via API).
- [ ] Export gera um JSON válido e completo.
- [ ] Delete remove acesso imediatamente.

---

### M10 — Agentic Observability & Feedback Loop (2–3 dias)
Objetivo: Abrir a "caixa preta" dos Agentes. Implementar rastreamento detalhado de chamadas de LLM, custos em tempo real e permitir que usuários avaliem as respostas para melhoria contínua (RLHF).

**Backend (`apps/agent-gateway` + `vertice-core`):**
- [ ] **Tracing:** Integrar OpenTelemetry / Cloud Trace para cada "Run".
  - Logar latência de cada etapa (Thinking, Tool Call, Rendering).
  - Rastrear tokens usados e custo estimado em USD por request.
- [ ] **Feedback API:** Endpoint `POST /v1/runs/{run_id}/feedback`.
  - Armazenar `score` (1/-1), `comment` e `metadata` (qual modelo/prompt foi usado).

**Frontend (`apps/web-console`):**
- [ ] **Telemetry View:** No Dashboard, mostrar um pequeno indicador de "Tokens/sec" e "Cost" da run atual.
- [ ] **Feedback UI:** Adicionar botões de 👍/👎 no final de cada resposta do agente.
- [ ] **Stats Page (`/dashboard/stats`):** Gráficos simples de uso (requests por dia, custo acumulado no mês).

**Critérios de Aceite:**
- [ ] Logs no Cloud Logging mostram o "Trace ID" correlacionando Frontend e Backend.
- [ ] Usuário consegue avaliar uma resposta e o dado é salvo no Firestore.
- [ ] Dashboard mostra o custo da última operação.

---

### M11 — Autonomous Maintenance with Google Jules (2–4 dias)
Objetivo: Transformar a manutenção do Vértice em um processo autônomo. Integrar o **Google Jules** (Agente de Coding Autônomo de 2026) para atuar como o "SRE de Código", realizando varreduras proativas, correções automáticas e gestão de débitos técnicos via GitHub.

**Configuração e Integração:**
- [ ] **GitHub App Connectivity:** Instalar e configurar o Google Jules GitHub App no repositório `vertice-code`.
  - Configurar permissões de leitura/escrita em Code, Pull Requests e Issues.
  - Ativar o label `jules` para acionamento sob demanda via Issues.
- [ ] **Scheduled Self-Healing (Scanning):**
  - Configurar varredura diária (Daily Scan) para identificar:
    - Vulnerabilidades de segurança (via integração Jules + OSV).
    - Débitos técnicos e `#TODO` esquecidos.
    - Depreciações de APIs do Google Cloud/Firebase (2026 updates).
- [ ] **Automated PR Pipeline:**
  - Jules deve clonar o repo em Cloud VMs seguras, testar a correção e abrir o PR.
  - Configurar regras de auto-merge para correções de dependências menores (opcional).

**Operação (Jules as a Team Member):**
- [ ] **Agent Persona:** No ecossistema Vértice, Jules será o encarregado da "Saúde Sistêmica".
- [ ] **Feedback Loop:** Integrar logs de build do Cloud Build com o Jules. Se um deploy falhar, o Jules deve analisar os logs e propor o fix imediatamente no mesmo PR.

**Critérios de Aceite:**
- [ ] Jules abre pelo menos 1 PR de manutenção (ex: bump de dependência ou fix de lint) com sucesso.
- [ ] O label `jules` em uma Issue dispara a execução do agente.
- [ ] Relatório semanal de "Código Curado" gerado pelo Jules no `/docs`.

---

### M12 — Nexus Meta-Agent Integration (The Apex of Evolution) (3–5 dias)
Objetivo: Integrar o **Nexus Meta-Agent** (desenvolvido como a Inteligência de Próxima Geração) para atuar como o "Cérebro Evolutivo" do ecossistema Vértice. O Nexus foca na auto-melhoria intrínseca e na otimização sistêmica de todos os outros agentes.

**Capacidades Integradas (Baseado na arquitetura Nexus):**
- [ ] **Intrinsic Metacognition:** Ativar a camada metacognitiva para monitorar e regular a performance de todos os agentes da agência.
- [ ] **Self-Healing Infrastructure:** Implementar o ciclo de cura em 3 fases (Detection, Diagnosis, Remediation) para infraestrutura Cloud Run/GKE.
- [ ] **Evolutionary Optimization:** Configurar o framework evolutivo (Island-Based) para otimizar o código dos agentes e os prompts do sistema baseados em performance real.
- [ ] **Hierarchical Memory (1M Tokens):** Conectar o sistema de memória de longo prazo (L1-L4) nativo do Gemini 3 para persistência de contexto entre gerações.

**Backend (`apps/agent-gateway` + `Nexus Implementation`):**
- [ ] Portar o código do Nexus (`docs/Agents-sdk/Nexus-agent`) para o ambiente de produção.
- [ ] Configurar permissões de "Super-Agent" para o Nexus (capacidade de modificar outros serviços).
- [ ] Integrar com Firestore para armazenamento de `metacognitive_insights` e `evolutionary_candidates`.

**Frontend (`apps/web-console`):**
- [ ] **Nexus Insights View (`/dashboard/nexus`):** Dashboard exclusivo para visualizar o progresso evolutivo, as "curas" realizadas e os insights metacognitivos.

**Critérios de Aceite:**
- [ ] Nexus realiza sua primeira "Auto-Reflexão" e gera um insight de melhoria válido.
- [ ] Pelo menos uma otimização de código é proposta e testada via framework evolutivo.
- [ ] O sistema de memória L1-L4 persiste dados corretamente no Firestore.

---

## 3) Runbook rápido (validação contínua, barato)

Checklist diário (read-only):
```bash
gcloud run services list --platform managed --region us-central1
gcloud beta container backup-restore backups list --location us-central1 --backup-plan vertice-backup-plan
gcloud compute regions describe us-central1 --format=json | jq '.quotas[] | select(.metric=="SSD_TOTAL_GB")'
```

Checklist por deploy (smoke mínimo):
- [ ] **(se serviço for público)** `/healthz/` retorna 200
- [ ] **(se serviço for privado)** chamada anônima retorna 401/403 e chamada via runtime autorizado retorna 200
- [ ] endpoint protegido retorna 401/403 sem token (quando aplicável)
- [ ] stream inicia e envia eventos em < 10s (via frontend/runtime autorizado)
- [ ] logs sem erros de permissão (Secret Manager/IAM)

Comandos de smoke (quando o serviço estiver privado via IAM):
```bash
AG_URL="$(gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.url)')"

# Anônimo (deve falhar com 401/403 quando privado)
curl -sS -o /dev/null -w 'anon /healthz/ -> %{http_code}\n' "$AG_URL/healthz/"

# Autenticado (requer que o operador tenha roles/run.invoker OU seja dono/admin do projeto)
TOKEN="$(gcloud auth print-identity-token --audiences="$AG_URL")"
curl -sS -o /dev/null -w 'auth /healthz/ -> %{http_code}\n' -H "Authorization: Bearer $TOKEN" "$AG_URL/healthz/"
```

---

## 4) O que eu preciso de você (decisões de 5 minutos)

Para eu transformar este roadmap em execuções/PRs pequenas e contínuas, confirme:
1) “Produção canônica” é Cloud Run? ✅ (confirmado)
2) Provedores de login para o MVP: Google-only ✅ (confirmado)
3) Multi-tenant no MVP: sim ✅ (confirmado)

---

## 5) “PRs executáveis” (para GPT‑5.1 aplicar sem atrito)

Esta seção é deliberadamente objetiva: cada item vira uma PR pequena e tem comandos claros.

### PR-L0 — Corrigir drift do gateway no Cloud Run (P0)
- Escopo: apenas `docs/google/*` (plano) + scripts (se necessário).
- Execução (produção): seguir `M0.1`.
- Aceite: `/healthz/` = 200 e `/openapi.json` = 200 no `vertice-agent-gateway`.

### PR-L1 — Hardening IAM: gateway privado (P0)
- Execução (produção): seguir `M1.1`.
- Aceite: `/dashboard` e `/artifacts` funcionam via `vertice-frontend` mesmo com gateway privado.

### PR-L2 — Pipeline de build do frontend canônico (`apps/web-console`) (P0/P1)
- Criar `apps/web-console/Dockerfile` (Next.js production) e um `cloudbuild.web-console.yaml`.
- Atualizar deploy do Cloud Run `vertice-frontend` para usar a imagem do `apps/web-console`.
- Aceite: `vertice-frontend` servindo as rotas do web-console e mantendo login + settings + dashboard.

### PR-L3 — Artifacts persistentes + RBAC mínimo (P1)
- Backend: persistir artifacts por `run_id` e `org_id` (Firestore/AlloyDB conforme decisão).
- Frontend: `/artifacts` renderiza artifacts e aplica sanitização.
- Aceite: artifacts aparecem após reload e usuário não acessa dados de outra org.

### PR-L4 — Web hardening (headers + CSRF mínimo) (P0)
- Escopo: `apps/web-console` (sem alterar features).
- Implementação:
  - headers de segurança via `apps/web-console/next.config.js` (`headers()`).
  - bloquear POST cross-origin em rotas cookie-auth (Origin/Referer).
- Aceite:
  - `X-Powered-By` ausente.
  - response inclui headers de segurança nas rotas principais.
  - POST cross-origin retorna 403.

### PR-L5 — UX Drafts Audit → backlog executável (P0/P1)
- Escopo: apenas docs (centralização).
- Ação: incorporar o resultado de `docs/google/FRONTEND_UX_DRAFTS_IMPLEMENTATION_AUDIT_2026-01-26.md` como checklist
  de PRs (front-only) nesta roadmap, para evitar “UI mock” em produção.
- Aceite: roadmap contém uma seção “UX Drafts → Wiring” com tarefas PR-sized para `/dashboard`, `/cot`, `/command-center`.

### PR-L6 — Backend Billing Foundation (Stripe) (P1)
- Escopo: `apps/agent-gateway`.
- Implementação:
  - Adicionar `stripe` ao `requirements.txt`.
  - Criar `app/core/billing.py` (serviço Stripe wrapper).
  - Implementar endpoints `/v1/billing/*` e webhook handler.
  - Testes de integração com `stripe-mock` ou fixtures.
- Aceite: Webhook processa `checkout.session.completed` e grava no Firestore (emulador).

### PR-L7 — Frontend Pricing & Plan Cards (P1)
- Escopo: `apps/web-console`.
- Implementação:
  - Página `/pricing` com design system Obsidian (Cards, Toggles, Checkmarks).
  - Integração com endpoint de checkout (`/v1/billing/checkout`).
  - Tratamento de estados de retorno (`/dashboard?success=true`).
- Aceite: UI renderiza planos corretamente e botão inicia fluxo de redirect.

### PR-L8 — Subscription Gating & Usage Limits (P1)
- Escopo: `apps/agent-gateway` (middleware) e `apps/web-console` (UI feedback).
- Implementação:
  - Middleware que verifica role/subscription antes de processar requests caros.
  - UI indicators para usuários Free (ex: "Upgrade to use GPT-5").
- Aceite: Usuário sem flag `is_pro` recebe erro/aviso ao tentar features Pro.

### PR-D1 — Docs Engine (MDX + Syntax Highlighting) (P1)
- Escopo: `apps/web-console`.
- Implementação:
  - Configurar MDX no Next.js 16.
  - Criar layout dedicado `/app/docs/layout.tsx` (Sidebar + Content).
  - Implementar componentes MDX (CodeBlock, Callout, Cards).
- Aceite: Renderização de `.mdx` funciona com estilo "Obsidian".

### PR-D2 — Docs Content & Navigation (P1)
- Escopo: `apps/web-console`.
- Implementação:
  - Escrever guias iniciais (baseado no SDK Python).
  - Adicionar link "Docs" no Navbar principal.
- Aceite: Navegação fluida entre páginas da doc e volta ao Dashboard.

### PR-S1 — Privacy Foundation (Crypto & Erasure) (P0)
- Escopo: `apps/agent-gateway`, `packages/vertice-core`.
- Implementação:
  - Migrar `gdpr_crypto.py` para `vertice-core/src/vertice_core/core/security.py` (se ainda não estiver).
  - Aplicar criptografia automática no `Store` (Firestore) para campos de texto.
  - Implementar endpoint `/v1/me/erasure`.
- Aceite: Firestore mostra dados encriptados; API retorna dados decriptados.

### PR-S2 — User Data Controls (Export & UI) (P1)
- Escopo: `apps/web-console`, `apps/agent-gateway`.
- Implementação:
  - Backend: Endpoint `/v1/me/export` (stream de JSONl).
  - Frontend: Página `/settings/privacy` com botões de ação.
- Aceite: Download de dados funciona e exclusão de conta redireciona para login.

### PR-O1 — Agentic Telemetry (Traces & Costs) (P1)
- Escopo: `apps/agent-gateway`, `packages/vertice-core`.
- Implementação:
  - Middlewares de telemetria e tracking de tokens (Vertex AI).
  - Exportar para Cloud Trace.
- Aceite: Cada run gera um Trace completo no Google Cloud Console.

### PR-O2 — Feedback Loop (👍/👎 & RLHF Storage) (P2)
- Escopo: `apps/web-console`, `apps/agent-gateway`.
- Implementação:
  - UI de feedback no final da mensagem.
  - Endpoint de storage de feedback no backend.
- Aceite: Botões de feedback funcionais e dados visíveis no banco.

### PR-J1 — Google Jules GitHub Integration (P1)
- Escopo: GitHub Repo + Configuração Cloud.
- Ação: Configurar GitHub App, Webhooks e Permissions para o Jules atuar no repo `vertice-code`.
- Aceite: Jules responde a um trigger de label `jules` em uma Issue.

### PR-J2 — Scheduled Maintenance & Self-Healing (P2)
- Escopo: GitHub Actions + Jules Scheduling.
- Ação: Criar workflow de "Daily Health Scan" onde o Jules identifica e corrige débitos técnicos automaticamente.
- Aceite: Jules gera o primeiro PR autônomo de manutenção.

### PR-N1 — Nexus Foundation & Metacognition (P1)
- Escopo: `apps/agent-gateway` + Nexus Integration.
- Ação: Integrar o motor metacognitivo e o sistema de memória hierárquica (Gemini 3).
- Aceite: Nexus gera insights baseados em logs de execução de outros agentes.

### PR-N2 — System-Wide Evolution & Healing (P2)
- Escopo: Agent Swarm + Infrastructure.
- Ação: Ativar os loops de otimização evolutiva e cura automática de infraestrutura.
- Aceite: Nexus propõe e valida uma melhoria de código autônoma.

### PR-INDEX — Fonte única dos PRs (docs/google) (P0)
Objetivo: centralizar “o que precisa ser PR” e evitar drift entre documentos.

Regra: a lista de PRs abaixo é a **fonte única**. Outros arquivos em `docs/google/` são referência (detalhes, relatórios,
contexto), mas não substituem este backlog.

**PRs de produto/arquitetura (jules)**
- PR-0/PR-1/PR-2/PR-3/PR-4/PR-5/PR-6 (fonte: `docs/google/jules_integration/JULES_BACKLOG_PRs.md`)

Resumo (status + validação rápida, para não depender de outro doc):
| PR | Tema | Status | Como validar (exemplos) |
|---|---|---|---|
| PR-0 | Bloquear RCE no sandbox | ✅ DONE (2026-01-25) | `pytest vertice-chat-webapp/backend/tests/unit/test_no_local_rce.py -v -x` |
| PR-1 | KMS/GDPR crypto fail-fast | ✅ DONE (2026-01-25) | `pytest vertice-chat-webapp/backend/tests/unit/test_gdpr_crypto.py -v -x` |
| PR-2 | `packages/vertice-core` + imports estáveis | ✅ DONE (2026-01-25) | `python -c "import vertice_core; print('OK')"` |
| PR-3 | `apps/agent-gateway` + AG-UI stream | ✅ DONE (2026-01-25) | `pytest tests/integration/test_agent_gateway_agui_stream.py -v -x` |
| PR-4 | AlloyDB memory foundation | ✅ DONE (2026-01-25) | `pytest tests/unit/test_alloydb_migration.py -v -x` |
| PR-5 | Google-managed Vertex (execução remota) | ✅ DONE (2026-01-25) | `pytest tests/unit/test_coder_reasoning_engine_app.py -v -x` |
| PR-6 | Vertex AI integration cutover | ✅ DONE (2026-01-25) | ver `docs/google/PR_6_VERTEX_AI_INTEGRATION_CUTOVER_2026.md` |

**PRs detalhados já existentes**
- `docs/google/PR_4_ALLOYDB_MEMORY_FOUNDATION_2026.md`
- `docs/google/PR_5_GOOGLE_MANAGED_VERTEX_2026.md`
- `docs/google/PR_6_VERTEX_AI_INTEGRATION_CUTOVER_2026.md`

**PRs de manutenção/ops (Google Cloud)**
- PR-M1..PR-M6 (fonte: `docs/google/jules_integration/JULES_BACKLOG_PRs.md`)
- Recommender (backup/maintenance/IAM/quota): `docs/google/GOOGLE_CLOUD_RECOMMENDER_ACTION_PLAN_2026-01-26.md`
- Runbook manutenção: `docs/google/GOOGLE_CLOUD_MAINTENANCE_BEST_PRACTICES_2026.md`
- Checklist contínuo (rotina): `docs/google/GOOGLE_CLOUD_CONTINUOUS_VALIDATION_CHECKLIST_2026.md`

Status (manutenção) — 2026-01-26:
- ✅ Inventário read-only (scripts): `tools/gcloud/inventory_cloud_run.sh`, `tools/gcloud/inventory_gke.sh`,
  `tools/gcloud/inventory_iam.sh`, `tools/gcloud/inventory_cloud_functions_v2.sh`
- ✅ Runbook e checklist: `docs/google/GOOGLE_CLOUD_MAINTENANCE_BEST_PRACTICES_2026.md`,
  `docs/google/GOOGLE_CLOUD_CONTINUOUS_VALIDATION_CHECKLIST_2026.md`

**Fases (quando precisar do contexto)**
- `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`
- `docs/google/PHASE_3_2_WIRING_NARCISSUS.md`
- `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`
- `docs/google/PHASE_6_NARCISSUS_UX_UI_2026.md`

---

## 6) Sessão — Ações Necessárias no Frontend (SaaS profissional, Google-only)

Objetivo: transformar `apps/web-console` em um web-app “launch-ready” (UX, auth, multi-tenant, resiliency e deploy),
mantendo stack Google e reduzindo retrabalho pós-lançamento.

Premissas (estado atual):
- Cloud Run canônico: `vertice-frontend` (público) → invoca `vertice-agent-gateway` (privado).
- Auth: Firebase Auth/Identity Platform (Google-only) já existe no app.
- Multi-tenant: org/workspace existe no gateway; o frontend usa cookie `vertice_org`.

### PR-F1 — Contrato de endpoints + status page
- Padronizar probes/monitoramento para `GET /healthz/` e `GET /readyz/` (nota: se gateway privado, probes devem ser
  feitos por principal autorizado, não por tráfego anônimo).
- Criar `/status` (somente autenticado) com: uid, org ativo, última run, latência (ping no gateway).
- Garantir que qualquer URL externa do gateway seja consumida apenas server-side (nunca expor em `NEXT_PUBLIC_*`).

### PR-F2 — Auth UX + estados de sessão
- Estados de loading e erro (login, refresh, logout).
- Re-login suave quando token expirar.
- Guard de rotas consistente (middleware já existe; alinhar comportamento em client/server).

### PR-F3 — Onboarding + Multi-tenant completo
- Onboarding pós-login (1–2 telas): escolher/criar org, selecionar org default.
- Settings: listar/criar/selecionar org + exibir role.
- Header: org switcher global (com fallback seguro e indicação clara de ambiente/org).

### PR-F4 — Streaming resiliente (Claude/Manus-like)
- SSE: reconexão com backoff, cancelamento e retry.
- UI: estados “connecting/streaming/error/completed”, retries e “copy transcript”.
- Persistência local do prompt draft e histórico por sessão.

### PR-F4.1 — UX Drafts → “Agentic Stream” real (P0)
Baseado em `docs/google/FRONTEND_UX_DRAFTS_IMPLEMENTATION_AUDIT_2026-01-26.md`.

Estado atual (2026-01-26):
- `/dashboard` tem **SSE real**, mas renderiza **um único blob** (`<pre>`).
- `/cot` e `/command-center` são **design-only** (sem wiring).

Objetivo: transformar a UI “parecida” em base real (sem expandir features), garantindo que a experiência “claude-code-web”
tenha o mínimo de estrutura: eventos tipados, cards, reconexão e seleção de artifacts.

Snapshot (drafts → implementação atual):
| Draft | Route | UI parity | Logic parity |
|---|---:|---:|---:|
| Agentic Stream Dashboard (v2) | `/dashboard` | High | Partial |
| Advanced Command Center | `/command-center` | High | Mock |
| Refined CoT Logic Stream | `/cot` | High | Mock |

Escopo sugerido (PR-sized):
1) Hook compartilhado de stream (AGUI)
   - parse SSE robusto e normalização em union tipado (delta/final/error/intent/tool/context/code/metrics).
2) Render estruturado no `/dashboard`
   - substituir `<pre>` por lista de cards (agent + intent + tool + code + context).
3) “Code Preview” conectado
   - remover snippet hard-coded e plugar “artifact selecionado” (in-memory primeiro).

Aceite:
- `/dashboard` mostra cards por evento (não só texto).
- eventos `intent`/`tool` aparecem como blocos dedicados.
- “Code Preview” muda com base em eventos (sem hardcode).

### PR-F4.2 — Contrato mínimo para `/cot` e `/command-center` (P1)
Objetivo: definir a forma dos dados (API) antes de “ligar” as telas.

Escopo:
- Definir (docs + types) payloads para:
  - CoT timeline (passos, confidences, context refs).
  - Command center telemetry (agents, status, tokens/sec, health).
- Criar endpoints/proxies equivalentes aos existentes (`/api/gateway/*`) se necessário.

Aceite:
- existe um contrato único (types + doc) e ambas telas param de ser mock assim que o backend entregar dados.

### PR-F5 — Artifacts + histórico (UX)
- `/artifacts`: filtros (org, data), paginação, detalhes do run.
- Render seguro (sanitização) para conteúdo gerado (markdown/código).

### PR-F6 — Observabilidade no frontend
- Error boundary global + logging estruturado (sem PII).
- Instrumentação para correlacionar requests (ex.: `X-Request-Id` quando disponível).
- Web vitals (mínimo) e alertas (via Cloud Monitoring/SLOs, se aplicável).

### PR-F7 — Segurança/compliance mínima
- CSP headers + cookies `Secure`/`SameSite` adequados.
- Páginas: Termos, Privacidade, Contato/Support.
- UI anti-abuso: rate limit básico no client e mensagens claras de bloqueio.

### PR-F8 — Redeploy do frontend (Cloud Run) + validação pós-hardening
- Redeploy `vertice-frontend` com o build novo.
- Validar rotas: `/`, `/dashboard`, `/cot`, `/artifacts`, `/command-center`, `/settings`.
- Validar chamadas `/api/gateway/*` “de dentro do runtime” (confirma ID token + IAM).

Critérios de aceite do frontend (para launch)
- Login funciona e mantém sessão.
- Stream SSE é resiliente em rede instável (reconnect) e não vaza tokens em logs.
- Multi-tenant visível e consistente; runs/artifacts carregam por org.
- Erros são observáveis (UI + logs) e existe `/status` para diagnóstico rápido.

---

## Anexo A — Contrato de env vars / secrets (fonte única)

### Frontend canônico: `apps/web-console` (Cloud Run: `vertice-frontend`)

Env vars (runtime):
- `VERTICE_AGENT_GATEWAY_URL`: URL do Cloud Run `vertice-agent-gateway` (sem `/` no final).

Env vars públicas (podem ser build-time ou runtime; não são segredos):
- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`

Requisitos de identidade (service-to-service):
- Service account do `vertice-frontend` deve ter `roles/run.invoker` no `vertice-agent-gateway` (quando privado).

### Backend: `apps/agent-gateway` (Cloud Run: `vertice-agent-gateway`)

Env vars (runtime):
- `VERTICE_AUTH_REQUIRED`: `1` em produção (rejeita requests sem auth); `0` apenas em dev/test.

Dependências (prod):
- Firestore (default store em Cloud Run):
  - papel mínimo recomendado para a SA do gateway: `roles/datastore.user` (ler/escrever documentos).
- Secret Manager (secrets por env var/volume conforme necessário):
  - exemplo já existente no projeto: `VERTICE_ALLOYDB_DSN` via Secret Manager.
- Vertex AI (quando usado):
  - papel já observado em algumas SAs: `roles/aiplatform.user`.

### Onde NÃO colocar segredos
- Nunca commitar `.env` com chaves/tokens.
- Para Cloud Run: preferir Secret Manager e IAM/ADC (WIF no CI/CD).

---

## Anexo Z — Referências oficiais (Google) (2026)

Observação: este roadmap é **Google-only**; links abaixo são apenas documentação oficial Google Cloud/Firebase.

- Cloud Run — end-users (Identity Platform/Firebase Auth)
  - https://cloud.google.com/run/docs/authenticating/end-users
- Cloud Run — public access (Invoker IAM / allUsers)
  - https://docs.cloud.google.com/run/docs/authenticating/public
- Cloud Run — service-to-service (ID tokens + IAM)
  - https://cloud.google.com/run/docs/authenticating/service-to-service
- Secret Manager com Cloud Run (secrets)
  - https://cloud.google.com/run/docs/configuring/jobs/secrets
- Firebase Auth — verify ID tokens (Admin)
  - https://firebase.google.com/docs/auth/admin/verify-id-tokens
- Firebase Auth — session cookies (Admin)
  - https://firebase.google.com/docs/auth/admin/manage-cookies
- Cloud Monitoring — uptime checks
  - https://docs.cloud.google.com/monitoring/uptime-checks
- Cloud Armor — rate limiting overview (opcional)
  - https://cloud.google.com/armor/docs/rate-limiting-overview
- Binary Authorization for Cloud Run (opcional)
  - https://cloud.google.com/binary-authorization/docs/run
- ADC (Application Default Credentials)
  - https://cloud.google.com/docs/authentication/provide-credentials-adc
- Workload Identity Federation (recomendado no CI/CD)
  - https://cloud.google.com/iam/docs/workload-identity-federation

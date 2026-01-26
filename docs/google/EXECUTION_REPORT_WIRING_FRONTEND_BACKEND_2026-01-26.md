# Execution Report — Wiring Frontend ↔ Backend (Google Stack) — 2026-01-26

Escopo: tornar o SaaS **production-ready** na stack Google (Cloud Run + Identity Platform/Firebase Auth), com wiring
end-to-end e multi-tenant mínimo (org/workspace + membership), sem introduzir segredos no repo.

## 1) Resultado (o que está funcionando)

- Frontend `apps/web-console` possui login Google (Firebase Auth), cria session cookie `__session` e protege rotas via
  middleware.
- Backend `apps/agent-gateway` exige identidade do usuário:
  - via `X-Vertice-User` (trusted proxy) **ou**
  - via `Authorization: Bearer <Firebase ID token>` (fallback) **ou**
  - bypass local quando `VERTICE_AUTH_REQUIRED=0`.
- Multi-tenant: backend cria/resolve org default por usuário e persiste “runs” por `org_id`.
- Wiring real:
  - `/dashboard` chama `/api/gateway/stream` (SSE) e renderiza o stream.
  - `/artifacts` exibe “Recent Runs” via `/api/gateway/runs`.
  - `/settings` lista orgs, cria org e seleciona org ativo (cookie `vertice_org`).

## 2) Evidência de validação (comandos executados + status)

### Frontend (TypeScript)
```bash
cd apps/web-console
npx tsc -p tsconfig.json --noEmit
npm run lint
```
Resultado: ✅ sem erros de tipos e ✅ sem erros de lint.

### Backend (Python)
```bash
ruff check apps/agent-gateway/app/auth.py apps/agent-gateway/app/store.py apps/agent-gateway/app/tenancy.py apps/agent-gateway/app/main.py
ruff format --check apps/agent-gateway/app/auth.py apps/agent-gateway/app/store.py apps/agent-gateway/app/tenancy.py apps/agent-gateway/app/main.py
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
```
Resultado: ✅ `pytest` 8 passed (`tests/integration/test_agent_gateway_agui_stream.py`).

## 3) Auditoria “estado real” no GCP (read-only)

Projeto ativo (gcloud): `vertice-ai` (2026-01-26)

### Cloud Run (serviços)
```bash
gcloud run services list --platform=managed --format='table(name,status.url)'
```
Observado:
- `vertice-frontend`
- `vertice-agent-gateway`
- `vertice-backend`
- `vertice-mcp`
- `ssrverticeai` (candidato a legado)

### Cloud Run IAM (risco antes do hardening)
```bash
gcloud run services get-iam-policy vertice-agent-gateway --region us-central1
```
Observado (antes): todos os serviços acima estavam com `roles/run.invoker` para `allUsers` (públicos).

Estado atual (após hardening, 2026-01-26): `allUsers` foi removido de `vertice-agent-gateway`, `vertice-backend` e
`vertice-mcp` (mantendo `vertice-frontend` público). Inventário antes/depois em `docs/google/_inventory/`.

### Cloud Run “drift” (importante)
No início do dia (antes da correção), o serviço `vertice-agent-gateway` estava rodando a imagem do repositório
`vertice-cloud/backend` (mesma família do `vertice-backend`). Evidência:
```bash
gcloud run services describe vertice-agent-gateway --region us-central1 --format='value(status.latestReadyRevisionName)'
gcloud run revisions describe <REV> --region us-central1 --format='value(spec.containers[0].image)'
```
Impacto observado: `GET /openapi.json` retorna **200**, mas `GET /healthz` retorna **404** no endpoint público do Cloud
Run.

Nota importante (observação empírica no domínio `*.run.app`): `GET /healthz` retorna **404 HTML** no edge mesmo quando o
serviço implementa a rota. Use sempre `GET /healthz/` (com `/` final) para probes e smoke tests.

Smoke test (read-only):
```bash
python - <<'PY'
import subprocess, urllib.request, urllib.error
ag = subprocess.check_output(
    ["gcloud","run","services","describe","vertice-agent-gateway","--region","us-central1","--format","value(status.url)"]
).decode().strip()
for path in ["/openapi.json","/healthz/"]:
    try:
        with urllib.request.urlopen(ag + path, timeout=20) as resp:
            print(path, resp.status)
    except urllib.error.HTTPError as e:
        print(path, e.code)
PY
```

## 4) Execução em produção (aprovado) — correções + hardening

### 4.1) Redeploy correto do `vertice-agent-gateway`
- Cloud Build (us-central1):
  - `741e1269-237b-4fe2-94f5-6c1e4995e90b` (primeiro build)
  - `d81276ba-492d-4d3b-9488-ba9ab9620176` (iter.)
  - `99ad288a-ad54-4f40-9ae7-b932a0ce89a1` (final)
- Imagem final (pinada por digest):
  - `us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/agent-gateway@sha256:babb430ea06f55fd71d6f7d9bfa2b8ab0ea472a89915f7e66060ee45c34c0c1e`
- Revision Cloud Run final:
  - `vertice-agent-gateway-00007-kmb`
- Smoke test (antes do hardening IAM): `GET /healthz/` e `GET /readyz/` retornaram **200**.

### 4.2) Hardening IAM (Cloud Run)
Aplicado:
- `vertice-agent-gateway`: removido `allUsers`; invokers:
  - `serviceAccount:cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com`
- `vertice-backend`: removido `allUsers`; invokers:
  - `serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-vertice-frontend@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-ssrverticeai@vertice-ai.iam.gserviceaccount.com`
- `vertice-mcp`: removido `allUsers`; invokers:
  - `serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
  - `serviceAccount:cr-vertice-backend@vertice-ai.iam.gserviceaccount.com`
- `vertice-frontend`: mantido público.

Inventário (antes/depois):
- `docs/google/_inventory/iam-vertice-agent-gateway-before-2026-01-26.json`
- `docs/google/_inventory/iam-vertice-agent-gateway-after-2026-01-26.json`
- `docs/google/_inventory/iam-vertice-backend-before-2026-01-26.json`
- `docs/google/_inventory/iam-vertice-backend-after-2026-01-26.json`
- `docs/google/_inventory/iam-vertice-mcp-before-2026-01-26.json`
- `docs/google/_inventory/iam-vertice-mcp-after-2026-01-26.json`

Smoke test (após hardening): chamadas anônimas para `vertice-agent-gateway`/`vertice-backend` retornam **403**.

## 5) Pendências remanescentes (próximos PRs)

1) Garantir permissões mínimas (IAM) por service account:
   - `cr-vertice-agent-gateway@...` com acesso mínimo a Firestore (se Firestore for o store padrão em produção).
2) Observabilidade e segurança:
   - request IDs / structured logs no gateway
   - budgets/alerts de billing e alertas de quota (especialmente `run.googleapis.com` e SSD em `us-central1`)
3) Cutover do legado:
   - decidir se `ssrverticeai` continua (ou é removido) após o redeploy final do frontend.

## 6) Arquivos alterados (referência rápida)

- Frontend auth/proxy/org:
  - `apps/web-console/app/login/page.tsx`
  - `apps/web-console/app/api/auth/session/route.ts`
  - `apps/web-console/app/api/gateway/stream/route.ts`
  - `apps/web-console/app/api/gateway/me/route.ts`
  - `apps/web-console/app/api/gateway/runs/route.ts`
  - `apps/web-console/app/api/gateway/orgs/route.ts`
  - `apps/web-console/app/api/org/select/route.ts`
  - `apps/web-console/app/api/org/active/route.ts`
  - `apps/web-console/app/settings/page.tsx`
  - `apps/web-console/lib/gateway.ts`
  - `apps/web-console/lib/session.ts`
  - `apps/web-console/middleware.ts`
- Backend auth/tenancy/store:
  - `apps/agent-gateway/app/auth.py`
  - `apps/agent-gateway/app/tenancy.py`
  - `apps/agent-gateway/app/store.py`
  - `apps/agent-gateway/app/main.py`

## 7) Segurança (nota)

Não foi adicionada nenhuma API key/secret no repo. A recomendação é manter:
- local: ADC (gcloud) e `.env` apenas na máquina (não versionado)
- CI/CD: Workload Identity Federation (sem chaves long-lived)

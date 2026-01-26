# Frontend Validation Report — apps/web-console (2026-01-26)

## Escopo
Validar a implementação atual do frontend `apps/web-console` nos níveis:
- Typecheck (TypeScript)
- Lint (ESLint/Next)
- Build (Next.js)

> Nota de segurança: nenhum segredo/token foi usado/gravado. Não vou inserir API keys no repo.

---

## Ambiente / Versões (observado no repo)
- App: `apps/web-console`
- Next.js: `15.5.9`
- React: `19.0.0`
- TypeScript: `^5`
- Tailwind: `3.4.1`

O roadmap em `docs/google/PHASE_3_2_WIRING_NARCISSUS.md` e
`docs/google/vertice-code-webapp-ui-ux/NARCISSUS_FRONTEND_ROADMAP_2026.md` cita “Next.js 16” e “Tailwind v4”, mas
o projeto atual está em Next 15 + Tailwind 3. Isso não é “erro”, só indica drift do plano vs implementação.

---

## Validações Executadas (resultado)

Executado em `apps/web-console`:
- `npx tsc -p tsconfig.json` → ✅ **OK** (exit 0)
- `npm run lint` → ✅ **OK** (0 warnings/errors)
  - Observação: `next lint` mostrou aviso de depreciação (“will be removed in Next.js 16”).
- `npm run build` → ✅ **OK** (build e geração de rotas estáticas)

Rotas geradas (App Router):
- `/`
- `/dashboard`
- `/cot`
- `/artifacts`
- `/command-center`

---

## Gaps (pensando em SaaS profissional)

### 1) “Wiring” backend (parcialmente implementado, precisa hardening)
Status atual (2026-01-26):
- `/dashboard` já chama `POST /api/gateway/stream` e consome SSE do `vertice-agent-gateway`.
- `/artifacts` já lista runs via `GET /api/gateway/runs`.
- `/settings` já lista/cria/seleciona org via `GET/POST /api/gateway/orgs` e cookie `vertice_org`.

O que ainda falta para “SaaS estilo claude-code-web” (production-ready):
- Tratamento de erros/retries no stream (reconnect com backoff, resumir por `run_id`).
- Status online confiável (hoje `GET /healthz` no Cloud Run do gateway retorna 404; usar `/openapi.json` como fallback
  até corrigir o deploy do gateway).
- Persistência de artifacts (não apenas “runs” + `final_text`).

### 2) Autenticação / multi‑tenant / billing (mínimo)
Para “SaaS pronto” normalmente entra:
- Auth (Google Identity Platform / Firebase Auth / OIDC) + sessão (cookies httpOnly) e proteção de rotas.
- Organização/time, RBAC (owner/admin/member), e trilha de auditoria.
- Billing (Stripe) + gating por plano (limites de uso).

### 3) Qualidade operacional no produto
- Observabilidade do cliente: logging estruturado de erros (Sentry/OTel frontend), tracing de requests.
- UX de carregamento: skeletons, empty states, “offline mode”, indicadores de streaming/latência.
- A11y: navegação por teclado, foco, aria em botões/inputs.
- Segurança de UI: CSP, headers, clickjacking, XSS hardening (especialmente ao renderizar markdown/artifacts).

### 4) Consistência de assets
Há dependência de assets remotos em CSS/background URLs. Para produção é mais robusto:
- hospedar assets no próprio app ou em bucket/CDN controlado,
- padronizar `next/font` (já usado) e evitar dependências externas não-versionadas quando possível.

---

## Recomendações (safe minimum para a próxima PR do frontend)
1) Implementar “plumbing” mínimo do plano 3.2:
   - manter o proxy atual `/api/gateway/*` e evoluir para retries/observabilidade.
   - trocar o “health check” para um endpoint que existe hoje (`/openapi.json`) até o `/healthz` voltar.
2) Definir um contrato de env vars (sem segredos no repo) e validar em runtime:
   - `NEXT_PUBLIC_*` só para dados públicos; segredos via Secret Manager no deploy.
3) Adicionar error boundary + página de erro (`app/error.tsx`) e 404 (`app/not-found.tsx`) se ainda não existir.

---

## Como reproduzir localmente (rápido)
Em `apps/web-console`:
- `npx tsc -p tsconfig.json`
- `npm run lint`
- `npm run build`
- `npm run dev` e navegar em `/dashboard`, `/cot`, `/artifacts`, `/command-center`

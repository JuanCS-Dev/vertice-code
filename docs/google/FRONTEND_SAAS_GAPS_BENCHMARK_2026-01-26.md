# Frontend SaaS Gaps (Benchmark 2026) — Vertice Web Console

Objetivo: listar o que normalmente existe em produtos “claude-code-web style” e quais lacunas ainda existem no
`apps/web-console` para lançamento SaaS profissional.

Fontes externas (referência de produto, não-Google):
- Claude Code on the web (Anthropic): https://www.anthropic.com/news/claude-code-on-the-web
- Claude Code on the web (docs): https://docs.claude.com/en/docs/claude-code/claude-code-on-the-web
- claude-code-web (open source): https://github.com/vultuk/claude-code-web

---

## 1) O que “produtos parecidos” fazem (padrão observado)

- **Multi-sessão / multi-run**: criar e gerenciar várias execuções em paralelo, com isolamento por sessão.
- **Persistência e reconexão**: reconectar e ver output histórico (buffer); sessões não morrem ao desconectar o browser.
- **Progresso em tempo real**: telemetria e status (queued/running/completed/failed), logs e etapas.
- **Integração com repositório**: conectar GitHub/repo, disparar tasks, gerar PRs/branches e mostrar diff.
- **Controles de segurança**:
  - auth “secure by default”
  - isolamento por org/workspace
  - proteção de credenciais (nunca expor secrets ao agente)
  - auditoria (quem fez o quê, quando)
- **Controles de produto**:
  - limites de uso (rate limits / quotas por plano)
  - billing/subscription
  - papéis (owner/admin/member) e convites
- **Operação**:
  - observabilidade (SLOs, alertas)
  - status page
  - incident playbooks (especialmente auth/outage)

---

## 2) Onde o Vertice já está forte (no estado atual)

- Login Google + session cookie (rota protegida) no `apps/web-console`.
- Stream SSE real no `/dashboard`.
- Multi-tenant mínimo no backend (org/workspace + membership + runs).
- “Recent Runs” no `/artifacts` e org management básico no `/settings`.

---

## 3) Lacunas para “SaaS profissional” (prioridade sugerida)

### P0 — Necessário para lançar
- **IAM hardening no Cloud Run** (backend privado; somente frontend invoca).
- **Hardening web básico**: headers de segurança (HSTS/CSP mínimo/XFO/etc) + CSRF mínimo para rotas cookie-auth.
- **Regras de tenant completas**: tudo o que for persistido deve carregar `org_id` e validar membership.
- **Persistência real**: runs + histórico (eventos) + artifacts (pelo menos metadados) em store gerenciado.
- **UX de reconexão**: retry/backoff e “resume stream” (ou reattach a run).
- **Política de limites**: rate limit por usuário/org (mesmo que simples) + proteção contra abuse.
- **Logout real** em todas as telas + UI de “who am I” (`/v1/me`).

### P1 — Diferencial competitivo
- **Projects/Repos**: conectar repo, escolher branch, executar tasks isoladas, exportar diff.
- **Artifacts real**: galeria baseada em dados reais (código/UI/SQL), preview e download.
- **Audit log** por org (mínimo: run created/finished/failed).

### P2 — Escala e enterprise
- Billing (Stripe) + quotas por plano
- SSO/SCIM, domínios, políticas de acesso
- Status page + incident automation

---

## 4) “Next PRs” executáveis (front-only)

- PR: padronizar um “layout shell” único (Sidebar/Header) para todas as rotas.
- PR: “Runs page” (histórico completo + filtros + status badges + link por `run_id`).
- PR: “Artifacts plumbing” (listar artifacts reais do backend; abrir/preview).

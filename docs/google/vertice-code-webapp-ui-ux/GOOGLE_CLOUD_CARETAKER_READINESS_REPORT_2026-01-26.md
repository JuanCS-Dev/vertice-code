# Google Cloud “Caretaker” Readiness Report (2026-01-26)

Escopo: validar (com brutal honestidade) o que já está pronto no monorepo para ficar **100% operado pela Google
Cloud** e o que ainda falta para deploy/observabilidade sem “máquina do dev”.

## 0) Definição crítica: “Prometheus”

Neste repositório:
- **Prometheus = Meta-Agent Prometheus** (subsistema interno do Vertice)
  - `packages/vertice-core/src/vertice_core/prometheus/`
  - MCP server: `packages/vertice-core/src/vertice_core/prometheus/mcp_server/`
- **Observability Prometheus** (GMP/MSP) = Cloud Monitoring / Managed Service for Prometheus (coisa diferente).

Este report não assume que “Prometheus” significa observabilidade.

## 1) Componentes “FULL GOOGLE” (o que precisa existir)

Para operar sem local:
1) **Build/Pub**: Cloud Build + Artifact Registry
2) **Runtime**: Cloud Run (gateway + MCP)
3) **Brains**: Vertex AI Reasoning Engine (regional) + inferência (global) via Vertex
4) **Memory**: AlloyDB (private networking/IAM) + migrations + smoke tests
5) **Secrets**: Secret Manager (+ KMS se GDPR exigir envelope keys)
6) **Observabilidade**: Cloud Logging + Cloud Monitoring (mínimo) / OTel ou GMP sidecar (opcional)
7) **Automação**: triggers (ou IaC) para não depender de scripts locais

## 2) Estado atual do repo (o que está pronto)

### 2.1 Gateway (AG-UI streaming)
- SSE + schema MVP `delta|tool|final|error` já implementados com frames extras (intent/thought/code_delta/trajectory).
- Persistência assíncrona de code deltas (AlloyDB se DSN configurado; fallback SQLite).
- Testes locais (offline) já existem e passaram neste ambiente:
  - `tests/integration/test_agent_gateway_agui_stream.py`
  - `tests/unit/test_thought_stream_splitter.py`

Doc de referência:
- `docs/google/vertice-code-webapp-ui-ux/BACKEND_NERVOUS_SYSTEM_TASK.md`

### 2.2 MCP (Meta-Agent Prometheus) — Cloud Run ready
- `Dockerfile.mcp` agora sobe o server real (`python -m vertice_core.prometheus.mcp_server.run_server`).
- `cloudbuild.mcp.yaml` agora builda no contexto da raiz e publica em Artifact Registry.
- Imports foram saneados (packaging-safe) e ToolRegistry inicializa de forma determinística.
- Teste local (sem sockets) passou:
  - `tests/unit/prometheus/test_mcp_server_http_smoke.py`

Doc/auditoria:
- `docs/google/MCP_CLOUD_RUN_INFRA_AUDIT_2026.md`

### 2.3 Reasoning Engine (Vertex)
- App `Queryable` do Coder está compatível com o contrato 2026:
  - `async def query(self, *, input=..., **kwargs)`
  - parsing de `input` (str/dict)
  - sem `asyncio.run()`
- `tools/deploy_brain.py` já executa empacotamento estável (`cwd` em `packages/vertice-core/src`) e escreve
  `apps/agent-gateway/config/engines.json`.
- SDK pin atualizado para paridade 2026:
  - `google-cloud-aiplatform==1.130.0`
  - `google-genai==1.60.0`

Checklist operacional:
- `docs/google/vertice-code-webapp-ui-ux/VERTEX_REASONING_ENGINE_DEPLOY_CHECKLIST_2026.md`

## 3) Gaps reais (o que impede “100% Google caretaker”)

### 3.1 Automação (o maior gap)
Hoje, muito fluxo ainda depende de execução local (“gcloud na máquina do dev”).

Para ser FULL GOOGLE, você precisa escolher um padrão e declarar como “fonte de verdade”:
- **IaC** (Terraform/Pulumi) + CI/CD (Cloud Build triggers), ou
- **Cloud Build triggers** + scripts idempotentes (menos ideal que IaC, mas funciona).

Sem isso, o sistema não está “aos cuidados da nuvem”.

### 3.2 Conectividade AlloyDB (Cloud Run → private DB)
O código suporta DSN/fallback, mas a infra precisa estar especificada (e testada):
- Serverless VPC Access Connector + rotas para private ranges, ou
- AlloyDB connector/proxy + IAM + TLS

Sem smoke test real no Cloud Run, o “cutover” não é confiável.

### 3.3 Secrets e chaves (GDPR/KMS)
Critério “zero local” exige:
- segredos em Secret Manager (DSN AlloyDB, IDs de engine, etc.)
- se GDPR exigir “chaves efêmeras”: Cloud KMS (envelope keys) e rotação/TTL documentada

### 3.4 Observabilidade (decisão explícita)
Hoje:
- Cloud Run metrics + Cloud Logging são suficientes para MVP.

Se você quer métricas custom (tools, tokens, latência por etapa), precisa escolher:
- OTel (recomendado) ou
- `/metrics` Prometheus + GMP sidecar

BRUTALMENTE HONESTO:
- o repo não expõe `/metrics` nem instrumenta OTel, então “sidecar GMP” por si só não resolve nada.

### 3.5 Convenções de imagens / repos (drift)
Há convenções competindo no repo:
- `cloudbuild.backend.yaml` publica em `vertice-cloud/...`
- `cloudbuild.mcp.yaml` publica em `vertice-cloud/...`
- scripts legados (`deploy-gcp.sh`) agora também usam `vertice-cloud/...`

Sem padronização, você terá deploys inconsistentes (e debug impossível).

## 4) Bloqueadores de validação “real cloud”

Este ambiente de execução (onde rodei os testes) apresentou bloqueio de DNS para chamadas às APIs do Google.
Consequência:
- não dá para concluir build/push/deploy “até o Google” daqui.

Isso NÃO invalida a correção de código/infra no repo, mas impede a validação online (Cloud Build/Run) nesta sessão.

## 5) Nota sobre Firestore Query Engine (blog)

A novidade do Firestore Query Engine (pipeline) pode ser relevante se você quiser:
- pipelines de ingestão/eventos,
- queries analíticas (ou materializações) para observabilidade/memória derivada.

Mas isso não substitui:
- AlloyDB (memória/embeddings/relacional) como “Source of Truth”,
- nem resolve o problema atual (deploy/empacotamento/engine runtime).

Conclusão: é uma potencial melhoria futura para *pipelines*, não uma dependência do cutover atual.

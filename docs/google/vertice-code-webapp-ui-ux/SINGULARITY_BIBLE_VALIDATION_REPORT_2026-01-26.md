# Validation Report — SINGULARITY_IMPLEMENTATION_BIBLE.md (2026-01-26)

Objetivo: validar a “Bible” contra (1) o **código atual do monorepo** e (2) a **documentação oficial Google Cloud**
mais recente disponível publicamente.

## 1) Veredito (brutalmente honesto)

**A Bible é uma boa direção macro, mas NÃO está consistente com o código atual e NÃO é suficiente para declarar o
sistema “100% aos cuidados da nuvem do Google”.**

Principais motivos:
- Contém **paths e componentes inexistentes/errados no repo** (ex: `vertice_cli`).
- Recomenda um padrão de métricas (Managed Prometheus sidecar) **sem haver instrumentação `/metrics`** no gateway/MCP.
- Não descreve (nem automatiza) o “chão de fábrica” necessário para operar sem intervenção local:
  - IaC/automação de **Service Accounts + IAM**, **Secrets**, **VPC Connector** (AlloyDB), **Cloud Build triggers**.

## 2) Validação contra o código (o que bate / o que não bate)

### 2.1 Bate com o código (OK)
- **Reasoning Engine é regional (us-central1)**:
  - Gateway lê `apps/agent-gateway/config/engines.json` e defaulta `location` para `us-central1`.
  - Deploy script `tools/deploy_brain.py` usa `vertexai.init(project=..., location=...)` e cria `ReasoningEngine`.
- **AlloyDB DSN via env** (com fallback local):
  - `VERTICE_ALLOYDB_DSN` / `ALLOYDB_DSN` aparecem no core e no script de migração.

### 2.2 Não bate com o código (inconsistências)

#### (A) MCP Evolution: paths incorretos
Bible diz:
- “Move `src/vertice_cli/prometheus` -> `packages/vertice-core/src/agents/prometheus`”
- “Dockerfile.mcp apontando `agents.prometheus.mcp_server.run_server`”

Realidade do repo:
- Não existe `vertice_cli/` neste monorepo.
- O MCP server real está em:
  - `packages/vertice-core/src/vertice_core/prometheus/mcp_server/run_server.py`
- O Dockerfile correto já aponta para:
  - `python -m vertice_core.prometheus.mcp_server.run_server`

#### (B) Nervous System: imagem/backend inconsistentes
Bible referencia:
- `us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/backend:latest`

Realidade do repo:
- `cloudbuild.backend.yaml` builda para:
  - `us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/backend:latest`
- `deploy-gcp.sh` também foi convergido para `vertice-cloud` (reduzindo drift operacional).

#### (C) Sidecar “Managed Prometheus” sem `/metrics`
Bible propõe sidecar `cloud-run-managed-prometheus`, mas:
- Não existe `/metrics` no gateway/MCP (busca por `/metrics`, `prometheus_client`, `opentelemetry` retornou vazio).
- Sem instrumentação, o sidecar não coleta nada útil.

## 3) Validação contra documentação Google Cloud (pontos-chave)

### 3.1 Reasoning Engine: regional, não “global”
Docs atuais do Vertex AI Agent Engine/Reasoning Engines listam **regiões suportadas** (ex: `us-central1`) e o
resource path é `projects/.../locations/{location}/reasoningEngines/...`.

Implicação prática:
- Mesmo que alguns modelos tenham “global endpoint” de inferência, o **runtime do Reasoning Engine é regional**.
- Portanto, a arquitetura correta é a que você já adotou no código:
  - Reasoning Engine em `us-central1`
  - (se necessário) inferência de modelo via endpoint “global” em um provider separado (não no engine runtime).

### 3.1.1 Gemini 3 (Vertex) e “global endpoint” (importante para evitar 404)
Os modelos Gemini 3 no Vertex AI (no momento) aparecem como **Preview** e, pela doc 2026, são atendidos no endpoint
**global**:
- `gemini-3-pro-preview`
- `gemini-3-flash-preview`

Se o sistema usar model IDs sem `-preview` (ex: `gemini-3-pro`) em `location="global"`, é esperado:
- `404 Not Found` (modelo não encontrado no endpoint) **ou**
- fallback invisível para um modelo/endpoint errado (inaceitável).

Status no código:
- `vertice_core.providers.vertex_ai.VertexAIProvider` agora defaulta para os model IDs `*-preview` quando o alias é
  `pro|flash`, preservando override explícito caso você force um model id diferente.

### 3.1.2 Claude 4.5 (Vertex) e versionamento por sufixo
Os modelos Claude via Vertex AI (partner models) são referenciados com sufixo de versão (ex: `@20250929`).

Exemplos na doc 2026:
- `claude-sonnet-4-5@20250929`
- `claude-opus-4-5@20251101`

Implicação prática:
- usar IDs “sem sufixo” (ou com versões inexistentes) tende a resultar em `404 Not Found` ou erros de modelo.

### 3.2 Cloud Run + Managed Service for Prometheus
Há um padrão oficial de coletor para Cloud Run, mas ele é útil quando:
- você expõe métricas (Prometheus/OpenTelemetry) e
- configura scrape/collector de forma consistente (secret/config, etc.).

Sem isso, o “observável” mínimo do Cloud Run continua sendo:
- Cloud Logging (stdout/stderr)
- Cloud Monitoring nativo (request count/latency/errors)

Referências (Google Cloud):
- Agent Engine (regiões suportadas): `docs.cloud.google.com/agent-builder/locations`
- Sidecar (Managed Prometheus) para Cloud Run: `cloud.google.com/stackdriver/docs/managed-prometheus/cloudrun-sidecar`
- Cloud Run + Managed Prometheus sidecar: `docs.cloud.google.com/run/docs/monitoring-managed-prometheus-sidecar`

Nota AlloyDB AI (embeddings):
- AlloyDB for PostgreSQL (managed): `cloud.google.com/alloydb/docs/ai/work-with-embeddings`
- AlloyDB Omni: `cloud.google.com/alloydb/omni/15.5.5/docs/work-with-embeddings`

### 3.3 SDK versions (2026) vs runtime drift
O deploy do Reasoning Engine depende do empacotamento (cloudpickle) e de SDKs que mudam rápido. Para evitar drift:
- `tools/deploy_brain.py` deve pin key deps de forma compatível com a doc 2026.

Status:
- atualizado para:
  - `google-cloud-aiplatform==1.130.0`
  - `google-genai==1.60.0`

## 4) “Só falta isso?” — Checklist do que ainda falta para “FULL GOOGLE CARETAKER”

Para ser honesto e operacional, ainda faltam (ou estão só “no papel”) itens críticos:

### 4.1 Automação/IaC (para não depender de máquina local)
- Terraform (ou equivalente) para:
  - APIs enablement
  - Artifact Registry repos
  - Cloud Run services (gateway + mcp) + env + secrets
  - Service Accounts + IAM bindings
  - AlloyDB cluster/instances + networking
  - Vertex Reasoning Engine deploy/updates (ou pipeline que rode `tools/deploy_brain.py`)

### 4.2 Secrets/keys (produção)
- Centralizar DSNs e chaves em Secret Manager (e, se exigido, KMS/Cloud KMS para envelope encryption).
- Cloud Run deve ler secrets via `--set-secrets`/mount e não via `.env` local.

### 4.3 AlloyDB (conectividade real)
- Se AlloyDB estiver em IP privado:
  - Cloud Run precisa de Serverless VPC Access Connector + rotas corretas.
  - Alternativa: AlloyDB Connector/Proxy com IAM.
- O código pode estar pronto, mas a infra não está declarada aqui.

### 4.4 Observabilidade “de verdade”
Decidir e implementar um dos caminhos:
- **Só Cloud Run nativo** (simples, suficiente para MVP).
- **Prometheus/OTel**:
  - instrumentar `/metrics` ou OTLP
  - adicionar sidecar/collector
  - dashboards/alerts

## 5) Conclusão objetiva
- A Bible faz sentido como visão macro, mas precisa ser **atualizada** para refletir:
  - paths reais (`vertice_core...`)
  - imagens reais (padronizar Artifact Registry)
  - o fato de que Managed Prometheus sidecar é opcional e depende de instrumentação
- E, mesmo com a Bible atualizada, ainda faltam itens de **automação/infra** para dizer que o sistema está “100%
nas mãos do Google” sem operação local.

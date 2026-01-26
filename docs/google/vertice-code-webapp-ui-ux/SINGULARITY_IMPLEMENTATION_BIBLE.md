# PROJECT SINGULARITY: GOOGLE CLOUD 2026 IMPLEMENTATION BIBLE

**STATUS:** NEEDS ALIGNMENT WITH CODEBASE (validated notes in `SINGULARITY_BIBLE_VALIDATION_REPORT_2026-01-26.md`)
**TARGET AGENT:** GPT 5.2
**MISSION:** 100% Cloud Migration (Zero Local Dependency)

Related (operational truth):
- `docs/google/vertice-code-webapp-ui-ux/GOOGLE_CLOUD_CARETAKER_READINESS_REPORT_2026-01-26.md`
- `docs/google/vertice-code-webapp-ui-ux/VERTEX_REASONING_ENGINE_DEPLOY_CHECKLIST_2026.md`
- `docs/google/MCP_CLOUD_RUN_INFRA_AUDIT_2026.md`

## 0. DISAMBIGUATION (CRITICAL: NO PROMETHEUS CONFUSION)

Neste repositório, **Prometheus = meta-agent interno do Vertice** (sub-sistema de agents/tools/memory), localizado em:
- `packages/vertice-core/src/vertice_core/prometheus/`
- MCP server (Prometheus meta-agent exposto via MCP): `packages/vertice-core/src/vertice_core/prometheus/mcp_server/`

**Prometheus (observabilidade)** é outra coisa: trata-se de “Managed Service for Prometheus” / “Cloud Monitoring”
na Google Cloud. Para evitar alucinação, este documento usa:
- **Meta-Agent Prometheus** = nosso subsistema `vertice_core.prometheus`
- **Observability (GMP/MSP)** = métricas/monitoramento no Google Cloud

## 0.1 GUARDRAILS (PRE-COMMIT / PRE-PUSH)

Objetivo: bloquear commit/push de alterações que **sabidamente** quebram o deploy no Google Cloud (Cloud Build + Cloud
Run + Reasoning Engine).

Instalação local (necessário para o “push ser bloqueado”):
```bash
pip install pre-commit
pre-commit install
pre-commit install -t pre-push
```

O que roda:
- **Commit:** varredura de policy em arquivos alterados (ex: proibição de Gemini 1/2) via
  `scripts/gcp_deploy_preflight.py`.
- **Push:** invariantes completas do repo + smoke tests via `tests/unit/test_gcp_deploy_guardrails.py`.

Bypass (deve ser raro, documentar o motivo):
```bash
git commit --no-verify
```

## 1. INFRASTRUCTURE FOUNDATION (IAM & NETWORK)

### 1.1 Service Accounts
Create dedicated identities for granular security (Principle of Least Privilege):
- `sa-vertice-brain`: For Vertex AI Agents.
- `sa-vertice-nervous`: For Cloud Run Gateway & MCP.
- `sa-vertice-memory`: For AlloyDB interaction.

Mínimo de IAM (não-exaustivo, ajustar ao modelo real de rede/segredos):
- `sa-vertice-nervous`:
  - Cloud Run runtime default + leitura de segredos (Secret Manager) + chamadas para Vertex (se gateway chamar).
- `sa-vertice-brain`:
  - Vertex AI (Reasoning Engine / Agent Engine runtime) + leitura de segredos (se necessário).
- `sa-vertice-memory`:
  - AlloyDB (via connector/proxy/IAM) + leitura de segredos do DSN/credenciais.

### 1.2 APIs to Enable
Ensure these are active before ANY deploy:
- `aiplatform.googleapis.com` (Vertex AI)
- `alloydb.googleapis.com` (AlloyDB)
- `run.googleapis.com` (Cloud Run)
- `monitoring.googleapis.com` (Observability: Cloud Monitoring)
- `logging.googleapis.com` (Cloud Logging)
- `secretmanager.googleapis.com`
- `artifactregistry.googleapis.com` (Artifact Registry)
- `cloudbuild.googleapis.com` (Cloud Build)
- `serviceusage.googleapis.com` (Service Usage / API enablement)
- `iam.googleapis.com` (IAM; often needed for service accounts / build flows)

---

## 2. DATA LAYER: ALLOYDB AI (THE SOURCE OF TRUTH)

### 2.1 Provisioning Spec
- **Region:** `us-central1`
- **Cluster:** `vertice-memory-cluster`
- **Instance:** `vertice-memory-primary` (4 vCPU, 32GB RAM minimum for vector workloads)

Networking (precisa escolher um modelo e declarar como padrão):
- Se AlloyDB for **private IP** (comum em produção): Cloud Run precisa de **Serverless VPC Connector** + rotas.
- Se usar **AlloyDB connector/proxy**: definir explicitamente como o runtime autentica (IAM/secret) e como faz TLS.

### 2.2 In-Database AI Configuration
Execute SQL via AlloyDB Studio:
```sql
CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE; -- Must be > v1.5.2
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS alloydb_scann;

-- Permission Grant (Critical)
GRANT EXECUTE ON FUNCTION embedding TO vertice_user;
```

Nota (importante):
- A configuração exata pode variar entre **AlloyDB for PostgreSQL (managed)** e **AlloyDB Omni** (flags e nomes de
  função `embedding` vs `google_ml.embedding`). Sempre confirmar antes do cutover.
- Em AlloyDB Omni, a documentação pede explicitamente `google_ml_integration` e (em alguns cenários) ajustar flags
  como `google_ml_integration.enable_model_support` antes de gerar embeddings.

---

## 3. INTELLIGENCE LAYER: VERTEX REASONING ENGINES

### 3.1 Deployment Manifest
Use `tools/deploy_brain.py` with explicit Service Account:
```bash
python3 tools/deploy_brain.py \
  --agent {agent_name} \
  --project vertice-ai \
  --location us-central1 \
  --staging-bucket gs://vertice-ai-reasoning-staging \
  --service-account sa-vertice-brain@vertice-ai.iam.gserviceaccount.com
```

Hard truth (2026): Reasoning/Agent Engine runtime é **regional** (ex: `us-central1`).
- “global” existe para endpoints de **inferência de modelos** (Gemini/Claude via Vertex), mas o **runtime do engine**
  continua regional (resource name sempre inclui `locations/{region}`).

Separação correta (evita tentativa-e-erro):
- **ReasoningEngine runtime**: `us-central1` (deploy do engine)
- **Model inference endpoint**: `global` (Gemini 3 Preview + Claude 4.5 via Vertex)

Model IDs (Vertex AI, 2026):
- Gemini 3: `gemini-3-pro-preview`, `gemini-3-flash-preview` (global only)
- Claude via Vertex (partner models, exemplos de versões atuais):
  - `claude-sonnet-4-5@20250929`
  - `claude-opus-4-5@20251101`

SDK baseline (Python, 2026):
- `google-cloud-aiplatform==1.130.0` (Reasoning Engines client)
- `google-genai==1.60.0` (Gemini/Claude inference on Vertex)

Referências oficiais (Google, 2026):
- Agent Engine / Reasoning Engines (locations): `https://cloud.google.com/agent-builder/docs/locations`
- Google Gen AI SDK + Gemini 3 Preview (Vertex): `https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-0-preview`
- Claude Sonnet 4.5 (Vertex): `https://cloud.google.com/vertex-ai/generative-ai/docs/models/anthropic/claude-sonnet-4.5`
- Claude Opus 4.5 (Vertex): `https://cloud.google.com/vertex-ai/generative-ai/docs/models/anthropic/claude-opus-4.5`
- Partner models overview: `https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-partner-models`

Para “zero local dependency”:
- Cloud Build trigger deve rodar `tools/deploy_brain.py` (ou equivalente) em pipeline, não na máquina do dev.
- `apps/agent-gateway/config/engines.json` precisa ser:
  - gerado automaticamente (deploy pipeline) **ou**
  - armazenado em Secret Manager / Config Store (evitar drift e commits manuais).

---

## 4. NERVOUS SYSTEM: CLOUD RUN GATEWAY (OBSERVABLE)

### 4.1 Sidecar Pattern (Prometheus)
Optional. Only apply if the service exposes `/metrics` (Prometheus) or OTLP and you’ve decided to run Managed Service
for Prometheus collection on Cloud Run.

BRUTALMENTE HONESTO: o exemplo abaixo deve seguir o padrão atual do Google (2026) para Cloud Run multi-container:
- annotation `run.googleapis.com/container-dependencies`
- sidecar image em Artifact Registry público (`us-docker.pkg.dev/cloud-ops-agents-artifacts/...`)
- se usar configuração custom (`RunMonitoring`), ela vive em Secret Manager e é referenciada via
  `run.googleapis.com/secrets` + volume mount em `/etc/rungmp/config.yaml`.

Update `service.yaml` to include the managed collector (exemplo):
```yaml
metadata:
  annotations:
    run.googleapis.com/container-dependencies: '{"collector":["app"]}'
    # Cloud Run YAML: map secret resource to a short name (used below).
    # Prefer gcloud `--set-secrets` if you want fewer YAML sharp edges.
    run.googleapis.com/secrets: run-gmp-config:projects/PROJECT_ID/secrets/run-gmp-config
spec:
  containers:
  - name: app
    image: us-central1-docker.pkg.dev/vertice-ai/vertice-cloud/backend:latest
    env:
    - name: VERTEX_AGENT_ENGINE_ENABLED
      value: "1"
  - name: collector
    image: us-docker.pkg.dev/cloud-ops-agents-artifacts/cloud-run-gmp-sidecar/cloud-run-gmp-sidecar:1.2.0
    volumeMounts:
    - name: config
      mountPath: /etc/rungmp
  volumes:
  - name: config
    secret:
      secretName: run-gmp-config
      items:
      - key: latest
        path: config.yaml
```

Referência oficial (Cloud Run + GMP sidecar):
- `https://cloud.google.com/run/docs/monitoring-managed-prometheus-sidecar`

BRUTALMENTE HONESTO: hoje no repo não há `/metrics` nem OTEL/OTLP no gateway/MCP.
- Sem instrumentação, o sidecar não entrega valor. Cloud Run já fornece métricas nativas (latência/erros/reqs).
- Decisão necessária:
  - (A) ficar no mínimo viável com Cloud Monitoring nativo, ou
  - (B) instrumentar Prometheus/OTel e então habilitar collector/sidecar.

Padronização de imagem (evitar 3 convenções):
- Hoje existem caminhos diferentes nos scripts/YAMLs para Artifact Registry.
- Padrão adotado (repo único): `us-central1-docker.pkg.dev/$PROJECT_ID/vertice-cloud/<service>:<tag>`
- Status (repo root):
  - `cloudbuild.backend.yaml` e `cloudbuild.frontend.yaml` convergidos para `vertice-cloud`
  - `cloudbuild.yaml` + `cloudbuild.us-central1.yaml` + `cloudbuild.europe-west1.yaml` + `cloudbuild.asia-southeast1.yaml`
    corrigidos para buildar o MCP com `Dockerfile.mcp` (sem path inexistente)

---

## 5. MCP EVOLUTION: PROMETHEUS AGENT

### 5.1 Refactoring Plan
- **Canonical path in this repo:** `packages/vertice-core/src/vertice_core/prometheus`
- **MCP server entrypoint:** `python -m vertice_core.prometheus.mcp_server.run_server`
- **Persist:** Connect to AlloyDB via `ALLOYDB_DSN` env var.

BRUTALMENTE HONESTO: MCP “real” (Cloud Run) já foi alinhado no código, mas o deploy cloud ficou bloqueado por DNS
neste ambiente de execução. Auditoria detalhada + checklist:
- `docs/google/MCP_CLOUD_RUN_INFRA_AUDIT_2026.md`

Segurança mínima para Cloud:
- `enable_execution_tools` deve continuar OFF por default e só ligar com `MCP_ENABLE_EXECUTION_TOOLS=1`.
- Qualquer ferramenta de execução precisa de hardening (RCE lockdown) antes de liberar em produção.

---

**Assinado,**
*Vertice-MAXIMUS*
*Reasoning Engine: Calibrated via Google Docs 2026.*

---

## 6. O QUE AINDA FALTA PARA “100% GOOGLE CARETAKER” (SEM OPERAÇÃO LOCAL)

Se a pergunta é “só falta isso?”: **não**. Falta (ou está incompleto) em produção:

### 6.1 Infra as Code / Automação
Você precisa de uma fonte de verdade (Terraform/Pulumi) ou automação equivalente para:
- Service Accounts + IAM bindings (brain/nervous/memory)
- Artifact Registry repos (padronizados)
- Cloud Build triggers (gateway + mcp + deploy_brain)
- Cloud Run services (gateway + mcp) com env/secrets/regions
- AlloyDB cluster/instance + networking

### 6.2 Segredos (Secret Manager)
Critério “zero local dependency”:
- DSNs e chaves NÃO podem viver em `.env`/máquina local.
- Cloud Run deve consumir segredos via Secret Manager (`--set-secrets` ou mounts).

### 6.3 Conectividade AlloyDB (Cloud Run → DB)
Definir e implementar um padrão:
- VPC Connector + private IP, ou
- Connector/Proxy com IAM + TLS
…e validar com smoke test real.

### 6.4 Observability (decisão + execução)
Escolher:
- Mínimo: Cloud Logging + Cloud Run metrics (OK para MVP)
- Completo: OTel/Prometheus + dashboards + alerts + tracing de requests/tool calls

### 6.5 Runbook (operação)
Para ficar “nas mãos do Google”, precisa de runbook:
- como redeployar gateway/mcp/brains sem máquina local
- rollback (imagens tags) + verificação de saúde
- alertas e SLOs

---

## 7. RUNBOOK EXECUTÁVEL (COMANDOS EXATOS)

Objetivo: subir **Gateway (Cloud Run)** + **MCP (Cloud Run)** + **Coder Brain (Vertex Reasoning Engine)** com o
mínimo de variação e seguindo a doc 2026.

### 7.1 Setup (1 vez por projeto)
```bash
export PROJECT_ID="vertice-ai"
export REGION="us-central1"
export STAGING_BUCKET="gs://vertice-ai-reasoning-staging"

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  serviceusage.googleapis.com \
  iam.googleapis.com \
  logging.googleapis.com \
  storage.googleapis.com

gcloud artifacts repositories create vertice-cloud \
  --repository-format=docker \
  --location="$REGION" \
  --description="Vertice container images" \
  --quiet || true
```

### 7.2 Build & Publish (Cloud Build)
Gateway (agent-gateway):
```bash
gcloud builds submit --config cloudbuild.backend.yaml .
```

MCP (Meta-Agent Prometheus):
```bash
gcloud builds submit --config cloudbuild.mcp.yaml .
```

### 7.3 Deploy (Cloud Run)
Gateway:
```bash
gcloud run deploy vertice-agent-gateway \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/vertice-cloud/backend:latest" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars VERTEX_AGENT_ENGINE_ENABLED=0
```

MCP:
```bash
gcloud run deploy vertice-mcp \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/vertice-cloud/mcp-server:latest" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars MCP_ENABLE_EXECUTION_TOOLS=0
```

### 7.4 Deploy “Brain” (Vertex Reasoning Engine)
Deploy do engine é **regional** (ex: `us-central1`), mesmo quando a inferência do modelo é `global`.
```bash
python3 tools/deploy_brain.py \
  --agent coder \
  --project "$PROJECT_ID" \
  --location "$REGION" \
  --staging-bucket "$STAGING_BUCKET"
```

### 7.5 Smoke Tests (real)
```bash
GATEWAY_URL="$(gcloud run services describe vertice-agent-gateway --region "$REGION" --format='value(status.url)')"
MCP_URL="$(gcloud run services describe vertice-mcp --region "$REGION" --format='value(status.url)')"

curl -sS "$GATEWAY_URL/healthz"
curl -sS "$MCP_URL/health"

# MCP JSON-RPC initialize + tools/list
curl -sS -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}' \
  "$MCP_URL/mcp"

curl -sS -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}' \
  "$MCP_URL/mcp"
```

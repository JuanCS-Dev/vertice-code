# Google Cloud Post‑Deploy Validation Report (2026‑01‑26)

**Contexto:** validação do deploy “toda infra para o Google” e fechamento do wiring mínimo para o frontend
Narcissus (Agent Gateway + MCP + AlloyDB).

**Data (UTC):** 2026‑01‑26
**Projeto:** `vertice-ai`
**Região:** `us-central1`

---

## 1) Resumo executivo (status)

**OK / Ready**
- Cloud Run: `vertice-agent-gateway` (Ready=True) — **Serverless VPC Access + DSN via Secret Manager**
- Cloud Run: `vertice-mcp` (Ready=True)
- Cloud Run: `vertice-backend` (Ready=True)
- Cloud Run: `vertice-frontend` (Ready=True)
- AlloyDB: `vertice-memory-cluster` / `vertice-memory-primary` (READY, private IP `10.66.0.2`)

**Update (2026‑01‑26): hardening “padrão Google”**
- Vertex AI: padrão **ADC/IAM** (sem API key no runtime).
- Cloud Run: service accounts dedicadas por serviço (least privilege).
- GKE: Backup for GKE (backup plan) + maintenance window recorrente.

**Observação importante para o frontend**
- Endpoint `GET /healthz` no `vertice-agent-gateway` retorna **404 (Google Frontend HTML)** no URL público do Cloud Run,
  apesar do OpenAPI listar `/healthz`. Isso impacta o “Status Mesh: SYSTEM ONLINE” do plano do frontend.
  - Evidência adicional: o `vertice-agent-gateway` está rodando uma imagem do repositório `vertice-cloud/backend`
    (mesma família do `vertice-backend`), o que sugere drift do que deveria ser o gateway. Recomenda-se alinhar o
    serviço para a imagem do gateway antes de qualquer hardening de IAM.

---

## 2) Inventário validado (gcloud)

### 2.1 Cloud Run (us-central1)
- Serviços:
  - `ssrverticeai` (**Ready=False**, mas responde 200; drift de imagem impede novas revisões)
  - `vertice-agent-gateway`
  - `vertice-mcp`
  - `vertice-frontend`
  - `vertice-backend`

### 2.2 AlloyDB (us-central1)
- Cluster: `vertice-memory-cluster` (READY)
- Instância primária: `vertice-memory-primary` (READY)
- Private IP: `10.66.0.2`

### 2.3 Networking
- VPC: `vertice-vpc`
- Subnet: `vertice-subnet` (`10.0.0.0/24`)
- PSA range (VPC peering): `vertice-psa-range` (`10.66.0.0/16`)
- Serverless VPC Access connector: `vertice-vpc-conn` (`10.8.0.0/28`, READY)

### 2.4 Secret Manager
- `vertice-alloydb-initial-password`: versão `1` (enabled)
- `vertice-alloydb-dsn`: versão `1` (enabled) — **criada nesta validação**
- `vertex-ai-key`: **0 versões** (não é mais usado pelo `vertice-backend` após migração para ADC/IAM)

---

## 3) Mudanças executadas (infra wiring do “sistema nervoso”)

Objetivo: permitir que o `vertice-agent-gateway` acesse o AlloyDB (private IP) e receba o DSN via Secret Manager.

1) Criado Serverless VPC Access connector:
- Nome: `vertice-vpc-conn`
- Rede: `vertice-vpc`
- Range: `10.8.0.0/28`
- Autoscaling: `minInstances=2`, `maxInstances=3`, `machineType=e2-standard-4`

2) Criado Secret Manager para DSN:
- Secret: `vertice-alloydb-dsn`
- Versão: `1`
- Payload: **não logado** (DSN gerado a partir do secret `vertice-alloydb-initial-password` e private IP do AlloyDB)

3) IAM (mínimo) para leitura do secret pelo Cloud Run:
- Service Account do serviço (atual): `cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com`
- Role no secret `vertice-alloydb-dsn`: `roles/secretmanager.secretAccessor` (SA dedicada)

4) Atualizado Cloud Run `vertice-agent-gateway`:
- Annotations:
  - `run.googleapis.com/vpc-access-connector=vertice-vpc-conn`
  - `run.googleapis.com/vpc-access-egress=private-ranges-only`
- Env:
  - `VERTICE_ALLOYDB_DSN` via Secret Manager `vertice-alloydb-dsn:1`

### 3.1 Log de comandos (reprodutível, sem vazar segredos)

Connector (Serverless VPC Access):
```bash
gcloud compute networks vpc-access connectors create vertice-vpc-conn \
  --region=us-central1 \
  --network=vertice-vpc \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-standard-4
```

Secret `vertice-alloydb-dsn` (payload gerado sem echo, a partir do password existente):
```bash
gcloud secrets create vertice-alloydb-dsn --replication-policy=automatic

export PASS="$(gcloud secrets versions access 1 --secret=vertice-alloydb-initial-password)"
python - <<'PY' | gcloud secrets versions add vertice-alloydb-dsn --data-file=- >/dev/null
import os, urllib.parse
pw = os.environ["PASS"]
print(
  "postgresql+asyncpg://postgres:"
  + urllib.parse.quote(pw, safe="")
  + "@10.66.0.2:5432/postgres?ssl=true",
  end="",
)
PY
```

IAM para leitura do secret pelo Cloud Run:
```bash
gcloud secrets add-iam-policy-binding vertice-alloydb-dsn \
  --member="serviceAccount:cr-vertice-agent-gateway@vertice-ai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Update do Cloud Run `vertice-agent-gateway` (connector + secret env var):
```bash
gcloud run services update vertice-agent-gateway \
  --region=us-central1 \
  --vpc-connector=vertice-vpc-conn \
  --vpc-egress=private-ranges-only \
  --set-secrets=VERTICE_ALLOYDB_DSN=vertice-alloydb-dsn:1
```

---

## 4) Validação (smoke tests online)

### 4.1 Agent Gateway
- `GET /openapi.json`: **200 OK**
- `GET /agui/stream?prompt=ping&session_id=smoke&agent=coder`: **SSE OK** (events `tool`, `delta`, `final`)
- `GET /docs`: **200 OK**
- `GET /healthz`: **404 HTML (Google Frontend)** — ver “Pendências”
- Cloud Logging (últimos ~15 min pós-deploy): **0 entradas `severity>=ERROR`**

### 4.2 MCP Server (Cloud Run)
- `GET /health`: **200 OK**
- `POST /mcp` com `initialize`: **200 OK** (JSON-RPC)

---

## 5) Validação (testes locais do monorepo)

Executado (rápido e específico):
```bash
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
pytest tests/unit/test_thought_stream_splitter.py -v -x
pytest tests/unit/prometheus/test_mcp_server_http_smoke.py -v -x
```

Resultado:
- ✅ Todos os testes acima passaram (11 tests).
- ⚠️ `pytest tests/unit -v -x` falha na coleta por `ImportError` em `tests/unit/agents/test_architect.py`:
  `cannot import name 'ARCHITECT_SYSTEM_PROMPT'`.

---

## 6) Prontidão para o frontend Narcissus (docs/google)

Plano de referência:
- `docs/google/PHASE_3_2_WIRING_NARCISSUS.md`
- `docs/google/vertice-code-webapp-ui-ux/BACKEND_NERVOUS_SYSTEM_TASK.md`

**O que está pronto para o PR 3.2-A / 3.2-C**
- `/agui/tasks` e `/agui/tasks/{task_id}/stream`: disponíveis via OpenAPI e no serviço `vertice-agent-gateway`.
- SSE multi-frame (intent/thought/code_delta/trajectory) está implementado no backend.
- “Memória” (AlloyDB) agora tem wiring infra mínimo (VPC connector + secret DSN).

**O que ainda bloqueia o PR 3.2-B (Status Mesh via /healthz)**
- `/healthz` não responde como JSON/200 no URL público do Cloud Run (retorna 404 HTML).
  - Ação recomendada: trocar a checagem do frontend para um endpoint que responda 200 hoje (ex.: `/docs` ou
    `/openapi.json`) **ou** corrigir o roteamento `/healthz` no gateway (preferível).

---

## 7) Pendências / Próximos passos (curto prazo)

1) **Fechar `ssrverticeai` (Ready=False)**
   - Decidir se o serviço ainda é necessário (parece estar ligado ao Firebase Hosting/frameworks).
   - Se necessário: redeploy para restaurar imagem no Artifact Registry e voltar a ter rollout/escala segura.
   - Se não for necessário: desativar/deletar com confirmação (evitar custos/ruído).

2) **Resolver `/healthz` no `vertice-agent-gateway`**
   Hoje o frontend não consegue confiar no “SYSTEM ONLINE” via `/healthz`.

3) (Opcional) **Alinhar drift com Terraform**
   Os arquivos em `infra/terraform/` descrevem subnet extra e `private_ip_google_access=true`, mas o estado
   atual tem apenas `vertice-subnet` com `privateIpGoogleAccess=False`.

---

## 8) Referências (Google Cloud — documentação oficial)

- Serverless VPC Access connector: https://cloud.google.com/vpc/docs/configure-serverless-vpc-access
- Cloud Run + VPC connector (gcloud examples): https://cloud.google.com/run/docs/configuring/vpc-connectors
- Cloud Run + Secret Manager (env vars): https://cloud.google.com/run/docs/configuring/services/secrets
- AlloyDB (visão geral / networking): https://cloud.google.com/alloydb/docs

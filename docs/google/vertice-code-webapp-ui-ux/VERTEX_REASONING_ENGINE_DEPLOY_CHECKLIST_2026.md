# Vertex AI Reasoning Engine — Deploy Checklist (2026)

Objetivo: parar o modo “tentar e errar” e executar deploys reprodutíveis (engine regional + inferência global),
com checklist auditável antes de apertar o botão.

## 0) Definições (não confundir)

- **Reasoning Engine runtime** = recurso gerenciado do Vertex AI (regional, ex: `us-central1`).
- **Model inference** = chamadas para modelos via Vertex AI (Gemini/Claude), pode ser **global**.

## 1) Pré-requisitos (sem isso, falha é esperada)

### 1.1 APIs (enable)
- `aiplatform.googleapis.com`
- `storage.googleapis.com` (staging bucket)
- `serviceusage.googleapis.com`
- `iam.googleapis.com`
- `logging.googleapis.com`

### 1.2 IAM (mínimo viável)
Service account do deploy/runtime do engine (ex: `sa-vertice-brain@...`) precisa:
- `roles/aiplatform.user` (ou role equivalente para Reasoning Engines)
- `roles/storage.objectAdmin` no bucket de staging (ou permissão equivalente)
- (recomendado) `roles/logging.logWriter` se o runtime exigir para logs

### 1.3 Bucket de staging (região compatível)
- bucket existe e está na **mesma região** (ou multiregion compatível) do engine, ex: `us-central1`
- exemplo: `gs://vertice-ai-reasoning-staging`

## 2) Contrato de App (Queryable) — “não vai startar” se errar

Motivos comuns de falha de startup no runtime:
- `ModuleNotFoundError` (imports quebrados por symlink/layout)
- `asyncio.run()` ou loop ownership incorreto (deadlock/hang)
- assinatura `query()` incompatível com o runtime

Checklist do código do app (ex: `CoderReasoningEngineApp`):
- `async def query(self, *, input=..., **kwargs)` (argumento primário nomeado `input`)
- `input` aceita `str` e `dict` (ex: `description|prompt|message`)
- **zero** `asyncio.run()` / `nest_asyncio` / “criar event loop”
- imports resolvem com `pip install -e packages/vertice-core` (sem sys.path hacks)

Arquivo atual (referência):
- `packages/vertice-core/src/agents/coder/reasoning_engine_app.py`

## 3) Empacotamento (cloudpickle) — mata 90% das falhas

### 3.1 Regras (para não cair no `No module named ...`)
- Nunca depender de symlinks do repo root no runtime do Google.
- Sempre deployar com cwd estável e `extra_packages` apontando para diretórios reais.

Status no repo:
- `tools/deploy_brain.py` faz `os.chdir(packages/vertice-core/src)` antes do create.
- `extra_packages` default: `["agents", "vertice_core", "vertice_agents"]`.

### 3.2 Requirements “paridade 2026”
Pinagem recomendada (reprodutível):
- `google-cloud-aiplatform==1.130.0`
- `cloudpickle==3.1.1`
- `google-genai==1.60.0`

Status no repo:
- `tools/deploy_brain.py` já está pinado com estas versões.

## 4) Location (o ponto que mais confunde)

### 4.1 Engine (regional)
Obrigatório:
- `--location us-central1` (ou outra região suportada pelo runtime)

### 4.2 Inferência (global)
Recomendado para modelos “top-tier” e partner models no Vertex AI:
- `location="global"` no provider de inferência

Model IDs (2026, Vertex AI):
- Gemini: `gemini-3-pro-preview`, `gemini-3-flash-preview`
- Claude (partner models, exemplos de versões atuais):
  - `claude-sonnet-4-5@20250929`
  - `claude-opus-4-5@20251101`

Status no repo:
- `vertice_core.providers.vertex_ai.VertexAIProvider` defaulta para `*-preview` e `location="global"`.

## 7) Referências oficiais (Google, 2026)

- Reasoning Engines locations: `https://cloud.google.com/agent-builder/docs/locations`
- Gemini 3 Preview (Vertex): `https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-0-preview`
- Partner models overview: `https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-partner-models`
- Claude Sonnet 4.5: `https://cloud.google.com/vertex-ai/generative-ai/docs/models/anthropic/claude-sonnet-4.5`
- Claude Opus 4.5: `https://cloud.google.com/vertex-ai/generative-ai/docs/models/anthropic/claude-opus-4.5`

## 5) Checklist de execução (passo-a-passo)

### 5.1 Preflight local (zero cloud)
- Import do app funciona sem sys.path hacks:
  - `python -c "from vertice_core.agents.coder.reasoning_engine_app import CoderReasoningEngineApp; print('OK')"`
- Preflight do deploy script (dry-run gera engines.json sem criar recurso):
  - `python tools/deploy_brain.py --agent coder --project vertice-ai --dry-run`

### 5.2 Deploy real (cloud)
- `python tools/deploy_brain.py --agent coder --project vertice-ai --location us-central1 --staging-bucket gs://...`
- Registrar `engine_id` em `apps/agent-gateway/config/engines.json` (feito pelo script)

### 5.3 Pós-deploy (smoke)
Se o ambiente tiver DNS/rotas ok:
- consultar status do recurso (Console/CLI)
- validar logs de startup (Cloud Logging) procurando:
  - `ModuleNotFoundError`
  - erros de credencial/ADC
  - dependências faltando (pip install)

## 6) “Falhou no start” — árvore de decisão

1) `ModuleNotFoundError`:
- confirmar `extra_packages` e cwd (sem symlink)
- confirmar imports: `vertice_core...` e `agents...` existem dentro de `packages/vertice-core/src`

2) `PermissionDenied` / `404` em modelos:
- confirmar projeto correto (`GOOGLE_CLOUD_PROJECT`)
- confirmar APIs habilitadas e IAM da SA
- confirmar model IDs e `location="global"` para modelos preview/partner

3) Timeout/hang:
- caçar `asyncio.run()` e loops criados manualmente
- confirmar `query` é async

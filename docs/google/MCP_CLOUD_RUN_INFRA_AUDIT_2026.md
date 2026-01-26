# MCP on Google Cloud (Cloud Run) — Infra Audit & Checklist (2026)

Data: 2026-01-26
Escopo: empacotamento, build (Cloud Build), runtime (Cloud Run), observabilidade e riscos de segurança para o MCP.

## 0) Contexto (sem adivinhação)
- “Prometheus” aqui é o subsistema interno do Vertice (não o Prometheus comercial).
- O objetivo é executar o **MCP Server real** em Cloud Run via imagem buildada no **contexto da raiz do monorepo**.

## 1) Estado real encontrado no repo (antes desta cirurgia)

### 1.1 Dockerfile do MCP apontava para servidor “placeholder”
- `Dockerfile.mcp` instalava `requirements.txt` do monorepo (pesado) e iniciava `scripts/mcp/simple_mcp_server.py`.
- O healthcheck usava `curl` sem instalar `curl` → healthcheck quebraria em ambientes que honram HEALTHCHECK.

### 1.2 Cloud Build MCP quebrado por path inexistente
- `cloudbuild.mcp.yaml` referenciava `prometheus/Dockerfile`, mas não existe um diretório `prometheus/` no root.

### 1.3 MCP server real existe, mas com empacotamento frágil
- Implementação real: `packages/vertice-core/src/vertice_core/prometheus/mcp_server/`.
- Os módulos importavam `from prometheus.mcp_server...` + `sys.path.insert(...)` para “forçar” resolução.
- Isso é frágil em runtimes gerenciados (Cloud Run / Vertex) porque:
  - depende de layout específico de diretórios;
  - não é compatível com instalação como pacote (`pip install -e ...`).

### 1.4 “Tool Registry” não era populado automaticamente
- `PrometheusMCPServer` expõe `tools/list`, mas **o registry inicia vazio** se nenhum módulo de ferramentas for importado.
- Comentário no código sugeria “Import tools to register them”, mas a importação não existia.

## 2) Mudanças aplicadas nesta etapa (infra + robustez)

### 2.1 Imports saneados (packaging-safe)
Arquivos:
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/run_server.py`
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/server.py`
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/transport.py`
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/manager.py`
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/tools/test_tool.py`

O que mudou:
- Removido `sys.path.insert(...)`.
- Imports passaram a ser relativos (`from .config ...`, `from .tools...`), evitando “mágica” de path.

### 2.2 Cloud Run compatibility (HOST/PORT)
Arquivo:
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/config.py`

O que mudou:
- `MCPServerConfig.from_env()` agora aceita:
  - host via `MCP_HOST` **ou** `HOST`
  - port via `MCP_PORT` **ou** `PORT` (Cloud Run)

### 2.3 Execução perigosa (RCE) virou opt-in
Arquivo:
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/config.py`

O que mudou:
- `enable_execution_tools` default agora é **False**.
- Pode ser habilitado explicitamente com `MCP_ENABLE_EXECUTION_TOOLS=1`.

### 2.4 ToolRegistry agora inicializa “de verdade”
Arquivo:
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/server.py`

O que mudou:
- Novo bootstrap de ferramentas no `__init__()` do server:
  - Importa módulos de tools com base em flags de config.
  - Ferramentas se auto-registram ao importar.
  - Falhas de import são logadas (não derrubam o server).

### 2.5 `/status` não quebra mais
Arquivo:
- `packages/vertice-core/src/vertice_core/prometheus/mcp_server/transport.py`

O que mudou:
- Removida tentativa inválida de `datetime.fromisoformat()` com `instance_id` (podia gerar 500).
- Usa `uptime_seconds` já calculado no `PrometheusMCPServer.get_stats()`.

### 2.6 Dockerfile do MCP virou “imagem real” de Cloud Run
Arquivo:
- `Dockerfile.mcp`

O que mudou:
- Instala deps mínimas do MCP: `scripts/mcp/requirements.txt` + `pip install -e packages/vertice-core`.
- Instala utilitários exigidos por tools: `git`, `ripgrep`, `curl`.
- Entry point passa a rodar o server real:
  - `python -m vertice_core.prometheus.mcp_server.run_server`

### 2.7 Cloud Build corrigido para usar o Dockerfile certo
Arquivo:
- `cloudbuild.mcp.yaml`

O que mudou:
- `-f Dockerfile.mcp` (contexto `.` na raiz do monorepo).

## 3) Testes e validação executados (neste ambiente)

### 3.1 Teste unitário “sem sockets”
Motivo:
- Este ambiente bloqueia bind/socket (PermissionError), então o teste valida handlers e JSON-RPC **sem abrir porta**.

Teste:
- `pytest tests/unit/prometheus/test_mcp_server_http_smoke.py -v -x`

Resultado:
- ✅ 1 passed

O que valida:
- `GET /health` via handler retorna 200 + `status=healthy`
- JSON-RPC `initialize` retorna `protocolVersion=2024-11-05`
- JSON-RPC `tools/list` retorna lista não vazia (bootstrap OK)
- `GET /status` retorna 200 + `uptime_seconds >= 0`

## 4) Checklists (o que precisa estar 100% OK para deploy “bem sucedido”)

### 4.1 Checklist Cloud Build (build/push)
- Artifact Registry existe (repo `vertice` em `us-central1`).
- Cloud Build SA tem permissão para push:
  - `roles/artifactregistry.writer`
- Build context é o root do monorepo (feito).
- Cloud Build YAML referencia Dockerfile existente (feito).

### 4.2 Checklist Cloud Run (runtime)
- Service name e region definidos (ex: `us-central1`).
- Service Account do Cloud Run:
  - `roles/logging.logWriter` (geralmente via runtime)
  - se usar outros serviços: `roles/aiplatform.user`, `roles/secretmanager.secretAccessor`, etc.
- `PORT` exposto e respeitado (feito: config lê `PORT`).
- Probes:
  - readiness/liveness via `GET /health` (endpoint existe e não 500).

### 4.3 Checklist Observabilidade (métricas/logs)
O mínimo (Cloud Run já entrega):
- Logs estruturados em stdout/err aparecem no Cloud Logging (OK).
- Métricas padrão do Cloud Run: request count/latency/errors (OK).

O recomendado (não implementado aqui; precisa decidir):
- Log correlation com trace:
  - capturar `X-Cloud-Trace-Context` e incluir `trace` nos logs JSON.
- Tracing distribuído (OpenTelemetry) se houver chamadas a Vertex/AlloyDB.
- Alertas:
  - taxa de erro 5xx, latência p95, reinícios, saturação de CPU/mem.

### 4.4 Checklist Segurança (MCP)
- `enable_execution_tools` permanece OFF por default (feito).
- Se habilitar `MCP_ENABLE_EXECUTION_TOOLS=1`, revisar:
  - lista de comandos permitidos
  - limites de tempo/memória/saída
  - bloqueio de rede/metadata server (SSRF já existe em `web_tools.py`)
- Git tools exigem `git` (instalado no Dockerfile).
- Search tools preferem `rg` (instalado no Dockerfile).

## 5) “Buracos” restantes (brutalmente honesto)

### 5.1 Grande dívida: imports `prometheus.*` no restante do vertice-core
- Existe uso amplo de `from prometheus...` em módulos fora do MCP server.
- Isso é incompatível com empacotamento normal (`pip install`) se não houver um pacote `prometheus` real.
- Para runtimes gerenciados (Cloud Run / Vertex), isso é um risco recorrente de `ModuleNotFoundError`.

Recomendação:
- Normalizar imports para `vertice_core.prometheus...` **ou** criar um shim package `prometheus/` que reexporta
  `vertice_core.prometheus` (decisão de arquitetura).

### 5.2 Tool coverage e dependências opcionais
- Algumas tools dependem de libs não pinadas no `scripts/mcp/requirements.txt` (ex: PDF parsing).
- Algumas tools dependem de binários adicionais (além de `git`/`rg`).

Recomendação:
- Definir “perfil de toolset” para Cloud Run (safe-by-default) e explicitar deps/binaries por perfil.

## 6) Comandos sugeridos (não executados aqui)

Build (Cloud Build):
- `gcloud builds submit --config cloudbuild.mcp.yaml .`

Deploy (Cloud Run):
- `gcloud run deploy vertice-mcp --image us-central1-docker.pkg.dev/$PROJECT_ID/vertice-cloud/mcp-server:latest --region us-central1 --allow-unauthenticated --port 8080`

Smoke test após deploy:
- `curl -sS $MCP_URL/health`
- JSON-RPC:
  - `curl -sS -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}' $MCP_URL/mcp`
  - `curl -sS -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}' $MCP_URL/mcp`

## 7) Tentativa de deploy a partir deste ambiente (bloqueada por DNS)

Eu tentei validar “até o Google” usando a sua autorização (gcloud logado), porém este ambiente não resolve DNS.

Evidências:
- `gcloud services list --enabled` falha com `NameResolutionError` ao resolver `serviceusage.googleapis.com`.
- `python -c "import socket; socket.getaddrinfo('serviceusage.googleapis.com', 443)"` falha com `socket.gaierror`.
- `/etc/resolv.conf` aponta para `nameserver 127.0.0.53` (stub do systemd-resolved), mas:
  - `resolvectl status` retorna `sd_bus_open_system: Operation not permitted`.

Impacto:
- Sem DNS, não dá para chamar Cloud Build/Run/APIs; portanto **não é possível** concluir build/push/deploy real daqui.

Próximo passo (executar no seu host onde DNS funciona):
- Build: `gcloud builds submit --config cloudbuild.mcp.yaml .`
- Deploy: `gcloud run deploy vertice-mcp --image us-central1-docker.pkg.dev/$PROJECT_ID/vertice-cloud/mcp-server:latest --region us-central1 --allow-unauthenticated --port 8080`
- Validar: executar os `curl` do item 6 e checar logs do serviço Cloud Run.

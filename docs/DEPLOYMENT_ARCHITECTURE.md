# 🏗️ VERTICE - Deployment Architecture
**Última atualização**: 07 de Janeiro de 2026
**Preparado para**: Google Cloud Run Deploy

---

## 📊 Visão Geral do Projeto

VERTICE é dividido em **4 componentes principais** para deployment:

```
┌─────────────────────────────────────────────────────────┐
│                    VERTICE ECOSYSTEM                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Landing Page (Firebase)        ✅ DEPLOYED         │
│     ├── URL: https://vertice-landing.web.app           │
│     └── Account: juan.brainfarma@gmail.com             │
│                                                         │
│  2. Web App Frontend (Cloud Run)   📦 TO DEPLOY        │
│     ├── Next.js 16.1.1                                 │
│     ├── Port: 8080                                     │
│     └── Account: juancs.d3v@gmail.com                  │
│                                                         │
│  3. Web App Backend (Cloud Run)    📦 TO DEPLOY        │
│     ├── FastAPI 0.115.0+                               │
│     ├── Port: 8000                                     │
│     ├── Integrates with MCP Server                     │
│     └── Account: juancs.d3v@gmail.com                  │
│                                                         │
│  4. MCP Server (Cloud Run)         📦 TO DEPLOY        │
│     ├── Prometheus MCP Gateway                         │
│     ├── Port: 3000                                     │
│     ├── 58 ferramentas expostas                        │
│     └── Account: juancs.d3v@gmail.com                  │
│                                                         │
│  5. CLI/TUI (Local execution)      ✅ FUNCTIONAL       │
│     └── Local only (não precisa deploy)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔗 Arquitetura de Comunicação

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Landing    │         │   Frontend   │         │   Backend    │
│   (Firebase) │────────▶│  (Next.js)   │────────▶│  (FastAPI)   │
│              │         │              │         │              │
│  Port: 443   │         │  Port: 8080  │         │  Port: 8000  │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                                                          │ HTTP/WS
                                                          │
                                                          ▼
                                                  ┌──────────────┐
                                                  │  MCP Server  │
                                                  │ (Prometheus) │
                                                  │              │
                                                  │  Port: 3000  │
                                                  └──────────────┘

Flow de dados:
1. User → Landing (Firebase) → Frontend (Cloud Run)
2. Frontend → Backend (FastAPI) via HTTP/WebSocket
3. Backend → MCP Server via HTTP (mcp_client.py)
4. MCP Server executa tools (58 ferramentas)
5. Response flow: MCP → Backend → Frontend → User
```

---

## 📦 Componente 1: Landing Page

**Status**: ✅ **DEPLOYED (Firebase)**

**Stack**:
- Framework: Next.js (estático)
- Hosting: Firebase Hosting
- CDN: Firebase CDN
- SSL: Firebase automaticamente

**Account**: `juan.brainfarma@gmail.com`

**Deployment**:
```bash
cd landing
npm run build
firebase deploy --only hosting
```

**URLs**:
- Production: https://vertice-landing.web.app
- Staging: https://vertice-landing--staging.web.app

---

## 📦 Componente 2: Web App Frontend

**Status**: 📦 **TO DEPLOY (Cloud Run)**

### Stack
- **Framework**: Next.js 16.1.1
- **Runtime**: Node.js 22 Alpine
- **Package Manager**: pnpm
- **Build Output**: Standalone mode
- **Port**: 8080 (Cloud Run default)

### Dependências Principais
```json
{
  "next": "16.1.1",
  "react": "19.2.3",
  "firebase": "^11.1.0",
  "@monaco-editor/react": "^4.7.0",
  "@xterm/xterm": "^6.0.0",
  "@tanstack/react-query": "^5.90.16",
  "@sentry/nextjs": "^10.32.1"
}
```

### Dockerfile Existente
**Localização**: `/vertice-chat-webapp/frontend/Dockerfile`

**Features**:
- Multi-stage build (deps → builder → runner)
- Non-root user (nextjs:nodejs)
- Health check `/api/health`
- Optimized for Cloud Run

### Variáveis de Ambiente Necessárias (Firebase)
```bash
# Firebase Config (Client Side)
NEXT_PUBLIC_FIREBASE_API_KEY=AIza_EXAMPLE...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=vertice-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=vertice-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=vertice-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=1:...

# Backend API
NEXT_PUBLIC_API_URL=https://vertice-backend-xxx.run.app
```

### Build e Deploy
```bash
cd vertice-chat-webapp/frontend

# Build Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/vertice-frontend:latest

# Deploy to Cloud Run
gcloud run deploy vertice-frontend \
  --image gcr.io/PROJECT_ID/vertice-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --max-instances 10 \
  --set-env-vars "NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1"
```

---

## 📦 Componente 3: Web App Backend

**Status**: 📦 **TO DEPLOY (Cloud Run)**

### Stack
- **Framework**: FastAPI 0.115.0+
- **Runtime**: Python 3.11 slim
- **ASGI Server**: Uvicorn
- **Port**: 8000

### Dependências Principais
```python
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
httpx>=0.27.2              # MCP Client
sse-starlette>=2.1.3       # SSE streaming
python-socketio>=5.11.4    # WebSocket
mcp>=1.1.0                 # MCP Protocol SDK
anthropic>=0.39.0          # Claude SDK
sqlalchemy[asyncio]==2.0.35
sentry-sdk[fastapi]==2.16.0
```

### Dockerfile Existente
**Localização**: `/vertice-chat-webapp/backend/Dockerfile`

**Features**:
- Multi-stage build (builder → runtime)
- Health check `/health`
- Uvicorn with ASGI

### Estrutura da API
```
vertice-chat-webapp/backend/app/
├── main.py                 # FastAPI app entry point
├── core/
│   ├── config.py          # Settings management
│   ├── exceptions.py      # Custom exceptions
│   └── observability.py   # Telemetry/Sentry
├── api/v1/
│   ├── chat.py            # Chat endpoint
│   ├── agents.py          # Agent execution
│   ├── terminal.py        # Terminal WebSocket
│   ├── executor.py        # MCP tool execution
│   ├── artifacts.py       # Code artifacts
│   ├── teleport.py        # Teleport features
│   └── billing.py         # Billing management
└── integrations/
    └── mcp_client.py      # ✅ MCP HTTP Client
```

### Integração com MCP Server
**Arquivo**: `app/integrations/mcp_client.py`

**Features**:
- Circuit breaker pattern
- Automatic retry (exponential backoff)
- Timeout protection (30s default)
- Connection pooling (httpx)

**Usage**:
```python
from app.integrations.mcp_client import MCPClient

async with MCPClient("http://vertice-mcp:3000") as client:
    # List tools
    tools = await client.list_tools()

    # Execute command
    result = await client.execute_command("ls -la")

    # Read file
    content = await client.read_file("/path/to/file")
```

### Variáveis de Ambiente Necessárias
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Redis Cache
REDIS_URL=redis://host:6379/0

# MCP Server
MCP_SERVER_URL=http://vertice-mcp:3000
MCP_CLIENT_TIMEOUT=30
MCP_CIRCUIT_BREAKER_THRESHOLD=3

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Authentication
CLERK_SECRET_KEY=sk_test_...

# Observability
SENTRY_DSN=https://...@sentry.io/...
OTEL_ENABLED=true

# Security
CORS_ORIGINS=https://vertice-frontend.run.app,https://vertice.com
SECRET_KEY=super-secret-key-change-in-production
```

### Build e Deploy
```bash
cd vertice-chat-webapp/backend

# Build Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/vertice-backend:latest

# Deploy to Cloud Run
gcloud run deploy vertice-backend \
  --image gcr.io/PROJECT_ID/vertice-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 20 \
  --concurrency 80 \
  --set-env-vars "DATABASE_URL=...,MCP_SERVER_URL=..."
```

---

## 📦 Componente 4: MCP Server (Prometheus Gateway)

**Status**: 📦 **TO DEPLOY (Cloud Run)**

### Stack
- **Framework**: MCP Protocol 1.1.0+
- **Runtime**: Python 3.11 slim
- **Transport**: HTTP + WebSocket
- **Port**: 3000

### Ferramentas Expostas (58 total)
```
prometheus/mcp_server/tools/
├── file_tools.py         (10 tools) - read, write, edit, delete, etc.
├── search_tools.py       (4 tools)  - search_files, glob, ls, tree
├── execution_tools.py    (3 tools)  - bash_command, background, kill
├── git_tools.py          (9 tools)  - status, diff, commit, PR, etc.
├── web_tools.py          (2 tools)  - web_fetch, web_search
├── media_tools.py        (3 tools)  - image, PDF, screenshot
├── context_tools.py      (5 tools)  - context, session, todo
├── prometheus_tools.py   (8 tools)  - Prometheus-specific
├── notebook_tools.py     (2 tools)  - Jupyter notebook read/edit
├── advanced_tools.py     (6 tools)  - multi_edit, plan_mode
├── agent_tools.py        (5 tools)  - Agent meta-tools
└── system_tools.py       (1 tool)   - think
```

### Arquitetura do MCP Server
```
prometheus/mcp_server/
├── manager.py            # Lifecycle management
├── server.py             # PrometheusMCPServer core
├── config.py             # MCPServerConfig
├── transport.py          # HTTP/WebSocket transport
└── tools/
    ├── registry.py       # Tool Registry System
    ├── base.py           # BaseTool, ToolDefinition
    ├── validated.py      # ValidatedTool wrapper
    └── [58 tool modules]
```

### Entry Points
1. **Standalone**: `python -m prometheus.mcp_server.manager --host 0.0.0.0 --port 3000`
2. **CLI**: `python prometheus/mcp_server/manager.py`
3. **Programmatic**: `from prometheus.mcp_server.manager import MCPServerManager`

### Dockerfile Necessário (TO CREATE)
**Localização**: `/prometheus/Dockerfile`

```dockerfile
# MCP Server Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY prometheus/ ./prometheus/
COPY vertice_core/ ./vertice_core/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:3000/health', timeout=3.0)"

# Run MCP Server
CMD ["python", "-m", "prometheus.mcp_server.manager", "--host", "0.0.0.0", "--port", "3000"]
```

### Variáveis de Ambiente Necessárias
```bash
# Server Config
MCP_HOST=0.0.0.0
MCP_PORT=3000
MCP_LOG_LEVEL=INFO

# Feature Flags
MCP_ENABLE_FILE_TOOLS=true
MCP_ENABLE_GIT_TOOLS=true
MCP_ENABLE_WEB_TOOLS=true
MCP_ENABLE_MEDIA_TOOLS=true
MCP_ENABLE_PROMETHEUS_TOOLS=true
MCP_ENABLE_EXECUTION_TOOLS=true  # ⚠️ Security-sensitive
MCP_ENABLE_NOTEBOOK_TOOLS=true

# Execution Security
MCP_EXECUTION_TIMEOUT=30
MCP_MAX_OUTPUT_BYTES=1048576  # 1MB
MCP_MAX_MEMORY_MB=512

# Git Security
MCP_GIT_PROTECTED_BRANCHES=main,master,develop

# Performance
MCP_MAX_CONCURRENT_REQUESTS=10
MCP_REQUEST_TIMEOUT=30
MCP_ENABLE_CACHING=true
```

### Build e Deploy
```bash
cd /media/juan/DATA/Vertice-Code

# Build Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/vertice-mcp:latest \
  --file prometheus/Dockerfile .

# Deploy to Cloud Run
gcloud run deploy vertice-mcp \
  --image gcr.io/PROJECT_ID/vertice-mcp:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \  # ⚠️ Ou configurar auth se necessário
  --port 3000 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 10 \
  --concurrency 80 \
  --set-env-vars "MCP_HOST=0.0.0.0,MCP_PORT=3000"
```

---

## 🔐 Security Considerations

### MCP Server Security
1. **Command Execution**: `CommandSecurityValidator` ativo
   - Blacklist de comandos perigosos (rm -rf /, fork bombs, etc.)
   - Regex patterns para blocked operations
   - Resource limits (timeout, memory, output)

2. **Git Operations**: `GitSafetyConfig` ativo
   - Protected branches (main, master, develop)
   - Dangerous flags blocked (--force, --hard, -i)
   - Commit message validation

3. **Path Sanitization**: Validação de paths para prevenir traversal attacks

### Network Security
```
┌─────────────┐
│   Landing   │  ← Firebase (HTTPS automático)
└─────────────┘

┌─────────────┐
│  Frontend   │  ← Cloud Run (HTTPS automático)
└──────┬──────┘
       │
       │ HTTPS + CORS
       ▼
┌─────────────┐
│   Backend   │  ← Cloud Run (HTTPS + JWT auth)
└──────┬──────┘
       │
       │ HTTP interno (VPC)
       ▼
┌─────────────┐
│  MCP Server │  ← Cloud Run (VPC interno ou auth API key)
└─────────────┘
```

**Recommendations**:
1. **Frontend → Backend**: HTTPS + CORS configurado
2. **Backend → MCP**: Usar VPC interno ou API key authentication
3. **MCP execution tools**: Considerar desabilitar em produção ou limitar por IP

---

## 📈 Monitoring & Observability

### Sentry Integration
- Frontend: `@sentry/nextjs`
- Backend: `sentry-sdk[fastapi]`

### OpenTelemetry
- Backend tem `opentelemetry-instrumentation-fastapi`
- Traces, metrics, logs

### Health Checks
```bash
# Frontend
curl https://vertice-frontend.run.app/api/health

# Backend
curl https://vertice-backend.run.app/health

# MCP Server
curl https://vertice-mcp.run.app/health
```

---

## 🚀 Deployment Sequence

### Ordem Recomendada
```
1. ✅ Landing (já deployed no Firebase)
   └── Nenhuma ação necessária

2. 📦 MCP Server (primeiro - base dependency)
   ├── Criar Dockerfile
   ├── Build image
   ├── Deploy to Cloud Run
   └── Testar health check

3. 📦 Backend (segundo - depende do MCP)
   ├── Build image
   ├── Deploy to Cloud Run
   ├── Configurar MCP_SERVER_URL
   └── Testar integração com MCP

4. 📦 Frontend (último - depende do Backend)
   ├── Build image
   ├── Deploy to Cloud Run
   ├── Configurar NEXT_PUBLIC_API_URL
   └── Testar integração completa
```

### Rollback Strategy
```bash
# Se deploy falhar, rollback para versão anterior
gcloud run services update-traffic vertice-mcp \
  --to-revisions PREVIOUS_REVISION=100

gcloud run services update-traffic vertice-backend \
  --to-revisions PREVIOUS_REVISION=100

gcloud run services update-traffic vertice-frontend \
  --to-revisions PREVIOUS_REVISION=100
```

---

## 🧪 Testing Strategy

### Pre-Deploy Tests
```bash
# 1. MCP Server
cd prometheus
pytest tests/unit/test_mcp_tools_basic.py

# 2. Backend
cd vertice-chat-webapp/backend
pytest tests/ -v

# 3. Frontend
cd vertice-chat-webapp/frontend
npm test
```

### Post-Deploy Tests
```bash
# 1. Health checks
curl https://vertice-mcp.run.app/health
curl https://vertice-backend.run.app/health
curl https://vertice-frontend.run.app/api/health

# 2. E2E integration test
# Frontend → Backend → MCP → Tool Execution
curl -X POST https://vertice-backend.run.app/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "List files in current directory", "agent": "executor"}'
```

---

## 💰 Cost Estimation (Cloud Run)

### Expected Monthly Costs (estimate)
```
MCP Server:
  - Requests: ~100K/month
  - Memory: 2 GB
  - CPU: 2 vCPU
  - Estimate: $20-30/month

Backend:
  - Requests: ~500K/month
  - Memory: 1 GB
  - CPU: 2 vCPU
  - Estimate: $30-50/month

Frontend:
  - Requests: ~1M/month (with CDN caching)
  - Memory: 512 MB
  - CPU: 1 vCPU
  - Estimate: $10-20/month

TOTAL: ~$60-100/month (Cloud Run only)
```

**Additional Costs**:
- Cloud Storage (artifacts, logs): $5-10/month
- Cloud SQL (se usado): $25-50/month
- Sentry: $26/month (Team plan)
- Firebase Hosting: Grátis (Spark plan)

---

## 🎯 Next Steps

### Immediate Actions (P0)
1. ✅ Criar Dockerfile para MCP Server
2. ✅ Corrigir violations do CODE_CONSTITUTION
3. ✅ Testar builds locais
4. Deploy MCP Server
5. Deploy Backend
6. Deploy Frontend
7. E2E testing

### Post-Deploy (P1)
1. Configure CI/CD (GitHub Actions)
2. Setup monitoring dashboards
3. Configure auto-scaling policies
4. Implement canary deployments
5. Setup backup/disaster recovery

---

**Preparado por**: Claude Sonnet 4.5
**Data**: 07 de Janeiro de 2026
**Account GCP**: juancs.d3v@gmail.com
**Account Firebase**: juan.brainfarma@gmail.com

**Soli Deo Gloria** 🙏

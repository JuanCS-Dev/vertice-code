# 🚀 VERTICE - Quick Deploy Guide
**Deploy para Google Cloud Run em 5 minutos**

---

## ⚡ Deploy Automatizado (Recomendado)

### Pré-requisitos
```bash
# 1. Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# 2. Ter um projeto GCP criado
# https://console.cloud.google.com

# 3. Docker instalado e rodando
docker --version
```

### Deploy em 1 Comando

```bash
# Configure seu PROJECT_ID
export GCP_PROJECT_ID="seu-project-id"

# Execute o script de deployment
./deploy-gcp.sh
```

**Isso irá**:
1. ✅ Autenticar no GCP
2. ✅ Habilitar APIs necessárias
3. ✅ Build e deploy MCP Server
4. ✅ Build e deploy Backend
5. ✅ Build e deploy Frontend
6. ✅ Configurar variáveis de ambiente automaticamente

**Duração**: ~15-20 minutos (primeira vez com build)

---

## 🔧 Deploy Manual (Passo a Passo)

### 1. Autenticação

```bash
gcloud auth login --account juancs.d3v@gmail.com
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

### 2. Deploy MCP Server

```bash
# Build da imagem
cd /media/juan/DATA/Vertice-Code
gcloud builds submit \
  --tag gcr.io/YOUR_PROJECT_ID/vertice-mcp:latest \
  --file prometheus/Dockerfile .

# Deploy no Cloud Run
gcloud run deploy vertice-mcp \
  --image gcr.io/YOUR_PROJECT_ID/vertice-mcp:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 10

# Salvar URL
export MCP_URL=$(gcloud run services describe vertice-mcp --region=us-central1 --format='value(status.url)')
echo "MCP Server URL: $MCP_URL"
```

### 3. Deploy Backend

```bash
# Build da imagem
cd vertice-chat-webapp/backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vertice-backend:latest .

# Deploy no Cloud Run
gcloud run deploy vertice-backend \
  --image gcr.io/YOUR_PROJECT_ID/vertice-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 20 \
  --set-env-vars "MCP_SERVER_URL=$MCP_URL"

# Salvar URL
export BACKEND_URL=$(gcloud run services describe vertice-backend --region=us-central1 --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

### 4. Deploy Frontend

```bash
# Build da imagem
cd ../frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vertice-frontend:latest .

# Deploy no Cloud Run
gcloud run deploy vertice-frontend \
  --image gcr.io/YOUR_PROJECT_ID/vertice-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --max-instances 10 \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL,NODE_ENV=production"

# Salvar URL
export FRONTEND_URL=$(gcloud run services describe vertice-frontend --region=us-central1 --format='value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
```

---

## ✅ Testes Pós-Deploy

### 1. Health Checks

```bash
# MCP Server
curl $MCP_URL/health

# Backend
curl $BACKEND_URL/health

# Frontend
curl $FRONTEND_URL/api/health
```

### 2. Testar MCP Tools

```bash
# Listar ferramentas disponíveis
curl -X POST $MCP_URL/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": "1"
  }'

# Executar comando bash
curl -X POST $MCP_URL/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": "2",
    "params": {
      "name": "bash_command",
      "arguments": {"command": "echo Hello from MCP!"}
    }
  }'
```

### 3. Testar Integração Completa

```bash
# Executar agent via Backend
curl -X POST $BACKEND_URL/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "List the current directory files",
    "agent": "executor"
  }'
```

---

## 🔐 Configuração de Variáveis de Ambiente

### MCP Server
Já configuradas automaticamente no deploy.

### Backend
```bash
# Configurar secrets (opcional)
gcloud run services update vertice-backend \
  --update-env-vars DATABASE_URL=... \
  --update-env-vars REDIS_URL=... \
  --update-env-vars ANTHROPIC_API_KEY=... \
  --update-env-vars CLERK_SECRET_KEY=...
```

### Frontend
```bash
# Configurar Clerk auth
gcloud run services update vertice-frontend \
  --update-env-vars NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=... \
  --update-env-vars CLERK_SECRET_KEY=...
```

---

## 📊 Monitoramento

### Ver Logs

```bash
# MCP Server logs
gcloud run services logs read vertice-mcp --region=us-central1

# Backend logs
gcloud run services logs read vertice-backend --region=us-central1

# Frontend logs
gcloud run services logs read vertice-frontend --region=us-central1
```

### Ver Métricas

```bash
# Abrir Cloud Console
open https://console.cloud.google.com/run?project=YOUR_PROJECT_ID
```

---

## 🔄 Updates e Rollback

### Update de um serviço

```bash
# Rebuild e redeploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vertice-mcp:latest -f prometheus/Dockerfile .
gcloud run services update vertice-mcp --image gcr.io/YOUR_PROJECT_ID/vertice-mcp:latest
```

### Rollback para versão anterior

```bash
# Listar revisões
gcloud run revisions list --service=vertice-mcp --region=us-central1

# Rollback para revisão específica
gcloud run services update-traffic vertice-mcp \
  --to-revisions REVISION_NAME=100 \
  --region=us-central1
```

---

## 💰 Custo Estimado

Com a configuração atual:
- **MCP Server**: ~$20-30/mês (2 GB RAM, 2 vCPU)
- **Backend**: ~$30-50/mês (1 GB RAM, 2 vCPU)
- **Frontend**: ~$10-20/mês (512 MB RAM, 1 vCPU)

**Total estimado**: $60-100/mês

**Para reduzir custos**:
- Reduzir max-instances durante desenvolvimento
- Usar --min-instances=0 (cold start)
- Configurar auto-scaling mais agressivo

---

## 🎯 Próximos Passos

1. ✅ Deploy completo funcionando
2. ⚙️ Configurar domínio customizado
3. 🔐 Adicionar autenticação (Clerk)
4. 📊 Configurar monitoring (Sentry + Cloud Monitoring)
5. 🚀 Setup CI/CD (GitHub Actions)
6. 🔄 Implementar blue-green deployments
7. 📝 Documentar APIs (OpenAPI/Swagger)

---

## ❓ Troubleshooting

### Build falha com "MODULE NOT FOUND"
```bash
# Verificar se requirements.txt está completo
cat prometheus/requirements.txt

# Rebuild com cache limpo
gcloud builds submit --no-cache ...
```

### Container não inicia (CrashLoopBackOff)
```bash
# Ver logs detalhados
gcloud run services logs read vertice-mcp --limit 100

# Testar localmente primeiro
docker run -p 3000:3000 vertice-mcp:test
docker logs <container-id>
```

### Timeout errors
```bash
# Aumentar timeout
gcloud run services update vertice-mcp --timeout 600s
```

---

**Preparado por**: Claude Sonnet 4.5
**Data**: 07 de Janeiro de 2026
**Account GCP**: juancs.d3v@gmail.com

**Soli Deo Gloria** 🙏

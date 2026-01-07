# 🚀 Guia de Deploy - Google Cloud Platform

**Vertice Chat Web App**
Deploy completo com Cloud Run, Cloud SQL, Memorystore e Secret Manager

---

## 📋 Pré-requisitos

- ✅ Conta GCP: `juancs.d3v@gmail.com` (com billing habilitado)
- ✅ `gcloud` CLI instalado ([Instalar aqui](https://cloud.google.com/sdk/docs/install))
- ✅ Docker instalado
- ✅ Repositório Git configurado

---

## 🔧 Configuração Inicial (Uma vez)

### 1. Autenticar no Google Cloud

```bash
# Login
gcloud auth login

# Configurar projeto
gcloud config set project YOUR_PROJECT_ID

# Habilitar APIs necessárias
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com
```

### 2. Criar Artifact Registry (Armazenamento de Imagens Docker)

```bash
# Criar repositório Docker
gcloud artifacts repositories create vertice-cloud \
  --repository-format=docker \
  --location=us-central1 \
  --description="Vertice Chat Web App containers"

# Configurar autenticação Docker
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 3. Criar Cloud SQL (PostgreSQL)

```bash
# Criar instância PostgreSQL
gcloud sql instances create vertice-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=CHANGE_THIS_PASSWORD \
  --backup-start-time=03:00

# Criar database
gcloud sql databases create vertice_prod \
  --instance=vertice-db

# Criar usuário
gcloud sql users create vertice_user \
  --instance=vertice-db \
  --password=SECURE_PASSWORD_HERE

# Obter connection string
gcloud sql instances describe vertice-db \
  --format='value(connectionName)'
# Resultado: PROJECT_ID:us-central1:vertice-db
```

**DATABASE_URL formato:**
```
postgresql+asyncpg://vertice_user:PASSWORD@/vertice_prod?host=/cloudsql/PROJECT_ID:us-central1:vertice-db
```

### 4. Criar Memorystore (Redis)

```bash
# Criar instância Redis
gcloud redis instances create vertice-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic

# Obter IP e porta
gcloud redis instances describe vertice-redis \
  --region=us-central1 \
  --format="value(host,port)"
# Resultado: 10.x.x.x  6379
```

**REDIS_URL formato:**
```
redis://10.x.x.x:6379
```

### 5. Configurar Secret Manager (Variáveis Sensíveis)

```bash
# Criar secrets
echo -n "sk-ant-..." | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
echo -n "sk-..." | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "sk_live_..." | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
echo -n "sk_test_..." | gcloud secrets create CLERK_SECRET_KEY --data-file=-
echo -n "pk_test_..." | gcloud secrets create CLERK_PUBLISHABLE_KEY --data-file=-

# DATABASE_URL
echo -n "postgresql+asyncpg://..." | gcloud secrets create DATABASE_URL --data-file=-

# REDIS_URL
echo -n "redis://10.x.x.x:6379" | gcloud secrets create REDIS_URL --data-file=-

# Dar permissão para Cloud Run acessar secrets
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Repetir para todos os secrets
for secret in OPENAI_API_KEY STRIPE_SECRET_KEY CLERK_SECRET_KEY CLERK_PUBLISHABLE_KEY DATABASE_URL REDIS_URL; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 6. Configurar Serverless VPC Access (Para Cloud SQL e Redis)

```bash
# Criar conector VPC
gcloud compute networks vpc-access connectors create vertice-connector \
  --region=us-central1 \
  --network=default \
  --range=10.8.0.0/28
```

---

## 🚢 Deploy Manual (Primeira Vez)

### Backend (FastAPI)

```bash
cd vertice-chat-webapp/backend

# Build imagem Docker
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/backend:latest .

# Push para Artifact Registry
docker push us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/backend:latest

# Deploy no Cloud Run
gcloud run deploy vertice-backend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars NODE_ENV=production \
  --set-secrets ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,CLERK_SECRET_KEY=CLERK_SECRET_KEY:latest \
  --vpc-connector vertice-connector \
  --vpc-egress all-traffic

# Obter URL do backend
gcloud run services describe vertice-backend --region us-central1 --format='value(status.url)'
# Exemplo: https://vertice-backend-xxxxxxx-uc.a.run.app
```

### Frontend (Next.js)

```bash
cd vertice-chat-webapp/frontend

# Atualizar API URL no next.config.ts (se necessário)
export NEXT_PUBLIC_API_URL=https://vertice-backend-xxxxxxx-uc.a.run.app

# Build imagem Docker
docker build \
  --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
  -t us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/frontend:latest .

# Push para Artifact Registry
docker push us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/frontend:latest

# Deploy no Cloud Run
gcloud run deploy vertice-frontend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/vertice-cloud/frontend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 20 \
  --timeout 60 \
  --concurrency 100 \
  --set-env-vars NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL,NODE_ENV=production \
  --set-secrets NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=CLERK_PUBLISHABLE_KEY:latest

# Obter URL do frontend
gcloud run services describe vertice-frontend --region us-central1 --format='value(status.url)'
# Exemplo: https://vertice-frontend-xxxxxxx-uc.a.run.app
```

---

## 🤖 Deploy Automático (CI/CD com Cloud Build)

### 1. Conectar GitHub ao Cloud Build

```bash
# Abrir console
gcloud builds triggers create github \
  --name="vertice-webapp-deploy" \
  --repo-name="vertice-code" \
  --repo-owner="JuanCS-Dev" \
  --branch-pattern="^main$" \
  --build-config="vertice-chat-webapp/cloudbuild.yaml" \
  --substitutions='_REGION=us-central1,_API_URL=https://vertice-backend-xxxxxxx-uc.a.run.app'
```

**Ou via Console:**
1. Ir para [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Clicar "Create Trigger"
3. Conectar repositório GitHub
4. Configurar:
   - **Nome**: `vertice-webapp-deploy`
   - **Branch**: `^main$`
   - **Build Configuration**: `cloudbuild.yaml`
   - **Substitution variables**:
     - `_REGION`: `us-central1`
     - `_API_URL`: `https://vertice-backend-xxxxxxx-uc.a.run.app`

### 2. Push para Deploy

```bash
git add .
git commit -m "feat: configure Cloud Run deployment"
git push origin main
```

Cloud Build vai:
1. ✅ Build backend Docker image
2. ✅ Build frontend Docker image
3. ✅ Push para Artifact Registry
4. ✅ Deploy backend no Cloud Run
5. ✅ Deploy frontend no Cloud Run

---

## 🌐 Configurar Domínio Customizado

### app.vertice-maximus.com → Frontend

```bash
# Mapear domínio
gcloud run domain-mappings create \
  --service vertice-frontend \
  --domain app.vertice-maximus.com \
  --region us-central1

# Cloud Run vai retornar registros DNS para adicionar:
# Tipo: CNAME
# Nome: app
# Valor: ghs.googlehosted.com
```

**Adicionar no DNS (Firebase ou outro provedor):**
```
app.vertice-maximus.com  →  CNAME  →  ghs.googlehosted.com
```

### api.vertice-maximus.com → Backend

```bash
gcloud run domain-mappings create \
  --service vertice-backend \
  --domain api.vertice-maximus.com \
  --region us-central1

# Adicionar CNAME no DNS
```

---

## 🔍 Monitoramento e Logs

### Ver logs em tempo real

```bash
# Backend
gcloud run services logs tail vertice-backend --region us-central1

# Frontend
gcloud run services logs tail vertice-frontend --region us-central1
```

### Ver métricas

```bash
# Abrir Cloud Console Monitoring
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

**Ou via Console:**
[Cloud Run Metrics](https://console.cloud.google.com/run)

---

## 💰 Estimativa de Custos (Uso Moderado)

| Serviço | Custo Mensal Estimado |
|---------|----------------------|
| Cloud Run (Frontend) | $5 - $20 |
| Cloud Run (Backend) | $10 - $40 |
| Cloud SQL (db-f1-micro) | $7 - $10 |
| Memorystore (1GB Basic) | $35 |
| Artifact Registry | $0.10/GB |
| Secret Manager | Grátis (primeiros 6 secrets) |
| **TOTAL** | **~$60 - $110/mês** |

*Free tier: 2M requests/mês grátis no Cloud Run*

---

## 🛠️ Comandos Úteis

### Atualizar secret

```bash
echo -n "new_value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Ver revisões de deploy

```bash
gcloud run revisions list --service vertice-backend --region us-central1
```

### Rollback para revisão anterior

```bash
gcloud run services update-traffic vertice-backend \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

### Escalar instâncias

```bash
gcloud run services update vertice-backend \
  --min-instances 1 \
  --max-instances 20 \
  --region us-central1
```

### Deletar tudo (cuidado!)

```bash
# Deletar serviços Cloud Run
gcloud run services delete vertice-frontend --region us-central1
gcloud run services delete vertice-backend --region us-central1

# Deletar Cloud SQL
gcloud sql instances delete vertice-db

# Deletar Redis
gcloud redis instances delete vertice-redis --region us-central1
```

---

## 📞 Suporte

**Dúvidas?**
- Documentação: https://cloud.google.com/run/docs
- Discord: [Vertice Code Community](#)
- Email: juan.brainfarma@gmail.com

---

✨ **Feito com amor e cuidado** ✨
*Para que cada desenvolvedor possa focar no que importa: criar.*

🙏 **Soli Deo Gloria** 🙏

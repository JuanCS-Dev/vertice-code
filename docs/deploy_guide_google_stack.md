# Guia de Deploy - Google Stack 2026 (Next.js AI + Streaming)

## Visão Geral

Este guia descreve como fazer deploy da Vertice-Chat WebApp usando Google Stack completo otimizado para 2026:
- **Firebase App Hosting**: Next.js 16 com AI streaming nativo
- **Cloud Run**: Backend Node.js com Vertex AI SDK
- **Vertex AI**: Streaming de código e tool calling
- **Firestore**: Database serverless
- **Secret Manager**: Gerenciamento seguro de credenciais

## Estratégia de Deploy 2026

Para suportar **AI streaming disruptivo**, usamos:
1. **Firebase App Hosting**: Server-side rendering + streaming UI
2. **Cloud Run + Node.js**: Backend com Vertex AI SDK nativo
3. **Server-Sent Events**: Streaming real-time de código
4. **CI/CD automático**: GitHub integration

## Pré-requisitos

- Conta Google Cloud com billing habilitado
- Firebase CLI instalado: `npm install -g firebase-tools`
- Google Cloud CLI instalado: `gcloud`
- Node.js 18+ instalado
- GitHub repository configurado

## 1. Setup do Firebase Project

### 1.1 Criar Firebase Project
```bash
# Login no Firebase
firebase login

# Criar projeto
firebase projects:create vertice-chat-webapp --project vertice-chat-webapp

# Selecionar projeto
firebase use vertice-chat-webapp
```

### 1.2 Habilitar Firebase App Hosting (CRÍTICO para 2026)
```bash
# App Hosting é OBRIGATÓRIO para Next.js 16 + AI streaming
firebase apphosting:backends:create us-central1 \
  --project vertice-chat-webapp \
  --build-command "npm run build" \
  --root-dir "." \
  --service-account firebase-adminsdk

# Firestore para database
firebase firestore:databases:create --project vertice-chat-webapp

# Authentication com Passkeys
firebase auth:config:set auth.providers.google.enabled true
firebase auth:config:set auth.providers.github.enabled true
firebase auth:config:set auth.providers.passkeys.enabled true
```

### 1.3 Configurar Environment Variables
```bash
# Para App Hosting
firebase apphosting:backends:configure us-central1 \
  --environment-variables NEXT_PUBLIC_API_URL="",FIREBASE_PROJECT_ID=vertice-chat-webapp
```

## 2. Setup Google Cloud

### 2.1 Configurar GCP Project
```bash
# Set project
gcloud config set project vertice-chat-webapp

# Habilitar APIs necessárias para 2026
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
```

### 2.2 Configurar Vertex AI
```bash
# Habilitar Vertex AI (crítico para AI streaming)
gcloud services enable aiplatform.googleapis.com

# Criar endpoint para modelos (opcional)
gcloud ai endpoints create \
  --display-name="Vertice AI Endpoint" \
  --region=us-central1
```

### 2.3 Configurar Secret Manager
```bash
# Service Account para Firebase Admin
gcloud iam service-accounts create firebase-admin \
  --display-name="Firebase Admin"

# Secrets para Firebase (e outros segredos do app)
gcloud secrets create firebase-service-account-key --data-file=firebase-admin-key.json
gcloud secrets create firebase-config --data-file=firebase-config.json
```

## 3. Build e Deploy Backend (Node.js + Vertex AI)

### 3.1 Preparar Backend Node.js
```bash
cd vertice-chat-webapp/backend

# package.json para Node.js backend
{
  "name": "vertice-backend",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@google-cloud/aiplatform": "^3.0.0",
    "@google-cloud/firestore": "^7.0.0",
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "@types/cors": "^2.8.0",
    "typescript": "^5.0.0"
  }
}
```

### 3.2 Dockerfile para Node.js
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 8080
CMD ["npm", "start"]
```

### 3.3 Build e Deploy Cloud Run
```bash
# Build com Cloud Build
gcloud builds submit --tag gcr.io/vertice-chat-webapp/backend .

# Deploy Cloud Run com Vertex AI
gcloud run deploy vertice-backend \
  --image gcr.io/vertice-chat-webapp/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-secrets FIREBASE_SA=firebase-service-account-key:latest \
  --set-env-vars NODE_ENV=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=vertice-chat-webapp
```

## 4. Build e Deploy Frontend (Firebase App Hosting)

### 4.1 Configurar Firebase App Hosting
```bash
cd vertice-chat-webapp

# firebase.json para App Hosting 2026
{
  "apphosting": {
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "rootDirectory": "frontend",
    "environmentVariables": {
      "NEXT_PUBLIC_API_URL": "",
      "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "vertice-chat-webapp"
    }
  }
}

# Instalar dependências
cd frontend
pnpm install
```

### 4.2 Deploy Firebase App Hosting
```bash
# Deploy automático com AI streaming support
firebase deploy --only apphosting

# Verificar status
firebase apphosting:backends:list
firebase apphosting:backends:describe us-central1
```

### 4.3 Configurar domínio customizado
```bash
# Adicionar domínio
firebase hosting:sites:add-domains vertice-chat-webapp app.vertice-maximus.com

# Verificar DNS
firebase apphosting:backends:set-traffic us-central1 \
  --set-traffic-target live
```

## 5. Integração Firebase App Hosting + Cloud Run

### 5.1 Configurar API Routes no App Hosting
```typescript
// frontend/app/api/chat/route.ts - Server Actions
import { VertexAI } from '@google-cloud/aiplatform'

export async function POST(request: Request) {
  const { messages } = await request.json()

  const vertexAI = new VertexAI({ project: 'vertice-chat-webapp' })
  const model = vertexAI.getGenerativeModel({ model: 'gemini-3-pro' })

  const result = await model.generateContentStream({
    contents: messages,
    generationConfig: { temperature: 0.7, maxOutputTokens: 2048 }
  })

  // Streaming response
  return new Response(
    new ReadableStream({
      async start(controller) {
        for await (const chunk of result.stream) {
          controller.enqueue(new TextEncoder().encode(chunk.text()))
        }
        controller.close()
      }
    }),
    {
      headers: {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache'
      }
    }
  )
}
```

### 5.2 CORS no Backend Node.js
```typescript
// backend/src/index.ts
import express from 'express'
import cors from 'cors'

const app = express()

app.use(cors({
  origin: [
    'https://vertice-chat-webapp.web.app',
    'https://us-central1-vertice-chat-webapp.web.app'
  ],
  credentials: true
}))
```

## 6. Configuração de Domínio Customizado

### 6.1 Firebase Hosting
```bash
# Adicionar domínio
firebase hosting:sites:add-domains vertice-chat-webapp app.vertice-maximus.com

# Verificar DNS
firebase hosting:sites:describe vertice-chat-webapp
```

### 6.2 Cloud Run Domain Mapping
```bash
# Map domain to Cloud Run
gcloud run domain-mappings create \
  --service vertice-backend \
  --domain api.vertice-maximus.com \
  --region us-central1
```

## 7. Monitoramento 2026

### 7.1 Firebase App Hosting Monitoring
```bash
# Performance e errors
firebase apphosting:backends:describe us-central1

# Logs de build/deploy
firebase apphosting:backends:list-builds us-central1
```

### 7.2 Cloud Run + Vertex AI Monitoring
```bash
# Logs do Cloud Run
gcloud logging read "resource.type=cloud_run_revision" --limit=20

# Vertex AI usage
gcloud ai models list --region=us-central1

# Performance metrics
gcloud monitoring dashboards create \
  --config-from-file=dashboard.json \
  --project=vertice-chat-webapp
```

### 7.3 AI Streaming Metrics
```bash
# Monitorar latência de AI responses
gcloud logging read "jsonPayload.model:gemini" --limit=10

# Error reporting para AI failures
gcloud services enable clouderrorreporting.googleapis.com
```

## 6. CI/CD Automático 2026

### 6.1 Firebase App Hosting Auto-deploy
```bash
# Conectar GitHub para auto-deploy
firebase apphosting:backends:set-deployment us-central1 \
  --github-repo=github.com/[user]/vertice-chat-webapp \
  --github-branch=main \
  --build-config=firebase.json
```

### 6.2 Cloud Build para Backend
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/npm'
  args: ['install']
  dir: 'backend'

- name: 'gcr.io/cloud-builders/npm'
  args: ['run', 'build']
  dir: 'backend'

- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/backend:$COMMIT_SHA', '.']
  dir: 'backend'

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
  - run
  - deploy
  - vertice-backend
  - --image=gcr.io/$PROJECT_ID/backend:$COMMIT_SHA
  - --region=us-central1
  - --platform=managed
  - --allow-unauthenticated
  - --port=8080
```

### 6.3 GitHub Triggers
```bash
# Backend trigger
gcloud builds triggers create github \
  --name=backend-trigger \
  --repository=github.com/[user]/vertice-chat-webapp \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml

# Frontend trigger (Firebase App Hosting)
firebase apphosting:backends:set-deployment us-central1 \
  --source=github \
  --github-repo=github.com/[user]/vertice-chat-webapp
```

## 9. Segurança

### 9.1 Secret Management
```bash
# Rotacionar secrets
gcloud secrets versions add firebase-service-account-key --data-file=new-key.json

# Atualizar Cloud Run
gcloud run services update vertice-backend \
  --set-secrets FIREBASE_SERVICE_ACCOUNT_KEY=firebase-service-account-key:latest
```

### 9.2 Firewall Rules
```bash
# VPC Firewall (se necessário)
gcloud compute firewall-rules create allow-cloud-run \
  --allow tcp:80,tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags cloud-run
```

## 8. Troubleshooting 2026

### Problemas Comuns com AI Streaming

**Erro: Streaming não funciona**
```bash
# Verificar Vertex AI quota
gcloud ai models describe gemini-3-pro --region=us-central1

# Check App Hosting logs
firebase apphosting:backends:list-builds us-central1
```

**Erro: Firebase App Hosting build falha**
```bash
# Verificar build logs
firebase apphosting:backends:describe us-central1

# Check Node.js version compatibility
node --version  # Deve ser 18+
```

**Erro: Vertex AI authentication (padrão Google: ADC/IAM, sem API key)**
```bash
# O Vertex AI usa Application Default Credentials (ADC):
# https://cloud.google.com/docs/authentication/provide-credentials-adc
#
# Em Cloud Run, a identidade é o Service Account do serviço:
# https://cloud.google.com/run/docs/securing/service-identity
#
# Garanta permissões IAM para Vertex AI:
# https://cloud.google.com/vertex-ai/docs/general/access-control

# Verificar qual Service Account o Cloud Run está usando:
gcloud run services describe vertice-backend --region us-central1 \
  --format='value(spec.template.spec.serviceAccountName)'

# (Se necessário) conceder permissão mínima ao SA:
PROJECT_ID="vertice-ai"
SA_EMAIL="239800439060-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"
```

**Erro: Cold starts afetando streaming**
```bash
# Configurar min instances
gcloud run services update vertice-backend \
  --min-instances 1 \
  --region us-central1 \
  --cpu 2 \
  --memory 2Gi
```

**Erro: CORS no streaming**
```bash
# Verificar CORS headers no backend
curl -H "Origin: https://us-central1-vertice-chat-webapp.web.app" \
  -v https://vertice-backend-abc123-uc.a.run.app/api/chat
```

## URLs Finais 2026

- **Frontend (App Hosting)**: https://us-central1-vertice-chat-webapp.web.app
- **Backend API (Cloud Run)**: https://vertice-backend-[ID]-uc.a.run.app
- **Firebase Console**: https://console.firebase.google.com/project/vertice-chat-webapp
- **Vertex AI Studio**: https://console.cloud.google.com/vertex-ai/studio
- **Cloud Logging**: https://console.cloud.google.com/logs

## Performance Esperada 2026

- **Frontend Load**: <2s (Firebase App Hosting)
- **AI Response Start**: <500ms (Vertex AI)
- **Streaming Latency**: <100ms por chunk
- **Cold Start**: <3s (Cloud Run optimized)

---

*Última atualização: Janeiro 2026 | Google Cloud Platform + Firebase + AI Streaming*

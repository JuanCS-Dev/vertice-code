# 🚀 GUIA REAL: DEPLOY GCP VERTICE WEBAPP (JANEIRO 2026)

## 📋 STATUS AUDITADO (13/01/2026)
✅ **Projeto GCP**: `vertice-ai` (US Central)
✅ **Stack**: Next.js 16.1.1 + Firebase Web Frameworks (Gen 2)
✅ **Hosting**: `vertice-ai.web.app` (Single Region: us-central1)
⚠️ **Multi-Region**: Configurado no JSON mas inativo na infraestrutura (EU/Asia targets offline).
✅ **Build System**: `pnpm` (Lockfile detectado)

## 🎯 SEQUÊNCIA DE DEPLOY (5 Minutos)

### PRÉ-REQUISITOS
Certifique-se de estar autenticado:
```bash
gcloud auth login
firebase login
```

### PASSO 1: VERIFICAÇÃO DE INTEGRIDADE (BUILD)
Antes de enviar, garantimos que o Type Safety está 100%.
```bash
cd vertice-chat-webapp/frontend
pnpm install
pnpm build
```
*Nota: Se houver erros de TypeScript, o deploy falhará. Corrija-os antes de prosseguir.*

### PASSO 2: CONFIGURAÇÃO DE TARGET (Se necessário)
Para garantir que o deploy vá para o site correto:
```bash
# Na raiz do projeto
firebase target:apply hosting vertice-ai vertice-ai
```

### PASSO 3: DEPLOY (WEBAPP ONLY)
Devido à ausência dos sites regionais (EU/Asia), fazemos deploy focado apenas na produção US:
```bash
firebase deploy --only hosting:vertice-ai
```

## 📊 INFRAESTRUTURA ATUAL

### 🔥 Frontend (Next.js 16)
- **Runtime**: Cloud Run (via Firebase Frameworks)
- **Região**: us-central1
- **SSR/API**: Habilitado (Gen 2 Cloud Functions)
- **Middleware**: Proxy mode (Next.js 16 standard)

### ☸️ Backend / Outros (Roadmap)
- *GKE Autopilot e Vertex AI não estão integrados neste ciclo de deploy do frontend.*
- *Multi-region hosting requer criação manual dos sites `vertice-ai-eu` e `vertice-ai-asia`.*

## ⚠️ TROUBLESHOOTING

### Erro: "Deploy target not configured"
Se tentar `firebase deploy --only hosting` sem especificar o target, ele tentará EU e Asia.
**Solução**: Use `--only hosting:vertice-ai`.

### Erro: "Type Error in chat-interface.tsx"
A versão do AI SDK v6 é estrita.
**Solução**: Propriedades como `api`, `headers` e `streamProtocol` foram removidas ou comentadas no `useChat` hook pois são defaults ou manuseadas dinamicamente.

## 🎉 URL DE PRODUÇÃO
👉 **https://vertice-ai.web.app**

---
*Documento atualizado automaticamente pelo Agente Gemini em 13/01/2026.*

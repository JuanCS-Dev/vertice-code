# Firebase App Hosting / Next.js SSR — Safe Minimum (2026-01-26)

Data: **2026-01-26**
Projeto: **`vertice-ai`**

Objetivo: manter o site no ar e evitar mudanças destrutivas enquanto o frontend passa por reestruturação.

## O que foi confirmado

- `ssrverticeai` é **Cloud Functions (Gen2)** gerado pelo **Firebase CLI** para **SSR do Next.js** (não é backend legado).
- `vertice-ai.web.app` e `vertice-ai.firebaseapp.com` estão servindo HTML Next.js compatível com `ssrverticeai`.
- O recurso está com **drift de imagem** (Artifact Registry): `Ready=False` no Cloud Run subjacente, porém ainda responde
  `200` porque o tráfego permanece na última revisão pronta.

Referências oficiais:
- Firebase App Hosting: https://firebase.google.com/docs/app-hosting
- Cloud Functions (2nd gen): https://cloud.google.com/functions/docs/2nd-gen/overview
- Cloud Run revisions/rollouts: https://cloud.google.com/run/docs/deploying

## Safe minimum (agora)

1) **Não deletar `ssrverticeai`**
- Risco alto de derrubar `vertice-ai.web.app`.

2) **Não tentar “consertar por Cloud Run update”**
- Como a imagem está ausente, qualquer update pode falhar por validação do deploy.

3) **Inventariar e registrar evidências (read-only)**
```bash
export GOOGLE_CLOUD_PROJECT="vertice-ai"
./tools/gcloud/inventory_cloud_functions_v2.sh
./tools/gcloud/inventory_cloud_run.sh
```

## Quando você terminar a reestruturação do frontend (redeploy recomendado)

O fix correto para o drift é um **redeploy do App Hosting** (o deploy vai reconstruir e publicar uma imagem válida).

Checklist mínimo pós-redeploy:
- `vertice-ai.web.app` responde `200` e carrega a UI nova.
- `gcloud run services describe ssrverticeai --region us-central1` volta a `Ready=True` (ou o equivalente no inventário).
- Logs sem `Image not found` e sem 5xx.

# Google Cloud — Análise do `ssrverticeai` (legado vs necessário) (2026-01-26)

Data: **2026-01-26**
Projeto: **`vertice-ai`**
Região: **`us-central1`**

## Conclusão

`ssrverticeai` **não parece legado**: ele é um **Cloud Functions Gen2** (runtime **Node.js**) criado pelo **Firebase CLI**
para servir **Next.js (SSR)** e hoje está, na prática, atendendo o tráfego do site `vertice-ai.web.app`.

Portanto, **não recomendo deletar** sem antes trocar oficialmente o frontend para outra rota (ex.: Cloud Run
`vertice-frontend`) e validar o cutover.

---

## Evidências (GCP)

1) O recurso é um Cloud Functions Gen2, com labels do Firebase:
- `deployment-tool: cli-firebase`
- `firebase-functions-codebase: firebase-frameworks-vertice-ai`
- `__FIREBASE_FRAMEWORKS_ENTRY__: next.js`

Fonte: `gcloud functions describe ssrverticeai --v2 --region us-central1 --project vertice-ai --format=json`

2) O endpoint do Firebase Hosting e o endpoint do `ssrverticeai` retornam HTML idêntico (indicando mesma origem SSR):
- `https://vertice-ai.web.app/` → `200` + `x-powered-by: Next.js`
- `https://ssrverticeai-nrpngfmr6a-uc.a.run.app/` → `200` + `x-powered-by: Next.js`

3) O serviço Cloud Run `ssrverticeai` está **`Ready=False`** por drift de imagem (Artifact Registry), mas ainda responde
`200` pois o tráfego continua preso na última revisão pronta.
- Ver inventário: `docs/google/_inventory/cloud_run_vertice-ai_summary_2026-01-26T16-27-43Z.md`

---

## Evidências (repo local)

O repositório está configurado para **Firebase App Hosting** apontando para o frontend Next.js:
- `firebase.json`:
  - `apphosting.rootDirectory = "vertice-chat-webapp/frontend"`

Isso indica que, **localmente**, o caminho oficial do frontend ainda é Firebase App Hosting (não apenas Cloud Run).

---

## Ação recomendada (segura)

1) **Decidir qual é o “frontend oficial”**
- Opção A (Google padrão para Next.js aqui): manter Firebase App Hosting → então precisamos **redeploy** para corrigir o
  drift da imagem do `ssrverticeai`.
- Opção B: migrar para Cloud Run `vertice-frontend` como origem do tráfego → então faremos o cutover (Hosting/DNS) e só
  depois desativamos `ssrverticeai`.

2) **Não deletar agora**
- Deletar `ssrverticeai` agora provavelmente derruba `vertice-ai.web.app`.

# Google Cloud ADC Migration + Backend Recovery Report (2026‑01‑26)

**Objetivo:** remover dependência de API key/Secret (`vertex-ai-key`) e colocar o `vertice-backend` em
**padrão Google (ADC/IAM)**, além de recuperar o serviço (container port).

**Projeto:** `vertice-ai`
**Região:** `us-central1`
**Data (UTC):** 2026‑01‑26

---

## 1) Resultado final

- Cloud Run `vertice-backend`: **Ready=True** (recuperado)
- Autenticação Vertex AI: **ADC/IAM (Service Account)** — sem `VERTEX_AI_KEY`
- `vertex-ai-key`: permanece sem versões, mas **não é mais bloqueador** do `vertice-backend`

---

## 2) Root cause (por que o serviço caiu)

1) O serviço `vertice-backend` referenciava um secret inexistente (`vertex-ai-key:latest` sem versões) e por isso
   falhava em readiness.
2) Após remover o secret, o rollout revelou outro problema: o Cloud Run estava configurado com **container port 8000**
   (variável `PORT=8000`), mas a imagem do backend escuta em **8080** → erro `HealthCheckContainerError`.

Doc oficial (Cloud Run troubleshooting): https://cloud.google.com/run/docs/troubleshooting#container-failed-to-start

---

## 3) Mudanças aplicadas (Cloud Run)

### 3.1 Remoção do secret de API key (migração para ADC)

```bash
gcloud run services update vertice-backend \
  --region=us-central1 \
  --remove-secrets=VERTEX_AI_KEY
```

### 3.2 Correção do container port

```bash
gcloud run services update vertice-backend \
  --region=us-central1 \
  --port=8080
```

---

## 4) Validação (online)

- `gcloud run services describe vertice-backend --region us-central1`:
  - `status.conditions[0].type=Ready`
  - `status.conditions[0].status=True`
- `gcloud run services describe vertice-agent-gateway --region us-central1`: `Ready=True`
- `gcloud run services describe vertice-mcp --region us-central1`: `Ready=True`
- Endpoint público:
  - `GET /health` → **200 OK**
  - `GET /` → **401** (esperado se o app exige autenticação)

---

## 5) Padrão Google 2026: ADC/IAM (referências oficiais)

- ADC (Application Default Credentials): https://cloud.google.com/docs/authentication/provide-credentials-adc
- Service identity no Cloud Run: https://cloud.google.com/run/docs/securing/service-identity
- Vertex AI IAM / access control: https://cloud.google.com/vertex-ai/docs/general/access-control

Nota prática:
- O `vertice-backend` está usando o Service Account `239800439060-compute@developer.gserviceaccount.com` e já possui
  `roles/editor` no projeto, então tem permissões suficientes para Vertex AI nesta fase.

---

## 6) Mudanças no repositório (docs/scripts)

Para alinhar o monorepo ao padrão ADC/IAM e evitar drift:
- Removido `--set-secrets VERTEX_AI_KEY=vertex-ai-key:latest` do script `vertice-chat-webapp/deploy-enterprise.sh`.
- Atualizados docs para não prescrever `vertex-ai-key` como requisito de autenticação Vertex:
  - `docs/deploy_guide_google_stack.md`
  - `docs/WEBAPP_DEPLOY_PLAN_2026.md`

---

## 7) Nota de segurança (segredos)

- Não registrar/commitar API keys no repo (nem em `.env`).
- Se ainda precisar de API key em cenários específicos, armazenar no Secret Manager e restringir IAM ao mínimo.

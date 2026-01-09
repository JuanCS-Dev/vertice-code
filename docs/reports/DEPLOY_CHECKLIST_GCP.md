# 🚀 Relatório de Preparação para Deploy (Google Stack)

**Data Alvo:** 08/01/2026
**Autor:** Vertice-MAXIMUS Agent
**Status:** PRONTO PARA DEPLOY (Aguardando Infraestrutura)

Este documento detalha **exatamente** o que você precisa verificar e configurar no console do Google Cloud (GCP) antes de rodar o comando final de deploy. Como decidimos usar a **Stack Google Pura**, não podemos usar mocks em produção.

---

## 1. ✅ Infraestrutura Crítica (Google Stack)

Você precisa garantir que estes recursos existam no projeto GCP `juancs-dev` (ou o ID correto do projeto).

### A. Banco de Dados (Cloud SQL)
*   **Recurso:** Cloud SQL para PostgreSQL (versão 15 ou superior).
*   **O que verificar:**
    1.  Crie a instância se não existir: `gcloud sql instances create vertice-db --database-version=POSTGRES_15 --cpu=1 --memory=4Gi --region=us-central1`.
    2.  Crie o banco: `gcloud sql databases create vertice_prod --instance=vertice-db`.
    3.  Crie o usuário: `gcloud sql users create vertice_user --instance=vertice-db --password=SUA_SENHA_FORTE`.
    4.  **ANOTE O "CONNECTION NAME":** Algo como `project-id:us-central1:vertice-db`.

### B. Cache (Cloud Memorystore)
*   **Recurso:** Cloud Memorystore for Redis.
*   **O que verificar:**
    1.  Crie a instância: `gcloud redis instances create vertice-redis --size=1 --region=us-central1`.
    2.  **ANOTE O IP:** O Cloud Run precisará deste IP para conectar.
    3.  **VPC Connector:** Para que o Cloud Run (Serverless) fale com o Redis (Privado), você precisa configurar o "Direct VPC Egress" ou um "VPC Connector".
        *   *Recomendação:* Use **Direct VPC Egress** no deploy do Cloud Run se disponível, ou crie um conector: `gcloud compute networks vpc-access connectors create vertice-vpc-connector --region=us-central1 --range=10.8.0.0/28`.

### C. Armazenamento de Imagens (Artifact Registry)
*   **O que verificar:**
    *   Garanta que o repositório existe:
        ```bash
        gcloud artifacts repositories create vertice-cloud \
            --repository-format=docker \
            --location=us-central1 \
            --description="Vertice Containers"
        ```

---

## 2. 🔐 Segredos & Configuração (Secret Manager)

O deploy **FALHARÁ** se estes secrets/variáveis não estiverem configurados corretamente.

| Nome do Secret / Var | Tipo | Notas |
| :--- | :--- | :--- |
| `DATABASE_URL` | **Secret** | **Formato:** `postgresql+asyncpg://USER:PASS@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE` <br> *Atenção:* Use o caminho do socket `/cloudsql/...` |
| `REDIS_URL` | **Secret** | **Formato:** `redis://IP_DO_MEMORYSTORE:6379` |
| `FIREBASE_PROJECT_ID` | Env Var | O ID do projeto Firebase (geralmente igual ao do GCP). Necessário para o Backend. |

### 🌍 Frontend Firebase Config (Build Args)
Estas variáveis precisam ser passadas para o **Cloud Build** via substituições (`_FIREBASE_API_KEY`, etc.) ou hardcoded no `cloudbuild.yaml` (menos seguro para API Key).

*   `NEXT_PUBLIC_FIREBASE_API_KEY`
*   `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
*   `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
*   `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
*   `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
*   `NEXT_PUBLIC_FIREBASE_APP_ID`

**Como criar os secrets de Backend:**
```bash
echo -n "postgresql+asyncpg://..." | gcloud secrets create DATABASE_URL --data-file=-
echo -n "redis://..." | gcloud secrets create REDIS_URL --data-file=-
```

---

## 3. 🧠 Inteligência (Gemini API)

Como removemos a Anthropic, seu sistema depende 100% do Vertex AI (Gemini).

*   **API Enable:** Garanta que a API `aiplatform.googleapis.com` (Vertex AI) está habilitada.
*   **Quotas:** Verifique se você tem cota para `gemini-1.5-flash` e `gemini-1.5-pro` na região `us-central1`.
*   **Permissões:** A "Service Account" padrão do Cloud Run (`Compute Engine default service account`) precisa da role **Vertex AI User**.
    ```bash
    gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
        --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
        --role="roles/aiplatform.user"
    ```

---

## 4. 🚀 O Comando Final

Depois de garantir os itens acima (especialmente o banco de dados e os secrets), rode:

```bash
# 1. Login
gcloud auth login

# 2. Set Project
gcloud config set project SEU_PROJECT_ID

# 3. Disparar o Build & Deploy
gcloud builds submit --config cloudbuild.yaml .
```

---

## 📝 Notas Finais do Auditor

1.  **VPC Network:** Se o deploy do backend falhar com "Connection timed out" ao tentar conectar no Redis, 99% de chance de ser falta de configuração de VPC Egress no Cloud Run.
2.  **Migrations:** Este deploy **NÃO** roda as migrações do banco (Alembic) automaticamente.
    *   *Pós-Deploy:* Você precisará conectar no banco (via Cloud SQL Proxy) e rodar `alembic upgrade head` localmente apontando para o banco de produção, ou criar um "Job" do Cloud Run para isso.
3.  **Domínios:** Após o deploy, configure o `CNAME` do seu domínio (`app.vertice.ai`) para apontar para a URL que o Cloud Run gerar.

**Bom deploy amanhã, chefe. A casa está em ordem.**

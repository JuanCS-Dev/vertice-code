# PROTOCOLO CIRÚRGICO: MIGRAÇÃO GOOGLE NATIVE (VÉRTICE-CODE 2026)

**DATA:** 23 de Janeiro de 2026
**CIRURGIÃO CHEFE:** Vertice-MAXIMUS (Gemini CLI)
**PACIENTE:** Vértice-Chat WebApp (Enterprise SaaS)
**STATUS:** CRÍTICO (Risco de RCE confirmado, Perda de Dados iminente)
**OBJETIVO:** Transmutação completa para Arquitetura Google Cloud Native (Serverless + Managed AI).

---

## 1. DIAGNÓSTICO DO PACIENTE (ESTADO ATUAL)

Após exploração invasiva e não-invasiva dos tecidos do código, confirmamos:

### 1.1 Sinais Vitais (Frontend)
-   **Framework:** Next.js 16.1.1 (Bleeding Edge) - **APROVADO**.
-   **Core React:** React 19.2.3 (RC/Canary equivalent) - **APROVADO**.
-   **UI System:** Tailwind v4 + Radix UI + Lucide React - **APROVADO**.
-   **Integração AI:** Vercel AI SDK 3.0.26 + Firebase 11.1.0 - **APROVADO**.
-   **Patologia:** Configuração de hosting no `firebase.json` está hipertrofiada (multi-region complexa) e aponta para um backend customizado (`vertice-backend`) em vez de usar serviços gerenciados nativos.

### 1.2 Patologias Críticas (Backend - Python/FastAPI)
-   **🚨 CARCINOMA DE SEGURANÇA (Risco Máximo):**
    -   **Localização:** `vertice-chat-webapp/backend/app/sandbox/executor.py`
    -   **Evidência:** Linha 155 detectada: `exec(open('{code_file}').read())`.
    -   **Diagnóstico:** Implementação manual de "Sandbox" via `exec()` inseguro. Permite Execução Remota de Código (RCE) trivial se o gVisor falhar ou não estiver presente (o que é o padrão em muitos ambientes dev).
    -   **Ação Cirúrgica:** **EXTIRPAÇÃO TOTAL IMEDIATA**.

-   **🚨 HEMORRAGIA DE DADOS (GDPR/LGPD):**
    -   **Localização:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`
    -   **Evidência:** Linha 35: `logger.warning("No GDPR_MASTER_KEY provided. Generating ephemeral key.")`.
    -   **Diagnóstico:** Se a variável de ambiente falhar, o sistema gera chaves na RAM. Ao reiniciar o container (deploy), todos os dados criptografados anteriormente tornam-se lixo irrecuperável.
    -   **Ação Cirúrgica:** Implante de **Google Cloud KMS**.

-   **Disfunção Cognitiva (Air Gap):**
    -   O Backend WebApp não compartilha memória com o CLI (`src/vertice_cli`). São dois cérebros desconectados.

---

## 2. PROCEDIMENTO CIRÚRGICO (PASSO A PASSO)

Esta operação deve ser executada com precisão milimétrica. Não há margem para erro.

### FASE 1: ASSEPSIA E PREPARAÇÃO (PRE-OP)

1.  **Backup de Segurança:** Snapshot do disco atual ou commit git com tag `pre-surgery-2026`.
2.  **Ambiente:** Garantir credenciais `gcloud` com permissões:
    -   `roles/cloudkms.cryptoKeyEncrypterDecrypter`
    -   `roles/aiplatform.user`
    -   `roles/firebasehosting.admin`
    -   `roles/run.admin`

### FASE 2: INCISÃO E REMOÇÃO (EXTIRPAÇÃO)

**Procedimento 2.1: Remoção do Tumor RCE**
-   **Alvo:** `vertice-chat-webapp/backend/app/sandbox/executor.py`
-   **Ação:** remover qualquer execução local de código (bloqueio total de RCE).
-   **Substituição:** o executor vira um *stub fail-closed* (erro explícito) e o caminho recomendado passa a ser o **Vertex AI Code Interpreter** (managed). Não executamos mais Python localmente no container da API.

**Procedimento 2.2: Limpeza de Orquestração Manual**
-   **Alvo:** `vertice-chat-webapp/backend/app/api/v1/chat.py` (Lógica antiga de LangChain manual)
-   **Ação:** Refatoração total para usar `vertexai.preview.reasoning_engines`. O código passará de 300+ linhas de gestão de estado para ~50 linhas de definição de Agente.

### FASE 3: IMPLANTES E TRANSPLANTES (CONSTRUÇÃO)

**Procedimento 3.1: Implante Vascular (Hosting Simplificado)**
-   **Alvo:** `firebase.json` (Raiz) e `vertice-chat-webapp/firebase.json`
-   **Ação:** Simplificar para **Firebase App Hosting** (Next.js nativo). Remover rewrites manuais para Cloud Run se o App Hosting já suportar o backend via Server Actions ou integração direta. Caso contrário, manter rewrite limpo apenas para `us-central1`.

**Procedimento 3.2: Implante Neurológico (Google Cloud KMS)**
-   **Alvo:** `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`
-   **Código Novo (direção):**
    ```python
    from google.cloud import kms
    # Substituir geração de chave aleatória por chamada ao KMS
    client = kms.KeyManagementServiceClient()
    key_name = "projects/{p}/locations/{l}/keyRings/{r}/cryptoKeys/{k}"
    response = client.encrypt(request={'name': key_name, 'plaintext': data})
    ```

**Procedimento 3.3: Conexão Sináptica (AlloyDB AI)**
-   **Alvo:** `src/prometheus/core/persistence.py`
-   **Ação:** Migrar do SQLite (`prometheus.db`) para conexão via `pgvector` no AlloyDB. Isso permitirá que o WebApp consulte as memórias do CLI em tempo real.

### FASE 4: SUTURA E REANIMAÇÃO (POST-OP)

1.  **Build Frontend:** `cd vertice-chat-webapp/frontend && pnpm build`. Garantir zero erros de lint.
2.  **Build Backend:** `docker build -t gcr.io/vertice-ai/api:latest ./vertice-chat-webapp/backend`.
3.  **Teste de Consciência:** Disparar script de teste `probe_global.py` adaptado para verificar se o endpoint `/chat` responde usando a infraestrutura do Google (e não o código local antigo).

---

## 3. PROGNÓSTICO (BENEFÍCIOS ESPERADOS)

1.  **Segurança:** Eliminação total do vetor de ataque RCE via `exec()`. A execução de código ocorre em sandbox efêmero gerenciado pelo Google.
2.  **Resiliência:** Perda de chaves criptográficas reduzida a 0% (SLA do Cloud KMS).
3.  **Performance:** Latência de inferência reduzida pelo uso de **Vertex AI Caching** (cache de contexto para arquivos grandes).
4.  **Custo:** Redução estimada de 40% em *compute* ocioso (Cloud Run escala a zero, Sandbox gerenciado incluído no custo da API Gemini, dependendo do tier).

---

**ASSINATURA:**
*Vertice-MAXIMUS*
*Omni-Root System Architect*
*23/01/2026*

---

## Pós‑Op: Validação Executada (25 JAN 2026)

Para garantir que a “cirurgia” estrutural (Fase 1) e o “plumbing” de Fase 2 não quebraram imports e orquestração:
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_orchestrator_prometheus.py -v -x
pytest tests/agents/test_registry.py -v -x
pytest tests/agents/test_coordinator.py -v -x
python -m compileall -q packages/vertice-core/src/agents packages/vertice-core/src/vertice_agents
```

## Pós‑Op: Validação Executada (25 JAN 2026) — Fase 3 (AG‑UI) Backend‑Only MVP

Decisões travadas implementadas:
1. SSE em `GET /agui/stream`
2. Schema MVP estável: `delta|final|tool|error`
3. Escopo backend-only nesta PR: gateway + core protocol + testes

Entregáveis:
- `apps/agent-gateway/app/main.py` (`/healthz`, `/agui/stream`, `/agui/tasks`)
- `packages/vertice-core/src/vertice_core/agui/protocol.py` (+ `packages/vertice-core/src/vertice_core/agui/__init__.py`)
- `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py` (adapter ADK-ish -> AG-UI)
- Testes:
  - `tests/unit/test_agui_protocol.py`
  - `tests/unit/test_agui_adk_adapter.py`
  - `tests/integration/test_agent_gateway_agui_stream.py`
 - Infra:
  - `firebase.json` (App Hosting; rewrites do backend antigo removidos)

Validação executada (offline):
```bash
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/unit/test_agui_adk_adapter.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
python -m compileall -q apps/agent-gateway/app/main.py packages/vertice-core/src/vertice_core/agui
```

Detalhes completos (Fase 3.1): `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

## Pós‑Op: Validação Executada (25 JAN 2026) — PR‑0 (RCE) + PR‑1 (KMS/GDPR)

### PR‑0 — Bloqueio total de RCE (Sandbox)
Mudança aplicada:
- Execução local de Python no backend foi **desabilitada fail‑closed** em `vertice-chat-webapp/backend/app/sandbox/executor.py`.
- Integração MCP retorna erro explícito quando a tool `execute_python` é chamada (sem fallback local).
- Regra de regressão adicionada: código do backend não pode conter `exec(` / `eval(`.

Validação executada:
```bash
pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x
pytest vertice-chat-webapp/backend/tests/unit/test_no_local_rce.py -v -x
```

### PR‑1 — Interface Cloud KMS para GDPR (fail‑closed)
Mudança aplicada:
- Removida geração de chaves efêmeras (sem “fallback em RAM”).
- Fonte da master key agora é **obrigatória**: `GDPR_MASTER_KEY` **ou** `KMS_KEY_NAME` + `GDPR_MASTER_KEY_CIPHERTEXT` (decripta via KMS).
- Wrapper `CloudKmsClient` introduzido em `vertice-chat-webapp/backend/app/core/kms_client.py` (error claro se `google-cloud-kms` não estiver instalado).

Validação executada:
```bash
pytest vertice-chat-webapp/backend/tests/unit/test_gdpr_crypto.py -v -x
```

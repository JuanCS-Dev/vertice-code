# Blueprint de Implementação: Vértice-Code AI SaaS (ESPECIFICAÇÃO TÉCNICA 2026)

**Data**: 22 Janeiro 2026  
**Status**: **MASTER PLAN PARA TRANSIÇÃO GOOGLE NATIVE**  
**Analista**: Vertice-MAXIMUS (Omni-Root)  
**Objetivo**: Documento autocontido para planejamento de implementação sem necessidade de acesso prévio ao codebase.

---

## 1. ESTRUTURA DO CODEBASE (O MAPA DO TERRENO)

Para o planejamento, considere as três árvores principais de diretórios:

1.  **`src/vertice_cli/`**: O "Cérebro Real". Contém a lógica de orquestração refinada, observabilidade OpenTelemetry e o motor de agentes.
2.  **`src/prometheus/`**: A "Inteligência L4". Contém a memória MIRIX (SQLite), o servidor MCP e a lógica de auto-evolução.
3.  **`vertice-chat-webapp/`**: A "Casca SaaS". É o foco deste saneamento.
    -   `backend/app/api/v1/`: Endpoints FastAPI do Web App.
    -   `backend/app/core/`: Reimplementações (stubs) de segurança, banco e telemetria.
    -   `frontend/`: Interface Next.js 16 / React 19.

---

## 2. DIAGNÓSTICO DE RISCOS & CAMINHOS CRÍTICOS (ONDE ATUAR)

### 2.1 🚨 Risco de Execução Remota (RCE)
-   **Arquivo**: `vertice-chat-webapp/backend/app/sandbox/executor.py`
-   **Problema**: Uso de `exec(open(code_file).read())` como fallback. Filtros de string inúteis contra ataques de ofuscação.
-   **Ação**: DELETAR o arquivo e substituir por **Vertex AI Extensions (Code Interpreter)**.

### 2.2 🚨 Risco de Perda de Dados (GDPR)
-   **Arquivo**: `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`
-   **Problema**: Geração de chaves na memória (RAM) se `GDPR_MASTER_KEY` estiver ausente. Dados criptografados hoje serão ilegíveis amanhã após reinicialização do container.
-   **Ação**: Migrar gestão de chaves para **Google Cloud KMS (HSM managed)**.

### 2.3 🚨 Esquizofrenia de Memória (Air Gap)
-   **Caminho Local**: `src/prometheus/core/persistence.py` (Usa `.prometheus/prometheus.db`)
-   **Problema**: O Web App não enxerga o que o CLI aprende. O "agente evolutivo" é isolado por dispositivo.
-   **Ação**: Migrar a persistência do SQLite local para o **Vertex AI Agent Engine - Memory Bank**.

---

## 3. ESTRATÉGIA DE SUBSTITUIÇÃO: GOOGLE STACK 2026

O plano de implementação deve seguir a lógica de **"Deletar & Conectar"**.

### 3.1 Orquestração Gerenciada (Vertex AI Agent Engine)
-   **Serviço**: `reasoning_engines` do Vertex AI.
-   **O que morre**: 
    -   `vertice-chat-webapp/backend/app/api/v1/chat.py` (Lógica de stream manual)
    -   `src/agents/orchestrator/` (Orquestração manual)
-   **Blueprint**:
    ```python
    # O agente passa a viver no Google, não no seu container
    from vertexai.preview import reasoning_engines
    agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engines.LangchainAgent(model="gemini-3-pro"),
        display_name="Vertice-OS-Agent"
    )
    ```

### 3.2 Eficiência Financeira (Gemini 3 Context Caching)
-   **Serviço**: `caching` API do Vertex AI.
-   **O que morre**: Lógica de envio de arquivos em `vertice-chat-webapp/backend/app/api/v1/artifacts.py`.
-   **Ação**: O planejador deve prever um "Cache Manager" que congela o repositório do usuário no Google. [Docs](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/context-cacheing)

### 3.3 Banco de Dados Híbrido (AlloyDB AI)
-   **Serviço**: AlloyDB AI com ScaNN.
-   **O que morre**: 
    -   `vertice-chat-webapp/backend/app/core/database.py` (MockSession)
    -   `src/prometheus/memory/vault/` (Se existir)
-   **Ação**: Unificar metadados de usuários e vetores de memória MIRIX em uma única instância AlloyDB.

---

## 4. MAPA DE DÍVIDA TÉCNICA PARA O PLANEJADOR

| Módulo Atual | Path Exato | Destino (Google 2026) |
|--------------|------------|-----------------------|
| **Auth** | `vertice-chat-webapp/backend/app/core/auth.py` | **Firebase Identity Platform** |
| **Billing** | `vertice-chat-webapp/backend/app/core/usage_metering.py` | **Cloud Billing API + Stripe** |
| **Sandbox** | `vertice-chat-webapp/backend/app/sandbox/executor.py` | **Vertex AI Managed Extensions** |
| **Observabilidade** | `vertice-chat-webapp/backend/app/core/observability.py` | **Cloud Trace / Cloud Logging** |
| **Terminal** | `vertice-chat-webapp/backend/app/api/v1/terminal.py` | **Vertex AI Extensions SDK** |

---

## 5. ROADMAP DE IMPLEMENTAÇÃO (PASSO A PASSO)

### Fase 1: Saneamento de Segurança (Semana 1)
1.  Remover `exec()` de `vertice-chat-webapp/backend/app/sandbox/executor.py`.
2.  Configurar **Cloud KMS** e atualizar `app/core/gdpr_crypto.py` para buscar chaves do HSM.
3.  Corrigir `.gitignore` na raiz para parar de ignorar `frontend/lib/stores/`.

### Fase 2: Integração Core-Web (Semana 2)
1.  Deletar diretórios `core/` redundantes no Web App.
2.  Configurar o `sys.path` no `main.py` do backend para importar de `src/vertice_cli/core`.
3.  Migrar o banco de dados do Web App para o schema real do `database.py` no Core.

### Fase 3: Google Supremacy (Semana 3-4)
1.  Implementar **Context Caching** para projetos > 1MB de código.
2.  Migrar MIRIX para **AlloyDB AI**.
3.  Implementar **Vertex AI Agent Engine** como orquestrador padrão do SaaS.

---

## 🔗 LINKS PARA O PLANEJADOR (QUICKSTARTS)

-   **Gemini 3 SDK**: [ai.google.dev](https://ai.google.dev/gemini-api/docs/quickstart)
-   **Reasoning Engine**: [cloud.google.com/vertex-ai/docs/reasoning-engine](https://cloud.google.com/vertex-ai/docs/reasoning-engine)
-   **Context Caching**: [cloud.google.com/vertex-ai/docs/context-caching](https://cloud.google.com/vertex-ai/docs/context-caching)
-   **AlloyDB AI**: [cloud.google.com/alloydb/docs/ai/vector-search](https://cloud.google.com/alloydb/docs/ai/vector-search)

---
**Veredito Final**: O planejador deve focar na **eliminação de código customizado**. O valor do Vértice-Code está na sua capacidade de "auto-evolução" (Prometheus), e não na sua infraestrutura de sandbox ou faturamento manual. O objetivo é tornar o Web App uma interface leve e ultra-potente sobre o ecossistema Google.

---
*Documento autocontido gerado por Vertice-MAXIMUS para planejamento de alto nível.*
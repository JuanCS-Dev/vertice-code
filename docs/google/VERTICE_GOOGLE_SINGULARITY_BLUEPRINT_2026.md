# VÉRTICE-CODE: THE GOOGLE SINGULARITY (BLUEPRINT 2026)

**CLASSIFICAÇÃO:** TOP SECRET // EYES ONLY
**AUTOR:** Vertice-MAXIMUS (Gemini CLI)
**DATA:** 23 JAN 2026
**MISSÃO:** Transmutação Total para Stack Google Native & AG-UI Protocol

---

## 1. O CONCEITO "SINGULARIDADE"

A era do "Monólito Híbrido" acabou. A partir de hoje, o Vértice-Code deixa de ser um software hospedado e torna-se uma **Entidade Viva na Google Cloud**.

Não gerenciamos mais servidores. Não gerenciamos mais filas. Não escrevemos mais "conectores" manuais entre o Backend e o Frontend.

Nós usamos a **Google Cloud como Sistema Operacional** e o **AG-UI como Sistema Nervoso**.

---

## 2. ARQUITETURA ALVO (THE HOLY GRAIL)

### 2.1 O Cérebro (Vertex AI Reasoning Engine)
*   **Tecnologia:** `vertexai.preview.reasoning_engines`.
*   **Papel:** Onde a inteligência reside. Não é mais um container Docker rodando LangChain manualmente. É um **Serviço Gerenciado de Agentes**.
*   **Implementação:**
    *   Os agentes (Security, Coder, Architect) são definidos como classes Python puras usando o **Google ADK (Agent Development Kit)**.
    *   Deploy é atômico: `ReasoningEngine.create(AgentClass)`. O Google gerencia a escala, a memória e a execução de ferramentas.

### 2.2 O Sistema Nervoso (AG-UI Protocol & CopilotKit)
*   **Tecnologia:** **AG-UI Protocol** (Open Standard) + **CopilotKit**.
*   **Papel:** O elo perdido entre o Cérebro e a Face. Substitui toda a lógica manual de WebSockets/SSE do `chat.py`.
*   **Funcionamento:**
    *   **Backend:** O agente ADK emite eventos padrão AG-UI.
    *   **Middleware:** Um endpoint leve no Next.js (Cloud Run) atua como "Runtime", repassando o stream.
    *   **Frontend:** Componentes React (`<CopilotSidebar />`, `<CopilotTextarea />`) consomem o stream nativamente. Zero código de "parsing" manual no frontend.

### 2.3 A Memória Infinita (AlloyDB AI)
*   **Tecnologia:** **AlloyDB AI** com `pgvector` e `google_ml_integration`.
*   **Papel:** Memória de Longo Prazo e Indexação de Código.
*   **Diferencial 2026:**
    *   Sem middleware de Embeddings. O AlloyDB chama o modelo de embedding da Vertex AI **diretamente via SQL** (`embedding('text-embedding-005', content)`).
    *   Indexação ScaNN (10x mais rápida que HNSW) para busca de código em milissegundos.

### 2.4 A Face (Firebase App Hosting)
*   **Tecnologia:** **Next.js 16** sobre **Firebase App Hosting**.
*   **Papel:** A interface do usuário.
*   **Diferencial:**
    *   Build Zero-Config com Google Cloud Build.
    *   Server-Side Rendering (SSR) rodando em Cloud Run gerenciado.
    *   Integração nativa com Secrets Manager (para chaves de API).

---

## 3. MAPA DE MIGRAÇÃO (A JORNADA DO HERÓI)

### FASE 1: A GRANDE PURGA (Saneamento) — ✅ COMPLETA (25/01/2026)
1.  **Incinerar o Fantasma:** `rm -rf src/vertice-chat-webapp` — ✅ **DONE**
2.  **Desacoplar o Core:** Mover `src/vertice_cli` para `packages/vertice-core` — ✅ **DONE**
3.  **Instalação Limpa:** O Backend SaaS instala o Core via `pip install -e ./packages/vertice-core` — ✅ **DONE**
4.  **Soberania Flash:** Gemini 3 Flash definido como motor padrão para eficiência máxima — ✅ **DONE**

### FASE 2: O TRANSPLANTE CEREBRAL (Vertex AI) — 🔄 EM PROGRESSO
**Status (25/01/2026):** infraestrutura/plumbing concluída; migração ADK dos agentes ainda pendente.
1.  **Converter Agentes (ADK):** Refatorar `agents/coder/agent.py` e agentes críticos para classe Python pura compatível com `vertexai.preview.reasoning_engines` (Google ADK).
2.  **Deploy do Engine (DONE):**
    - Script: `tools/deploy_brain.py` (suporta `--dry-run`, fail-closed sem SDK do Vertex).
    - Registry local: `apps/agent-gateway/config/engines.json`.
    - Bibliotecas empacotáveis:
      - `packages/vertice-core/src/agents/` (import `agents.*`, com symlink root `agents`).
      - `packages/vertice-core/src/vertice_agents/` (compat `vertice_agents.*`, com symlink `src/vertice_agents`).

**Validação executada (25/01/2026, offline):**
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_orchestrator_prometheus.py -v -x
pytest tests/agents/test_registry.py -v -x
pytest tests/agents/test_coordinator.py -v -x
python -m compileall -q packages/vertice-core/src/agents packages/vertice-core/src/vertice_agents
```

### FASE 3: A RECONEXÃO NERVOSA (AG-UI)
**Status (25/01/2026):** MVP backend-only entregue (SSE `GET /agui/stream` + contrato `delta|final|tool|error`).
```bash
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
```
1.  **Backend Adapter:** Implementar o wrapper `ag_ui_adk` no servico Python para traduzir pensamentos do Gemini em eventos AG-UI.
2.  **Frontend Wiring:** Instalar `@copilotkit/react-core` e `@copilotkit/react-ui`. Substituir o `chat-interface.tsx` manual pelos componentes CopilotKit.

### FASE 4: A ETERNIDADE (Dados)
1.  **Migração SQL:** Script para mover dados do SQLite local (`prometheus.db`) para AlloyDB Omni (Dev) ou AlloyDB Google Cloud (Prod).
2.  **Auto-Embedding:** Configurar triggers no AlloyDB para gerar embeddings automaticamente quando novo código for inserido na base.

### FASE 5: GOVERNANÇA E DEVEX (Otimização)
1.  **Orquestração Turbo:** Configuração de monorepo com `turbo.json` para builds paralelos e cache em GCS.
2.  **Justiça as a Service:** Isolar o módulo de governança (`vertice_governance/justica`) em um serviço Cloud Run dedicado.

### FASE 6: NARCISSUS (A Face da Singularidade)
1.  **Stitch Integration:** Implementar a UI/UX baseada nos rascunhos do Google Stitch (@docs/google/vertice-code-webapp-ui-ux/).
2.  **Immersive Experience:** Landing page com input central direto para o agente e dashboard de streaming CoT (Chain of Thought).
3.  **Artifact Gallery:** Interface visual para gestão de código, UI e ativos gerados pela malha de agentes.

---

## 4. ESTRUTURA DE ARQUIVOS DEFINITIVA (2026)

```text
/
├── apps/
│   ├── web-console/           # Next.js 16 + CopilotKit (Firebase Hosting)
│   │   ├── src/app/api/copilot/route.ts  # O "Runtime" do AG-UI
│   │   └── firebase.json
│   └── agent-gateway/         # FastAPI (Cloud Run) - O "Corpo" do Agente
│       ├── main.py            # Roda o servidor AG-UI
│       └── requirements.txt   # Depende de "vertice-core"
│
├── packages/
│   ├── vertice-core/          # O "Espírito" (Python Library)
│   │   ├── agents/            # Definições Puras (ADK)
│   │   ├── tools/             # Ferramentas (Google Search, Code Interpreter)
│   │   └── memory/            # AlloyDB Connectors
│   └── vertice-ui/            # Design System (Radix/Tailwind)
│
└── infra/
    ├── terraform/             # IaC para AlloyDB, Vertex AI, Cloud Run
    └── cloudbuild.yaml        # Pipeline CI/CD Unificado
```

---

## 5. CUSTO E BENEFÍCIO (O RESULTADO)

| Métrica | Antes (Docker Monólito) | Depois (Google Singularity) |
| :--- | :--- | :--- |
| **Escalabilidade** | Limitada pelo tamanho da VM | **Infinita** (Serverless) |
| **Latência** | Alta (Python processando tudo) | **Baixa** (Streaming via AG-UI) |
| **Manutenção** | Pesadelo (DevOps manual) | **Zero** (Managed Services) |
| **Custo Ocioso** | 100% (VM sempre ligada) | **Perto de Zero** (Scale to Zero) |
| **Inteligência** | Gemini 1.5 via API | **Gemini 3 Nativo + Grounding** |

---

**ESTE DOCUMENTO É A LEI.**
A partir deste momento, qualquer linha de código escrita deve obedecer a este blueprint. Não há retorno. O Vértice-Code agora é **Google Native**.

*Assinado,*
**Vertice-MAXIMUS**
*Omni-Root System Architect*

---

## Update de Execução (25 JAN 2026) — Fase 3.1 (AG‑UI)

Implementado (backend-only):
- `apps/agent-gateway/app/main.py`: `GET /agui/stream` (SSE) + `/agui/tasks` (task API + stream)
- `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py`: adapter ADK-ish -> `AGUIEvent`
- `firebase.json`: App Hosting (sem rewrites do backend antigo)

Detalhes completos: `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

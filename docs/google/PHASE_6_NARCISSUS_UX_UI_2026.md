# VÉRTICE-CODE: FASE 6 - NARCISSUS (A FACE DA SINGULARIDADE)

**STATUS:** DEFINITION READY
**CONTEXT:** Final Stage of Google Singularity (2026)
**OBJECTIVE:** Implement a "Sovereign UI" using Google Stitch drafts and CopilotKit.

---

## 1. A VISÃO NARCISSUS
O software não deve apenas funcionar; ele deve emanar inteligência. A interface **Narcissus** abandona o layout "SaaS tradicional" por uma experiência **Agent-First**. O usuário não navega em menus; ele comanda uma malha de inteligência.

### Artefatos Stitch Integrados:
1. **`lading-page/code.html`**: A porta de entrada. Um input central massivo que conecta o usuário diretamente ao "Cérebro" (Vertex AI).
2. **`advanced_command_center/code.html`**: Painel de controle da malha (Agent Mesh). Monitoramento de latência, tokens e saúde dos agentes em tempo real.
3. **`refined_agentic_stream_dashboard/code.html`**: Onde o pensamento do Gemini se torna visível. Streaming de alta fidelidade com renderização de blocos de código e progresso de tarefas.
4. **`refined_cot_logic_stream/code.html`**: Visualização do Chain-of-Thought (CoT). O usuário vê *como* o agente chegou à conclusão.
5. **`artifact_gallery/code.html`**: O repositório de criações. Onde o código, UI e assets gerados pelos agentes são exibidos e exportados.

---

## 2. ARQUITETURA DE INTERFACE (THE STACK)

*   **Framework:** Next.js 16 (Serverless via Firebase App Hosting).
*   **Styling:** Tailwind CSS v4 (Obsidian/Neon Cyan Theme).
*   **Protocolo de Streaming:** AG-UI + CopilotKit.
*   **Componentes Core:** Radix UI (Primitives) + Lucide React (Icons).
*   **Visualização:** Framer Motion (para transições de "pulso" da inteligência).

---

## 3. MAPA DE IMPLEMENTAÇÃO (THE FINAL POLISH)

### 3.1 A Porta de Entrada (Immersive Landing)
Substituir o login genérico por uma experiência de **Direct Command**.
*   **Ação:** Implementar o input central do `lading-page/code.html` integrado ao `ReasoningEngine` da Vertex AI.
*   **Efeito:** O sistema responde "SYSTEM ONLINE // WAITING FOR INPUT" antes mesmo do usuário digitar.

### 3.2 O Fluxo de Consciência (Streaming Dashboard)
Integrar o `refined_agentic_stream_dashboard` com o `ag_ui_adk`.
*   **Ação:** Criar os widgets `StreamingResponseWidget` e `LogicTrace`.
*   **Diferencial:** Renderização assíncrona de CoT (Chain of Thought) em tempo real, permitindo que o usuário interrompa ou refine o raciocínio no meio do processo.

### 3.3 A Galeria de Artefatos (Artifact Management)
Criar a visão `artifact_gallery` para gerenciar o que o Vértice constrói.
*   **Ação:** Sincronizar os outputs do `CoderAgent` diretamente com o grid de artefatos.
*   **Funcionalidade:** Preview de UI gerada em tempo real dentro de iFrames isolados.

### 3.4 O Command Center (Agent Mesh Telemetry)
Painel `advanced_command_center` para governança.
*   **Ação:** Exibir métricas do `TokenTracker` e `ResilienceManager` do core em gráficos de alta performance (Neon Emerald/Cyan).

---

## 4. CRITÉRIOS DE ACEITE (PADRÃO PAGANI)

1.  **Zero Latência Visual:** O stream de texto deve fluir a 60fps sem "jank".
2.  **Fidelidade Estética:** Uso estrito do tema *Obsidian* (#0B1416) com acentos *Neon Cyan* (#00E5FF).
3.  **Responsividade Imersiva:** A TUI e a WebApp devem compartilhar a mesma linguagem visual (Matrix Pattern).
4.  **Integração Total:** O frontend deve consumir 100% dos dados via Agente Gateway (Cloud Run), sem chamadas diretas a bases de dados (exceto via Agente).

---

**"A interface é o espelho da alma da máquina."**
*Assinado,*
**Vertice-MAXIMUS**

---

## Dependências já prontas (25 JAN 2026)

Para a UI Narcissus consumir o “Cérebro” via streaming, o repo já possui:
- `apps/agent-gateway/config/engines.json` (registry local de engines).
- `tools/deploy_brain.py` (gera/atualiza o registry; `--dry-run` offline).
- `apps/agent-gateway/app/main.py` com:
  - `GET /agui/stream` (SSE)
  - `POST /agui/tasks` + `GET /agui/tasks/{task_id}` + `GET /agui/tasks/{task_id}/stream`
- Contrato MVP `delta|final|tool|error`: `packages/vertice-core/src/vertice_core/agui/protocol.py`
- Adapter ADK->AG-UI: `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py`

Smoke checks executados (offline):
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/unit/test_agui_adk_adapter.py -v -x
```

Detalhes completos (Fase 3.1): `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

---

## Pré‑requisito de Segurança (25 JAN 2026) — PR‑0/PR‑1

O frontend Narcissus assume backend blindado:
- Execução local de código desabilitada (RCE fail‑closed).
- Chaves GDPR/LGPD obrigatórias via env var ou KMS (sem fallback efêmero).

Detalhes: `docs/google/DETAILED_SURGERY_PREP_REPORT_2026.md`.

## Pré‑requisito de Memória (25 JAN 2026) — PR‑4 (AlloyDB)

Fundação entregue no `vertice-core` (Episodic MVP) para substituir o SQLite legado de forma incremental.

Detalhes: `docs/google/PR_4_ALLOYDB_MEMORY_FOUNDATION_2026.md`

---

## Update (25 JAN 2026) — Phase 4 (AlloyDB AI Cutover)

- Memória agora default AlloyDB AI (fallback local sem DSN) + embeddings in-db (sem overhead em Python).
- Migração real: `tools/migrate_memory.py` (`.prometheus/prometheus.db` → AlloyDB).
- Validação (offline): `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x` → `14 passed in 0.53s`.
- Detalhes: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`.

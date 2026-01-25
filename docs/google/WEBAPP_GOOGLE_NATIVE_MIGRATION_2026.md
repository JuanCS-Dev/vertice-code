# Vértice-Code: Google Native Migration Master Plan (2026)

**Date:** January 23, 2026
**Target Architecture:** Google Cloud Native (Serverless + Managed AI)
**Objective:** Elimination of over-engineering, maximization of security, and performance via the Google ecosystem.

---

## 1. Executive Summary: The "Delete & Connect" Strategy

The current audit reveals a classic "2024 era" architecture: heavy on manual container orchestration, custom sandboxing, and self-hosted databases. In 2026, the Google Cloud ecosystem renders 60% of this code obsolete.

**The Strategy:**
1.  **Delete** the custom sandbox (`executor.py`), manual orchestrator, and local SQLite persistence.
2.  **Connect** directly to managed Vertex AI and Firebase services.
3.  **Result:** A "Shell" application that is stateless, infinitely scalable, and relies on Google's security perimeter.

---

## 2. Architecture Transformation

### Before (Current)
*   **Compute:** Docker Containers (API, Worker, Sandbox, DB).
*   **AI:** Manual LangChain chains, custom tool definitions.
*   **Sandbox:** Insecure local `exec()` fallback or complex gVisor setup.
*   **DB:** Local SQLite/Postgres containers.
*   **Hosting:** Manual Vercel/Docker build.

### After (Google Native 2026)
*   **Frontend:** **Firebase App Hosting** (Next.js 16 Serverless).
*   **Backend API:** **Cloud Run** (Stateless FastAPI adapter).
*   **AI Core:** **Vertex AI Reasoning Engine** (Managed Agent Runtime).
*   **Sandbox:** **Vertex AI Code Interpreter** (Managed Extension).
*   **Memory:** **AlloyDB AI** (High-Performance Vector) OR **Firestore** (Lite).

---

## 3. Migration Action Plan

### 3.1 🚨 KILL: Custom Sandbox (`executor.py`)
The file `vertice-chat-webapp/backend/app/sandbox/executor.py` is a security liability.
**Replacement:** Vertex AI Code Interpreter Tool.

**Implementation (Python SDK):**
```python
from vertexai.preview import reasoning_engines
from vertexai.generative_models import Tool

# No more custom Docker/gVisor code.
# Just enable the capability.
agent = reasoning_engines.LangchainAgent(
    model="gemini-3-pro",
    tools=[Tool.from_google_search_retrieval(search_grounding_tool),
           Tool.code_interpreter_tool()] # <--- THIS REPLACES executor.py
)
```

### 3.2 ⚡ UPDATE: Frontend Hosting (`firebase.json`)
Migrate from manual builds to **Firebase App Hosting**. This natively supports Next.js 16, handles SSR via Cloud Functions, and integrates with GitHub.

**New `firebase.json`:**
```json
{
  "apphosting": {
    "rootDirectory": "vertice-chat-webapp/frontend",
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "environmentVariables": {
      "NEXT_PUBLIC_API_URL": "",
      "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "vertice-ai"
    }
  }
}
```

### 3.3 🧠 MIGRATE: Orchestration & Memory
Move from `src/agents/orchestrator` to **Vertex AI Reasoning Engine**.

*   **Why?** It manages the runtime, context caching, and tool execution loop for you.
*   **Memory:** Use **AlloyDB AI** if you are indexing the *entire codebase* (scann index is 10x faster). Use **Firestore Vector Search** if you only need conversation history.

**Recommendation:** Go with **AlloyDB AI** as per the original analysis to future-proof the "Codebase Knowledge Graph".

### 3.4 🛡️ SECURE: Auth & Secrets
*   **Auth:** Replace custom JWT logic (`auth.py`) with **Firebase Authentication** (Identity Platform). It handles MFA, social login, and session management.
*   **Secrets:** Move `.env` files and `gdpr_crypto.py` keys to **Secret Manager**. Mount them as volumes in Cloud Run.

---

## 4. Cost & Performance Analysis (2026 Estimates)

| Component | Current (Containers) | New (Google Native) | Savings/Impact |
| :--- | :--- | :--- | :--- |
| **Sandbox** | High (Requires heavy VM/gVisor) | **Free** (Included in Gemini API*) | **100% Compute Reduction** |
| **Vector DB** | Fixed Cost (Always-on Instance) | **AlloyDB** (Scalable) / **Firestore** (Pay-go) | **Dynamic Scaling** |
| **Frontend** | Fixed Vercel/VM Cost | **App Hosting** (Scale to Zero) | **Efficiency** |
| **Ops Effort** | High (Patching, Logs, Monitor) | **Zero** (Managed Services) | **Focus on Logic** |

*\*Note: Gemini API pricing applies, but the infrastructure cost is abstracted.*

---

## 5. Immediate Next Steps

1.  **Run:** `rm vertice-chat-webapp/backend/app/sandbox/executor.py`
2.  **Confirm:** `firebase.json` (repo root) is using **App Hosting** (no legacy rewrites).
3.  **Refactor:** Update `backend/app/api/v1/chat.py` to call `vertexai.reasoning_engines` instead of local agent classes.
4.  **Deploy:**
    ```bash
    # Frontend
    firebase deploy --only apphosting

    # Backend
    gcloud run deploy vertice-api --source ./backend
    ```

**Signed:** Gemini CLI (Agent 2026)

---

## Update de Execução (25 JAN 2026)

Entregáveis já implementados para destravar o caminho Google Native:
- `tools/deploy_brain.py` (deploy/registry de engines com `--dry-run` offline).
- `apps/agent-gateway/config/engines.json` (fonte de verdade local do gateway).
- Bibliotecas empacotáveis e compatíveis:
  - `packages/vertice-core/src/agents/` (import `agents.*`).
  - `packages/vertice-core/src/vertice_agents/` (import `vertice_agents.*` para compat com testes/código legado).

Validação executada (offline):
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_orchestrator_prometheus.py -v -x
```

## Update de Execução (25 JAN 2026) — Fase 3 (AG‑UI) Backend‑Only MVP

Entregue (backend-only):
- Runtime SSE: `GET /agui/stream` em `apps/agent-gateway/app/main.py`
- Contrato MVP (schema estável): `packages/vertice-core/src/vertice_core/agui/protocol.py`
  - Tipos: `delta|final|tool|error`
- Adapter ADK->AG-UI: `packages/vertice-core/src/vertice_core/agui/ag_ui_adk.py`
- Task API: `POST /agui/tasks` + `GET /agui/tasks/{task_id}` + `GET /agui/tasks/{task_id}/stream`

Validação executada (offline):
```bash
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/unit/test_agui_adk_adapter.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
python -m compileall -q apps/agent-gateway/app/main.py packages/vertice-core/src/vertice_core/agui
```

Próximo passo (fora desta PR): wiring do frontend (CopilotKit) para consumir o runtime do gateway.

Detalhes completos (Fase 3.1): `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

---

## Update (25 JAN 2026) — PR‑4 (AlloyDB Memory Foundation — Episodic MVP)

Entregue (sem infra real, config-driven) no `vertice-core`:
- `packages/vertice-core/src/vertice_core/memory/alloydb_connector.py` (pool)
- `packages/vertice-core/src/vertice_core/memory/schema.sql` (schema mínimo)
- `packages/vertice-core/src/vertice_core/memory/cortex/episodic.py` (toggle `sqlite|alloydb`)

Validação: `pytest tests/unit/test_alloydb_migration.py -v -x`
Detalhes: `docs/google/PR_4_ALLOYDB_MEMORY_FOUNDATION_2026.md`

## Update (25 JAN 2026) — PR‑0/PR‑1 (Security Hardening)

- **RCE:** sandbox local do backend desabilitado (fail‑closed). Execução de código deve ser via **Vertex AI Code Interpreter**.
- **GDPR/KMS:** master key obrigatória via env var ou via KMS (sem chaves efêmeras).

Comandos de validação: `docs/google/DETAILED_SURGERY_PREP_REPORT_2026.md`.

## Update (25 JAN 2026) — PR‑5 (Google Managed Vertex AI)

Entregue:
- Execução de código via **Vertex AI Code Execution** (sandbox gerenciado), com execução local bloqueada (fail‑closed).
- Providers em modo “Google‑native 2026” com modelos permitidos: **Gemini 3 (Pro/Flash)** e **Claude 4.5 (Sonnet/Opus via Vertex AI)**.

Validação executada (offline):
```bash
pytest vertice-chat-webapp/backend/tests/unit/test_sandbox_executor.py -v -x
pytest tests/unit/test_coder_reasoning_engine_app.py -v -x
pytest tests/integration/test_vertex_deploy.py -v -x
```

Detalhes: `docs/google/PR_5_GOOGLE_MANAGED_VERTEX_2026.md`

---

## Update (25 JAN 2026) — Phase 4 (AlloyDB AI Cutover)

- Memória agora default AlloyDB AI (fallback local sem DSN) + embeddings in-db.
- Migração real: `tools/migrate_memory.py` (`.prometheus/prometheus.db` → AlloyDB).
- Validação (offline): `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x` → `14 passed in 0.53s`.
- Detalhes: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`.

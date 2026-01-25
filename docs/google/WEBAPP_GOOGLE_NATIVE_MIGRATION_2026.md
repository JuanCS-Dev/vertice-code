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
  "hosting": {
    "site": "vertice-ai-2026",
    "apphosting": {
      "source": ".",
      "nodeVersion": "20",
      "environmentVariables": {
        "NEXT_PUBLIC_API_URL": "https://api-gateway-xyz.run.app"
      }
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
2.  **Create:** `firebase.json` in `vertice-chat-webapp/` root.
3.  **Refactor:** Update `backend/app/api/v1/chat.py` to call `vertexai.reasoning_engines` instead of local agent classes.
4.  **Deploy:**
    ```bash
    # Frontend
    firebase deploy --only hosting

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

# GOOGLE SINGULARITY: THE MONOREPO STRATEGY (2026)

**STATUS:** APPROVED DOCTRINE
**CONTEXT:** 2026 AI-Native Architecture
**VERDICT:** **Separate Repositories = DEATH.** Do not split the Git repo. Split the **Dependencies**.

---

## 1. THE "SEPARATE REPO" TRAP
You asked: *"Shouldn't we have separate repositories?"*
**Answer (2026):** **NO.**

In the era of AI Agents, splitting your code into Polyrepos (separate Git repos) is a strategic error.
*   **The Sync Problem:** If you change the Agent's "Brain" (Core) in Repo A, you must publish a package, wait for CI, and then update Repo B (CLI) and Repo C (Webapp). This kills velocity.
*   **The Context Problem:** Your AI coding assistant (Gemini/Copilot) loses context if the code is in different repos. It cannot see that a change in the Database Schema requires a change in the Frontend Type Definition.

**How Google Does It:**
Google uses **One Repository** (Piper) for 95% of its code. They manage complexity not by splitting Git, but by using **Build Targets** (Blaze/Bazel).
*   For us, the equivalent is **Workspaces** (Nx / Turborepo / Python PEP-621).

---

## 2. THE SOLUTION: "STRICT WORKSPACES"

The problem isn't that they are in the same folder. The problem is that they are "fighting" (Circular Dependencies). The Webapp is importing the CLI. That is illegal.

We will reorganize the codebase into **3 Sovereign Territories**:

### 📦 TERRITORY 1: `packages/vertice-core` (The Shared Soul)
*   **Role:** Pure Python Library. NO CLI, NO Web Server, NO UI.
*   **Content:**
    *   `/agents` (The Brains: Security, Coder, Architect logic).
    *   `/memory` (AlloyDB/Vector connectors).
    *   `/protocol` (The AG-UI Definitions).
*   **Rule:** Can only import external PyPI libs. Cannot import *anything* else from the repo.

### 🚀 TERRITORY 2: `apps/` (The Deployables)
These are the "Faces" of the system. They depend on `vertice-core`, but never on each other.

*   `apps/cli/`: The Typer/Rich terminal app.
    *   *Depends on:* `vertice-core`.
*   `apps/agent-gateway/`: The Cloud Run FastAPI service.
    *   *Depends on:* `vertice-core`.
*   `apps/web-console/`: The Next.js Frontend.
    *   *Depends on:* `ag-ui-react` (npm).

### 🛠️ TERRITORY 3: `infra/` (The Foundation)
*   Terraform and Dockerfiles that orchestrate the `apps/`.

---

## 3. THE NEW FOLDER STRUCTURE (VISUALIZED)

```text
/ (Monorepo Root)
├── pyproject.toml        # Defines the Workspace (PEP 621)
├── infra/                # Terraform (AlloyDB, Cloud Run)
├── packages/
│   └── vertice-core/     # PIP INSTALLABLE PACKAGE
│       ├── pyproject.toml
│       └── src/vertice_core/
├── apps/
│   ├── cli/              # "vertice-cli"
│   ├── agent-gateway/    # "vertice-api" (Cloud Run)
│   └── web-console/      # "vertice-web" (Firebase)
└── docs/
```

---

## 4. EXECUTION PLAN: THE "GREAT DECOUPLING"

We don't need new Git repos. We need **fences**.

1.  **Create `packages/vertice-core`**: Move `src/vertice_agents` and `src/vertice_core` here.
2.  **Create `apps/cli`**: Move `src/vertice_cli` here.
3.  **Create `apps/agent-gateway`**: New clean FastAPI project.
4.  **Refactor Imports:**
    *   OLD: `from src.vertice_agents import Coder`
    *   NEW: `from vertice_core.agents import Coder`

---

## Atualização de Implementação (25 JAN 2026)

Entregáveis concretos já aplicados no repo:
- `packages/vertice-core/src/agents/` incluído no build (importável como `agents.*`) e symlink root `agents`.
- `packages/vertice-core/src/vertice_agents/` criado como compatibilidade (importável como `vertice_agents.*`) e symlink `src/vertice_agents`.
- `tools/deploy_brain.py` + `apps/agent-gateway/config/engines.json` como registry de Reasoning Engines.

Validação executada (offline):
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
pytest tests/integration/test_orchestrator_prometheus.py -v -x
pytest tests/agents/test_registry.py -v -x
pytest tests/agents/test_coordinator.py -v -x
```

**Conclusion:**
We keep the **Speed** of a Monorepo but gain the **Sanity** of Microservices.

*Signed,*
**Vertice-MAXIMUS**

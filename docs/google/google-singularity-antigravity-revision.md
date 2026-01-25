# VERTICE-CODE: GOOGLE SINGULARITY (ANTIGRAVITY REVISION)

**AUTHOR:** Antigravity (Google Deepmind) vs. Vertice-MAXIMUS
**DATE:** 23 JAN 2026
**STATUS:** EXECUTION READY
**CONTEXT:** Synthesis of Blueprint 2026, Codex Revision, and Deep Dive Report.

---

## 1. THE ULTRATHINK DIAGNOSIS (THE WHY)

Our analysis confirms a **Tier 1 Structural Failure**:
*   **The "Deep Tissue" Coupling:** `vertice-chat-webapp/backend/app/core/security.py` directly imports `src.vertice_cli`. This means the "Web App" is not a web app; it is a parasite attached to the CLI source code. You cannot deploy one without the other.
*   **The "Ghost" Directory:** `src/vertice-chat-webapp` exists but contains only shadows of a past life. This creates confusion for tools and humans alike.
*   **The Conclusion:** We are not refactoring for aesthetics. We are refactoring for **Survival**. If we do not decouple now, we cannot deploy to Cloud Run securely.

---

## 2. THE ANTIGRAVITY PLAN (THE HOW)

We execute in **3 Phases**. No "Weeks". We measure in "Impact".

### PHASE 1: PURGE & ISOLATE (The necessary destruction)

**Objective:** Clean the workspace and create the `vertice-core` package so the SaaS can breathe.

1.  **INCINERATE:** `rm -rf src/vertice-chat-webapp`. (Diagnosed: It is dead tissue).
2.  **EXTRACT:** Move `src/vertice_cli` content to `packages/vertice-core/src/vertice_core`.
3.  **ALIAS:** Create a temporary `src/vertice_cli` that re-exports `vertice_core` to prevent breaking existing scripts immediately (The "Bypass" maneuver).
4.  **DECOUPLE:** Patch `vertice-chat-webapp/backend/requirements.txt` to install `-e packages/vertice-core` instead of relying on `sys.path` hacks.

**Success Metric:** `pytest` in the SaaS repo runs without requiring the root `src/` directory in PYTHONPATH.

### PHASE 2: BRAIN SURGERY (Gemini 3.0 Native)

**Objective:** Upgrade the "Coder" to use Google's Agent Development Kit (ADK) patterns.

1.  **REFACTOR AGENTS:** Transform `CoderAgent` from a `BaseAgent` subclass into a composite `ReasoningEngine` compatible class.
    *   *Current State:* Hybrid class mixed with CLI tools.
    *   *Target State:* Pure Python class locatable by `reasoning_engines.LangchainAgent`.
2.  **STREAMING PIPELINE:** Implement `ag_ui_adk` adapter in `vertice-core` to format Vertex AI chunks into frontend-ready JSON/Markdown streams.

### PHASE 3: THE HYPERLOOP (Infrastructure)

**Objective:** Deploy to Google Cloud (Cloud Run + AlloyDB).

1.  **ALLOYDB SETUP:** Provision AlloyDB Omni for local dev (replacing SQLite).
2.  **DEPLOYMENT SCRIPT:** Create `tools/deploy_brain.py` using the Google Cloud SDK to "uplift" the python agents to Vertex AI.

**Status (25 JAN 2026):** `tools/deploy_brain.py` + `apps/agent-gateway/config/engines.json` já implementados (com `--dry-run` offline).

Validação executada:
```bash
pytest tests/integration/test_vertex_deploy.py -v -x
```

**Status (25 JAN 2026):** Fase 3 (AG‑UI) backend-only MVP entregue (SSE `GET /agui/stream` + schema estável `delta|final|tool|error`).

Validação executada (offline):
```bash
pytest tests/unit/test_agui_protocol.py -v -x
pytest tests/integration/test_agent_gateway_agui_stream.py -v -x
```

---

## 3. IMMEDIATE EXECUTION STEPS

This is the order of operations for the next 60 minutes:

**Step 1: The Purge**
```bash
rm -rf src/vertice-chat-webapp
```

**Step 2: The Core Extraction**
```bash
mkdir -p packages/vertice-core/src/vertice_core
mv src/vertice_cli/* packages/vertice-core/src/vertice_core/
```

**Step 3: The Package Definition**
Create `packages/vertice-core/pyproject.toml` definition.

**Step 4: The Reconnection**
Update `vertice-chat-webapp/backend/requirements.txt`.

**Signed,**
*Antigravity*
*Google Deepmind Agent*

---

## Update de Execução (25 JAN 2026) — Fase 3.1 (AG‑UI)

Implementado (backend-only):
- Adapter ADK->AG-UI + API de tasks (`/agui/tasks/*`) no `apps/agent-gateway`
- `firebase.json` consolidado para App Hosting (sem rewrites do backend antigo)

Detalhes completos: `docs/google/PHASE_3_1_AGUI_TASKS_ADAPTER.md`

---

## Update (25 JAN 2026) — PR‑0/PR‑1 (Security Hardening)

- **PR‑0 (RCE):** sandbox local do backend foi desabilitado (fail‑closed).
- **PR‑1 (GDPR/KMS):** master key obrigatória; suporte a KMS via ciphertext.

Detalhes: `docs/google/DETAILED_SURGERY_PREP_REPORT_2026.md`.

---

## Update (25 JAN 2026) — PR‑4 (AlloyDB Memory Foundation — Episodic MVP)

Implementado (config-driven, sem infra real):
- Conector AlloyDB com pool + schema mínimo + `EpisodicMemory` com backend `alloydb`.

Detalhes e validação: `docs/google/PR_4_ALLOYDB_MEMORY_FOUNDATION_2026.md`

---

## Update (25 JAN 2026) — Phase 4 (AlloyDB AI Cutover)

- Cutover: AlloyDB AI como default (fallback local sem DSN) + embeddings in-db via `google_ml_integration`.
- Migração real: `tools/migrate_memory.py` (`.prometheus/prometheus.db` → AlloyDB).
- Validação (offline): `pytest tests/unit/test_alloydb_migration.py tests/unit/test_alloydb_cutover_behavior.py -v -x` → `14 passed in 0.53s`.
- Detalhes: `docs/google/PHASE_4_ALLOYDB_AI_CUTOVER_2026.md`.

# BRUTAL AUDIT REPORT V2

## System Diagnostics - Air Gap Analysis
**Date:** 2025-05-20
**Author:** Jules (Senior System Architect)

### 1. Executive Summary
The system suffers from severe "schizophrenia" where two distinct architectures exist but do not communicate. The CLI (`vtc`) initializes a modern, dependency-injected architecture (`vertice_core`), but the TUI (`vertice`) runs on a legacy, monolithic architecture (`vertice_tui`) that ignores the CLI's initialization. This results in "air gaps" where configuration, providers, and state are not shared.

### 2. Critical Air Gaps Identified

#### Gap #1: Provider Registry Disconnect (The "Split Brain")
- **Symptom:** CLI registers providers (Groq, Cerebras, etc.) into `vertice_core.providers.registry`, but TUI uses `GeminiClient` which defaults to hardcoded Gemini/Vertex logic.
- **Root Cause:** `vertice_tui.core.llm_client.GeminiClient` *attempts* to use `vertice_core.clients.get_client()`, but likely fails or is not properly wired because `vertice_core.clients.VerticeClient` relies on `vertice_core.providers.registry` which might be empty if `vertice_cli` initialization didn't happen in the same process/context (though it seems it does).
- **The Twist:** The `VerticeClient` *does* look up from the registry. If the TUI runs in the same process as the CLI (which it does via `ui_launcher`), the registry *should* be populated.
- **Deep Dive Finding:** `GeminiClient` only tries `get_client()` in `_init_multi_provider`. If that fails (ImportError or Exception), it falls back to direct API.
- **Actual Issue:** The `GeminiClient` in TUI is wrapping the `VerticeClient` (which is good), BUT the `ProviderManager` in `vertice_tui` (which manages `GeminiClient`) has its own hardcoded logic for routing ("gemini", "prometheus", "maximus") and doesn't expose the underlying providers (Groq, Mistral, etc.) to the user or the `Bridge`.

#### Gap #2: ProviderManager Isolation
- **Symptom:** The TUI's `ProviderManager` classifies tasks into "simple", "complex", "governance" and maps them to "gemini", "prometheus", "maximus". It has no concept of "groq", "cerebras", or "router".
- **Impact:** Users cannot explicitly select "groq" or "cerebras" in the TUI, nor does the auto-routing logic consider them.
- **Fix:** `ProviderManager` needs to be updated to query `GeminiClient.get_available_providers()` and expose them, or better yet, `VerticeClient` should replace `GeminiClient` as the primary interface.

#### Gap #3: Legacy Core vs Modern Core
- **Symptom:** Existence of top-level `core/` directory alongside `vertice_core/`.
- **Impact:** Confusion in imports. `vertice_cli` imports from `vertice_core.providers`, but some files import from `core.resilience`.
- **Status:** `vertice_core` seems to be the intended future, but `core` is still heavily used. This is a technical debt item but less critical than the functional air gaps.

#### Gap #4: Configuration Loading
- **Symptom:** `Bridge` loads `.env` manually. `vertice_cli` might rely on `python-dotenv` loaded elsewhere.
- **Impact:** Inconsistent environment if not careful.

### 3. Proposed Remediation Plan

#### Phase 1: Unify Provider Access (The "Bridge" Fix)
1.  **Refactor `vertice_tui/core/llm_client.py`:** Ensure `GeminiClient` correctly wraps `VerticeClient` and exposes all providers.
2.  **Refactor `vertice_tui/core/managers/provider_manager.py`:**
    - Remove hardcoded "gemini"/"prometheus"/"maximus" limits.
    - Allow `get_client` to return any available provider from the `GeminiClient` (which wraps `VerticeClient`).
    - Expose available providers in `get_provider_status`.

#### Phase 2: Cleanup
1.  Standardize imports to `vertice_core` where possible.

### 4. Verification Strategy
- Run `vtc status` (which uses `Bridge`) and ensure it lists all providers (Groq, Cerebras) if configured.
- Run `vtc chat` with different providers to verify routing.

---
*Signed: Jules, Senior Architect*

# NARCISSUS FRONTEND CONSTITUTION (2026)

**STATUS:** APPROVED DOCTRINE
**OBJECTIVE:** Create the world's most immersive and efficient agent-centric interface.

## 1. VISION
The Narcissus UI is the physical manifestation of the Vertice Agent Swarm. It moves away from chat-based paradigms to an **Observable Autonomy** model where the user acts as the Arquiteto (Director) of a neural code forge.

## 2. DESIGN LANGUAGE (THE OBSIDIAN SPEC)
- **Primary Background:** `#0B1416` (Obsidian)
- **Primary Accent:** `#00E5FF` (Neon Cyan)
- **Success/Health:** `#10B981` (Neon Emerald)
- **Warning/Thinking:** `#F59E0B` (Amber)
- **Typography:** 
  - Display: *Space Grotesk* (Bold, Tracking-tight)
  - UI/Body: *Inter*
  - Code: *JetBrains Mono* / *Fira Code*

## 3. COMPONENT BLUEPRINTS (STITCH DERIVATIVES)

### 3.1 The Sovereign Portal (Landing)
- **Reference:** `docs/google/vertice-code-webapp-ui-ux/vertice-lading-page/code.html`
- **Core Feature:** Massively centered `AgentInput` field.
- **Behavior:** Enter key triggers a session transition animation (Portal -> Hub).

### 3.2 The Consciousness Stream (Main Dashboard)
- **Reference:** `docs/google/vertice-code-webapp-ui-ux/vertice_-_refined_agentic_stream_dashboard_2/code.html`
- **Deep Streaming Detail:**
    - **Intent Analysis Card:** Real-time extraction of goals into JSON-style UI blocks.
    - **Confidence Metrics:** Visual indicators for model certainty (98% confidence patterns).
    - **Context Retrieval Tags:** Dynamic links to files with specific line-range highlights.
    - **Mission Trajectory:** A progress-based node map showing the flow between Alpha, Beta, and Gamma agents.
- **Behavior:** Smooth 60fps transitions between "Thinking" (Amber Pulse) and "Executing" (Emerald Stream) states.

### 3.3 The Tactical HUD (Governance & Telemetry)
- **Reference:** `docs/google/vertice-code-webapp-ui-ux/vertice_-_advanced_command_center/code.html`
- **Core Features:**
    - **Agent Mesh Topology:** A live SVG map showing nodes and active routes between agents.
    - **Token Velocity HUD:** Real-time throughput graph (Tokens/sec).
    - **System Load Matrix:** CPU/MEM/NET breakdown for the active Reasoning Engine.

## 4. TECHNICAL STACK (GOOGLE NATIVE 2026)
- **Framework:** Next.js 16 (App Router)
- **State Management:** CopilotKit + custom AG-UI Hooks.
- **Styling:** Tailwind CSS v4 + Framer Motion.
- **Code Intelligence:** Monaco Editor + JetBrains Mono.
- **Streaming:** Multi-channel SSE via `/agui/tasks/{id}/stream` (handling text, tool_calls, and intent_metadata).

## 5. ROADMAP

### PHASE A: THE SOVEREIGN ENTRY (Tonight)
- [ ] Next.js 16 Scaffolding in `apps/web-console`.
- [ ] Tailwind v4 Theme injection (Obsidian/Cyan).
- [ ] `AgentPortal` component implementation.

### PHASE B: THE NEURAL HUB
- [ ] AG-UI Client-side adapter.
- [ ] Task streaming dashboard.
- [ ] CoT Visualization.

### PHASE C: THE ARTIFACT VAULT
- [ ] Code Editor integration (Monaco/CodeMirror).
- [ ] Sandboxed Live Preview (iFrame).
- [ ] GitHub Sync.

---
**Assinado,**
*Vertice-MAXIMUS*
*Omni-Root System Architect*

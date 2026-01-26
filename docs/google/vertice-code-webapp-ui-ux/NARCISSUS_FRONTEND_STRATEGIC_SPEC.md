# NARCISSUS FRONTEND STRATEGIC SPECIFICATION (2026)

**AUTHOR:** Vertice-MAXIMUS & Arquiteto
**STATUS:** CANONICAL DOCTRINE
**VERSION:** 1.0 (Singularity Era)

## 1. THE DELEGATIVE PARADIGM
Narcissus is NOT a chat interface. It is a **Command & Control Dashboard**. 
The interaction flow is: **Command** (Portal) -> **Observe** (Stream) -> **Audit** (Trace) -> **Refine** (Forge).

## 2. AGENT-UI MAPPING (THE TRIAD)
Our interface must visually represent our distinct Agent Nodes:
- **Node ALPHA (Architect):** High-level design, ADRs, and Mermaid diagrams.
- **Node BETA (Coder):** Implementation, testing, and file operations.
- **Node GAMMA (Reviewer):** Security, quality, and context validation.
- **SUPERVISOR (Sigma Style):** The trajectory consolidator (Mission Progress).

## 3. COMPONENT ARCHITECTURE (STITCH-DRIVEN)

### 3.1 The Agent Portal (Entry Layer)
- **Visuals:** Obsidian black, centered input, pulsing cyan accents.
- **Logic:** Handshake with Firebase Auth and initial task creation.

### 3.2 The Neural Trace (Thinking Layer)
- **Visuals:** Real-time event log with absolute timestamps (00:01s).
- **Features:**
    - **Intent Card:** Auto-extracted JSON goals.
    - **Context Links:** Direct line-range references to codebase.
    - **Trajectory HUD:** 65% style progress bar with agent handoff indicators.

### 3.3 The Artifact Forge (Action Layer)
- **Visuals:** Monaco Editor + Sandboxed Preview iFrame.
- **Features:**
    - Character-by-character code streaming.
    - "Unsaved Changes" persistence indicators tied to AlloyDB.

## 4. PROTOCOL EXTENSIONS (AG-UI 2026)
The backend MUST emit specialized events to feed the Narcissus detail level:
- `event: intent` -> Populates the Intent Analysis card.
- `event: trajectory` -> Updates the Mission Map nodes.
- `event: context_ref` -> Creates clickable file reference tags.

## 5. DESIGN TOKENS
- **Obsidian:** `#0B1416`
- **Cyan Neon:** `#00E5FF`
- **Emerald Pulse:** `#10B981`
- **Amber Thinking:** `#F59E0B`

---
**Assinado,**
*Vertice-MAXIMUS (Neuroshell Agent)*

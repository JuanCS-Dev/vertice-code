# ⚡ PROJECT VIVID: The Runtime Evolution Roadmap
**Objective**: Transform Vertice-Code-Web from a "Static Editor" to a "Live Runtime Environment".
**Target**: Surpass Bolt.new (Browser-only) and Claude Code (Read-only) by combining **In-Browser Preview** with **Cloud-Native Power**.

---

## 🏗️ ARCHITECTURAL DECISION: The "Hybrid Sovereign" Model

We reject the choice between "Browser-only" (Bolt) and "Cloud-only" (GitHub Codespaces). We choose **BOTH**.

| Layer | Technology | Purpose | Implementation |
| :--- | :--- | :--- | :--- |
| **Instant UI** | **Sandpack** (Wasm/Bundler) | Render React components, HTML, Tailwind instantly in the browser. Zero latency. | `@codesandbox/sandpack-react` |
| **Heavy Logic** | **Vertice MCP** (Cloud Run) | Execute Python scripts, heavy builds, Docker containers, DB migrations. | `xterm.js` over WebSocket to MCP |

---

## 🗓️ PHASE 1: INSTANT REALITY (Sandpack Integration)
**Goal**: When Vertice generates a React component, it appears INSTANTLY on the right panel.

### 1.1 Core Integration
- [ ] Install `@codesandbox/sandpack-react`
- [ ] Create `components/artifacts/preview/sandpack-client.tsx`
- [ ] Configure "Vite-React-TS" template with Tailwind CSS support (critical for our stack).

### 1.2 The "Dual-Brain" Synchronization
- [ ] **Monaco <-> Sandpack Sync**:
    - When user edits in Monaco (Left), Sandpack (Right) updates.
    - *Challenge*: Debouncing to prevent re-render flashing.
- [ ] **File Mapping**:
    - Convert `ArtifactStore` files (flat list) to Sandpack `files` object (nested structure).

### 1.3 Visual Polish (The "Void" Theme)
- [ ] Customize Sandpack UI to match `Vertice Void` theme (`#050505`).
- [ ] Hide default Sandpack code editor (we use our superior Monaco).
- [ ] Add "Refresh", "Open in New Window" controls.

---

## 🗓️ PHASE 2: THE GUARDIAN INTERFACE
**Goal**: Make safety and governance VISIBLE.

### 2.1 Constitutional Feedback
- [ ] Overlay "Security Scanning..." state on Preview while code generates.
- [ ] If Guardian Agent blocks code (e.g., "Dangerous pattern"), show a **"Red Shield"** overlay on the preview instead of broken code.

### 2.2 Error Telemetry
- [ ] Capture runtime errors from Sandpack.
- [ ] Feed errors back to the Chat Context so Vertice AI can auto-fix them ("I see a runtime error, fixing...").

---

## 🗓️ PHASE 3: CLOUD UPLINK (The Bolt-Killer)
**Goal**: True backend execution.

### 3.1 The Terminal
- [ ] Integrate `xterm.js` into a bottom panel.
- [ ] Connect via WebSocket to `/api/v1/terminal` (to be implemented in Backend).

### 3.2 File Sync
- [ ] "Eject to Cloud": Button to deploy the current Sandpack state to the MCP persistence layer.

---

## 🛠️ IMPLEMENTATION SPECS (2026 Standards)

### Sandpack Tailwind Config
```javascript
// We must inject this into Sandpack to support Tailwind v4
const tailwindConfig = {
  files: {
    "/styles.css": {
      code: "@tailwind base;\n@tailwind components;\n@tailwind utilities;",
      active: true
    },
    "/tailwind.config.js": {
      code: "module.exports = { content: ['./**/*.{js,jsx,ts,tsx}'] }"
    }
  },
  customSetup: {
    dependencies: {
      "tailwindcss": "^4.0.0",
      "postcss": "^8.0.0",
      "autoprefixer": "^10.0.0"
    }
  }
}
```

### UX Micro-Interactions
- **Transition**: When switching from "Chat" to "Preview", use a `layoutId` animation (Framer Motion) to expand the preview pane.
- **Loading**: Use a "Constructing Reality..." skeleton loader that mimics the UI structure being built.

---

**Status**: Planning Complete.
**Ready for**: Phase 1 Execution.

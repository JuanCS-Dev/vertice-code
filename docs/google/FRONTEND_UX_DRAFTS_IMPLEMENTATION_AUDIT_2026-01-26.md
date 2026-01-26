# Frontend UX Drafts — Implementation Audit (2026-01-26)

## Goal
Validate whether the UX draft “agentic stream / CoT / command center” screens are **actually wired to real data**
in `apps/web-console`, or if they are mostly **static mocks**.

## Sources (Drafts)
- `docs/google/vertice-code-webapp-ui-ux/vertice_-_refined_agentic_stream_dashboard_1/code.html`
- `docs/google/vertice-code-webapp-ui-ux/vertice_-_refined_agentic_stream_dashboard_2/code.html`
- `docs/google/vertice-code-webapp-ui-ux/vertice_-_advanced_command_center/code.html`
- `docs/google/vertice-code-webapp-ui-ux/vertice_-_refined_cot_logic_stream/code.html`

## Sources (Implementation)
- `apps/web-console/app/dashboard/page.tsx`
- `apps/web-console/app/command-center/page.tsx`
- `apps/web-console/app/cot/page.tsx`
- `apps/web-console/app/api/gateway/stream/route.ts`
- `apps/web-console/lib/gateway.ts`

## Summary Table

| Draft | Route | UI parity (visual) | Logic parity (real wiring) | Notes |
|---|---:|---:|---:|---|
| Agentic Stream Dashboard (v1) | `/dashboard` | Medium | Partial | Visual shell similar, but v1-specific “plan/ADR cards + structured feed items” are not implemented. |
| Agentic Stream Dashboard (v2) | `/dashboard` | High | Partial | **Real SSE streaming exists**, but rendered as a **single text blob**, not as typed cards (intent/tool/code/context). |
| Advanced Command Center | `/command-center` | High | Mock | Page is static UI only (no fetch/SSE/state). |
| Refined CoT Logic Stream | `/cot` | High | Mock | Page is static timeline UI only (no fetch/SSE/state). |

## Findings (What is real vs mock)

### 1) `/dashboard` (Agentic Stream)
**What is real:**
- Client uses `fetch("/api/gateway/stream", { method: "POST", body: { prompt, session_id, agent } })` and consumes a
  streaming body reader (SSE-style frames split by `\n\n`). (`apps/web-console/app/dashboard/page.tsx`)
- Supports event types (parsed from `data: {json}`):
  - `delta` → appends `payload.data.text` to `streamText`
  - `final` → replaces `streamText`
  - `error` → throws
  - `tool` w/ `data.frame === "intent"` → extracts `run_id` into `lastRunId` (shown as “RUN: …”)
- `/api/gateway/stream` is a server proxy to the gateway upstream path `"/agui/stream"` and returns
  `Content-Type: text/event-stream`. (`apps/web-console/app/api/gateway/stream/route.ts`)

**What is currently mock / not wired (vs drafts):**
- The “Live Agent Feed” is not a list of structured cards; it’s a **single `<pre>`** containing `streamText`.
- Tool frames, intent blocks, per-agent attribution, timestamps, confidence badges, context/file chips, and
  mission trajectory/progress UI in the drafts are **not populated from real events**.
- Right-side “Code Preview” panel is **hard-coded example code**, not connected to the stream.
- “Session Metrics” (tokens/cost/speed) are **hard-coded**.

**Conclusion:** `/dashboard` is **partially real**: streaming transport exists and works, but the draft’s
“refined agentic feed” is **not implemented** (no typed event model rendered into cards).

### 2) `/command-center` (Tactical HUD)
- `apps/web-console/app/command-center/page.tsx` is a **static** page: no state, no API calls, no SSE.
- The mesh, agent list, bottom terminal, telemetry sections are visually present but **not driven by data**.

**Conclusion:** **Mock UI** (design-only).

### 3) `/cot` (Logic Stream)
- `apps/web-console/app/cot/page.tsx` is a **static** page: no state, no API calls, no SSE.
- The timeline is hard-coded demo content (steps, intent JSON, context tiles, etc.).

**Conclusion:** **Mock UI** (design-only).

## Validation (syntax/types/lint)
Executed in `apps/web-console`:
- `npx tsc --noEmit -p tsconfig.json` ✅
- `npx eslint app/dashboard/page.tsx app/command-center/page.tsx app/cot/page.tsx app/api/gateway/stream/route.ts` ✅

## Recommended “Base Wiring” Tasks (PR-sized, no new product features)
These are the minimal steps to make the UI behave closer to the drafts (still “frontend base”, not expanding scope):

1. **Extract a shared AGUI stream hook**
   - Create a single `useAguiStream()` (or equivalent) that:
     - parses SSE frames robustly (multi-line `data:` blocks, `event:` support),
     - normalizes payload into a typed union (delta/final/error/intent/tool/context/code/metrics).

2. **Render stream as structured cards**
   - Replace the single `<pre>` with a list renderer that maps normalized events into:
     - agent messages (with agent id + timestamp),
     - intent cards (JSON block),
     - tool call frames (name/args/result),
     - code blocks (language + copy button),
     - context links (file + line-range).

3. **Wire “Code Preview” to stream artifacts**
   - Add a simple in-memory “selected artifact” model that can be populated by stream events (e.g. a `tool` result
     containing file content), instead of a hard-coded snippet.

4. **Define a backend contract for CoT + telemetry**
   - Before wiring `/cot` and `/command-center`, define the minimal API shape(s) needed (even if proxied via the
     gateway like `/api/gateway/stream`).

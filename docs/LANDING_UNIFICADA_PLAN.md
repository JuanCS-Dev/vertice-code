# Plan Refactoring: Vertice-Code Unified Landing Page (2026 Edition)

**Status:** IN PROGRESS
**Date:** 2026-01-06
**Objective:** Refactor `@docs/LANDING_UNIFICADA_PLAN.md` to align with 2026 "Intelligent Minimalism" trends and the Claude Code Web aesthetic.

## 1. Design Philosophy Update: "Intelligent Minimalism" (2026 Trend)

The 2026 web design landscape, influenced by AI leaders (OpenAI, Perplexity, Anthropic), has shifted from "simple minimalism" to "intelligent minimalism".

**Key Characteristics for Vertice-Code:**
*   **Hyper-Functional Whitespace:** Whitespace isn't just empty; it guides cognitive flow.
*   **Adaptive Dark Mode:** The interface shouldn't just be "dark"; it should use deep, rich grays (e.g., `#0a0e1a` to `#161b2e`) rather than pure black to reduce eye strain and feel "premium".
*   **Typography-First Hierarchy:** Bold, purposeful headings (Sans-Serif) paired with highly legible Monospace for code/technical data.
*   **Micro-Interactions:** Subtle feedback on every interaction (hover, click, focus) to indicate "liveness".
*   **"Glassmorphism 2.0":** Very subtle, high-performance blurs used *only* for depth layering (e.g., the console overlay), not as decoration.

## 2. Refactored HTML Structure (Single-Page App Feel)

The structure will be flattened further to resemble a web app more than a marketing site.

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vertice-Code | Sovereign AI Agency</title>
    <!-- Preconnect to fonts -->
    <!-- Meta tags for SEO/Social -->
</head>
<body class="bg-primary text-primary antialiased selection:bg-accent selection:text-white">

    <!-- 1. Fixed Minimal Navbar (Glass) -->
    <nav class="fixed top-0 w-full z-50 border-b border-white/5 bg-primary/80 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <div class="w-6 h-6 bg-accent rounded-sm"></div> <!-- Minimal Logo Placeholder -->
                <span class="font-bold text-lg tracking-tight">Vertice-Code</span>
            </div>
            <div class="hidden md:flex gap-8 text-sm font-medium text-muted">
                <a href="#console" class="hover:text-white transition-colors">Console</a>
                <a href="#agents" class="hover:text-white transition-colors">Agents</a>
                <a href="#tools" class="hover:text-white transition-colors">Tools</a>
                <a href="/docs" class="hover:text-white transition-colors">Docs</a>
            </div>
            <div class="flex gap-4">
                <a href="https://github.com/juan-cs-dev/vertice-code" target="_blank" class="text-muted hover:text-white transition-colors">
                    <svg>...</svg> <!-- GitHub Icon -->
                </a>
            </div>
        </div>
    </nav>

    <main class="relative pt-32 pb-20">

        <!-- 2. Hero Section (Centered, Typography-Led) -->
        <section class="max-w-4xl mx-auto px-6 text-center mb-24">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-accent mb-8">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                v2.0.0 Stable
            </div>
            <h1 class="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
                The Sovereign <br />
                <span class="text-transparent bg-clip-text bg-gradient-to-r from-white to-white/50">Tactical Executor.</span>
            </h1>
            <p class="text-xl text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
                A unified multi-agent agency with constitutional governance.
                Orchestrating 20 agents and 85+ tools with millisecond latency.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <button onclick="scrollToConsole()" class="px-8 py-4 bg-white text-black font-bold rounded-lg hover:bg-gray-200 transition-all transform hover:scale-105">
                    Launch Console
                </button>
                <a href="/docs" class="px-8 py-4 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-all font-medium">
                    Read Documentation
                </a>
            </div>
        </section>

        <!-- 3. Integrated Live Console (The "Hero" Product Demo) -->
        <section id="console" class="max-w-6xl mx-auto px-6 mb-32">
            <div class="rounded-xl border border-white/10 bg-[#0f1219] shadow-2xl overflow-hidden relative group">
                <!-- Mac-like Window Header -->
                <div class="h-10 bg-white/5 border-b border-white/5 flex items-center px-4 gap-2">
                    <div class="flex gap-1.5">
                        <div class="w-3 h-3 rounded-full bg-red-500/20"></div>
                        <div class="w-3 h-3 rounded-full bg-yellow-500/20"></div>
                        <div class="w-3 h-3 rounded-full bg-green-500/20"></div>
                    </div>
                    <div class="ml-4 flex gap-4 text-xs font-mono text-muted">
                        <span class="text-accent border-b border-accent cursor-pointer">request.json</span>
                        <span class="hover:text-white cursor-pointer transition-colors">headers</span>
                    </div>
                    <div class="ml-auto flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-green-500"></span>
                        <span class="text-xs font-mono text-muted">Connected: Vertice-MCP</span>
                    </div>
                </div>

                <!-- Console Body (Split View) -->
                <div class="grid md:grid-cols-2 min-h-[500px] font-mono text-sm">
                    <!-- Left: Request Builder -->
                    <div class="p-6 border-r border-white/5 relative">
                        <div class="mb-4 flex justify-between items-center">
                            <span class="text-muted text-xs uppercase tracking-wider">Payload</span>
                            <select id="method-select" class="bg-transparent text-xs text-accent border-none focus:ring-0 cursor-pointer">
                                <option value="list">tools/list</option>
                                <option value="call">tools/call</option>
                                <option value="ping">ping</option>
                            </select>
                        </div>
                        <textarea id="request-editor" class="w-full h-[350px] bg-transparent text-white/90 resize-none outline-none font-mono" spellcheck="false">{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}</textarea>
                        <button id="execute-btn" class="absolute bottom-6 right-6 px-4 py-2 bg-accent text-white rounded hover:bg-accent-hover transition-colors shadow-lg flex items-center gap-2">
                            <span>Execute</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                        </button>
                    </div>

                    <!-- Right: Response Viewer -->
                    <div class="p-6 bg-[#0a0c10] relative">
                         <div class="mb-4 flex justify-between items-center">
                            <span class="text-muted text-xs uppercase tracking-wider">Response</span>
                            <span id="timing-badge" class="hidden text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded">45ms</span>
                        </div>
                        <pre id="response-viewer" class="text-green-400/90 overflow-auto h-[400px] scrollbar-hide">// Waiting for request...</pre>
                    </div>
                </div>
            </div>
        </section>

        <!-- 4. "Bento Grid" Features (Replacing Cards) -->
        <section id="features" class="max-w-6xl mx-auto px-6 mb-32">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Large Card -->
                <div class="md:col-span-2 p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <div class="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-6 text-accent">
                        <svg>...</svg> <!-- Network Icon -->
                    </div>
                    <h3 class="text-2xl font-bold mb-3">Multi-LLM Routing</h3>
                    <p class="text-muted leading-relaxed max-w-lg">
                        Intelligent traffic direction between Claude 3.5 Sonnet, Gemini 1.5 Pro, and Groq.
                        Optimizes for cost, speed, and capability per-token.
                    </p>
                </div>

                <!-- Tall Card -->
                <div class="md:row-span-2 p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/50 pointer-events-none"></div>
                    <h3 class="text-2xl font-bold mb-3 relative z-10">Constitutional<br>Governance</h3>
                    <div class="mt-8 space-y-4 font-mono text-xs text-muted relative z-10">
                        <div class="flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            JUSTIÇA Protocol Active
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            SOFIA Oversight: L3
                        </div>
                    </div>
                </div>

                <!-- Medium Card -->
                <div class="p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <h3 class="text-xl font-bold mb-2">85+ Tactical Tools</h3>
                    <p class="text-sm text-muted">Native integration with Git, Filesystem, Docker, and Web Search.</p>
                </div>

                 <!-- Medium Card -->
                 <div class="p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <h3 class="text-xl font-bold mb-2">MCP Native</h3>
                    <p class="text-sm text-muted">Full compliance with Model Context Protocol specification.</p>
                </div>
            </div>
        </section>

        <!-- 5. Minimal Footer -->
        <footer class="max-w-6xl mx-auto px-6 pt-12 pb-12 border-t border-white/5 flex flex-col md:flex-row justify-between items-center text-sm text-muted">
            <div>
                © 2026 Vertice-Code. <span class="opacity-50">Soli Deo Gloria.</span>
            </div>
            <div class="flex gap-6 mt-4 md:mt-0">
                <a href="#" class="hover:text-white transition-colors">Privacy</a>
                <a href="#" class="hover:text-white transition-colors">Terms</a>
                <a href="#" class="hover:text-white transition-colors">Status</a>
            </div>
        </footer>

    </main>

    <!-- Scripts -->
    <script src="landing/script-v2.js"></script>
</body>
</html>
```

## 3. Style Guide (CSS Variables)

To achieve the "Anthropic/OpenAI" look:

```css
:root {
    /* Backgrounds */
    --bg-primary: #0a0e1a;  /* Deep Navy/Black */
    --bg-secondary: #0f1219; /* Slightly lighter for cards */

    /* Text */
    --text-primary: #ffffff;
    --text-muted: #94a3b8;  /* Slate 400 */

    /* Accent */
    --accent: #06b6d4;      /* Cyan 500 */
    --accent-hover: #0891b2; /* Cyan 600 */

    /* Borders */
    --border-subtle: rgba(255, 255, 255, 0.05);

    /* Typography */
    --font-sans: 'Inter', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}
```

## 4. Interaction Logic (JavaScript)

The console needs to feel **real**.

1.  **Mock Network Delay:** Use `setTimeout` with random 50-150ms delay to simulate real network latency.
2.  **Typing Effect:** Stream the JSON response character-by-character (fast) to mimic LLM/Server streaming.
3.  **Dynamic Status:** Change the badge from "Connecting..." to "200 OK" (Green) or "500 Error" (Red).

**Quick Start Tabs Logic:**
- Simple class toggling (`hidden` vs `block`) for code snippets.
- "Copy to Clipboard" with a visual "Copied!" tooltip feedback.

## 5. Next Steps

1.  **Execute:** Write `landing/index-v2.html` with the structure above.
2.  **Style:** Write `landing/styles-v2.css` (using Tailwind CDN for prototyping or raw CSS with variables).
3.  **Script:** Write `landing/script-v2.js` implementing the console logic.
4.  **Verify:** Open in browser and check responsiveness.

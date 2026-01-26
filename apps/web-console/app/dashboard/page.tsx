"use client";

import Link from "next/link";
import { useCallback, useMemo, useRef, useState } from "react";

type AGUIEventPayload = {
  type: string;
  session_id?: string;
  data?: Record<string, unknown>;
};

function parseSseBlock(block: string): AGUIEventPayload | null {
  const lines = block.split("\n").filter(Boolean);
  const dataLine = lines.find((l) => l.startsWith("data: "));
  if (!dataLine) return null;
  const raw = dataLine.slice("data: ".length);
  try {
    return JSON.parse(raw) as AGUIEventPayload;
  } catch {
    return null;
  }
}

export default function Dashboard() {
  const [prompt, setPrompt] = useState("");
  const [streamText, setStreamText] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sessionId = useMemo(() => {
    return globalThis.crypto?.randomUUID?.() ?? `s-${Date.now()}`;
  }, []);

  const send = useCallback(async () => {
    const trimmed = prompt.trim();
    if (!trimmed || busy) return;

    setBusy(true);
    setStreamText("");
    setLastRunId(null);

    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    try {
      const res = await fetch("/api/gateway/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: trimmed, session_id: sessionId, agent: "coder" }),
        signal: ac.signal,
      });
      if (!res.ok || !res.body) {
        const t = await res.text().catch(() => "");
        throw new Error(t || `gateway error (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        while (buffer.includes("\n\n")) {
          const idx = buffer.indexOf("\n\n");
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const payload = parseSseBlock(block);
          if (!payload) continue;

          if (payload.type === "tool" && payload.data?.frame === "intent") {
            const runId = typeof payload.data?.run_id === "string" ? payload.data.run_id : null;
            if (runId) setLastRunId(runId);
          }

          if (payload.type === "delta") {
            const text = typeof payload.data?.text === "string" ? payload.data.text : "";
            if (text) setStreamText((t) => t + text);
          } else if (payload.type === "final") {
            const text = typeof payload.data?.text === "string" ? payload.data.text : "";
            if (text) setStreamText(text);
            return;
          } else if (payload.type === "error") {
            const msg = typeof payload.data?.message === "string" ? payload.data.message : "error";
            throw new Error(msg);
          }
        }
      }
    } finally {
      setBusy(false);
    }
  }, [busy, prompt, sessionId]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setBusy(false);
  }, []);

  return (
    <div className="bg-background-light dark:bg-obsidian min-h-screen flex flex-col font-display text-white selection:bg-primary/30">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-border-dim bg-panel/90 backdrop-blur-md px-6 py-3">
        <div className="flex items-center gap-4">
          <Link href="/" className="size-8 text-primary flex items-center justify-center">
            <svg className="w-full h-full" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z" fill="currentColor"></path>
              <path clipRule="evenodd" d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z" fill="currentColor" fillRule="evenodd"></path>
            </svg>
          </Link>
          <h2 className="text-white text-xl font-bold leading-tight tracking-tight">Vertice</h2>
          <div className="h-6 w-px bg-border-dim mx-2"></div>
          <div className="flex gap-1">
            <Link
              href="/dashboard"
              className="px-4 py-1.5 rounded-lg bg-panel border border-border-dim/50 text-white text-sm font-medium hover:bg-border-dim/50 transition-colors shadow-[0_0_8px_rgba(0,229,255,0.2)]"
            >
              Stream
            </Link>
            <Link
              href="/command-center"
              className="px-4 py-1.5 rounded-lg text-gray-400 text-sm font-medium hover:text-white hover:bg-border-dim/30 transition-colors"
            >
              Command Center
            </Link>
            <Link
              href="/cot"
              className="px-4 py-1.5 rounded-lg text-gray-400 text-sm font-medium hover:text-white hover:bg-border-dim/30 transition-colors"
            >
              CoT
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-panel border border-border-dim">
            <span className="size-2 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-xs font-mono text-gray-300">SYSTEM: ONLINE</span>
          </div>
          <div className="h-6 w-px bg-border-dim"></div>
          <Link href="/settings" className="text-gray-400 hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-xl">settings</span>
          </Link>
          <button className="text-gray-400 hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-xl">notifications</span>
          </button>
          <div className="bg-center bg-no-repeat bg-cover rounded-full size-8 ring-2 ring-border-dim" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuA7RWKvzmF_kiRiWphbsVsIWdgmxF29jeowRyFyqZFmvP1KSj75LJbJ9isbGpVRNHyL0H_0Dt4Da7Chw4ovw3sRu_dfDvRBK2Ldfme_VLI5QW0dl9qeg49WnYpDEZMCh4pcre-BghhqaR0JIz8tbN0fq7DY5RXGC50rUtg3i5cvOQoXab7l5SK-E2eSTs_TVSeswBritNRPpqeWqN7ctsu8sGncxL5FePJcuVTV2XeM2cMz9UIKXH2w5WYfv7o5ndtyvKaz9XiSlj1a')" }}></div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden p-4 gap-4 h-[calc(100vh-64px)]">
        {/* Left Sidebar */}
        <aside className="w-80 flex flex-col gap-4 min-w-[320px] max-w-[320px]">
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 flex-1 rounded-xl flex flex-col overflow-hidden">
            <div className="p-4 border-b border-border-dim flex justify-between items-center">
              <h2 className="text-white text-lg font-bold tracking-tight">Mission Objectives</h2>
              <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">3 Active</span>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-2 no-scrollbar">
              <div className="p-3 bg-panel/50 rounded-lg border border-border-dim/50 mb-4">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs text-gray-400 font-medium">EPIC PROGRESS</span>
                  <span className="text-sm font-bold text-primary">65%</span>
                </div>
                <div className="h-1.5 w-full bg-panel-light rounded-full overflow-hidden">
                  <div className="h-full bg-primary shadow-[0_0_15px_rgba(0,229,255,0.15)] w-[65%] rounded-full"></div>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 px-2 py-1 text-gray-300 hover:text-white cursor-pointer group">
                  <span className="material-symbols-outlined text-lg transition-transform group-hover:rotate-90">arrow_right</span>
                  <span className="text-sm font-semibold">Authentication System</span>
                </div>
                <div className="pl-4 space-y-1 border-l border-border-dim ml-3.5">
                  <div className="flex items-start gap-3 p-2 rounded hover:bg-panel transition-colors group">
                    <span className="material-symbols-outlined text-green-500 text-lg mt-0.5">check_circle</span>
                    <div>
                      <p className="text-sm text-gray-400 line-through group-hover:text-gray-300">Design Login Schema</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-2 rounded bg-panel border border-primary/30 shadow-[0_0_8px_rgba(0,229,255,0.2)] relative overflow-hidden">
                    <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-primary"></div>
                    <span className="material-symbols-outlined text-primary text-lg mt-0.5 animate-spin">sync</span>
                    <div>
                      <p className="text-sm text-white font-medium">Generate API Routes</p>
                      <span className="text-[10px] text-primary uppercase tracking-wider font-mono mt-1 block">Processing...</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-2 rounded hover:bg-panel transition-colors opacity-60">
                    <span className="material-symbols-outlined text-gray-600 text-lg mt-0.5">radio_button_unchecked</span>
                    <div>
                      <p className="text-sm text-gray-300">Frontend Integration</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-1 mt-4">
                <div className="flex items-center gap-2 px-2 py-1 text-gray-300 hover:text-white cursor-pointer group">
                  <span className="material-symbols-outlined text-lg transition-transform group-hover:rotate-90">arrow_right</span>
                  <span className="text-sm font-semibold">Database Migration</span>
                </div>
                <div className="pl-4 space-y-1 border-l border-border-dim ml-3.5">
                  <div className="flex items-start gap-3 p-2 rounded hover:bg-panel transition-colors opacity-60">
                    <span className="material-symbols-outlined text-gray-600 text-lg mt-0.5">radio_button_unchecked</span>
                    <div>
                      <p className="text-sm text-gray-300">Schema Validation</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 rounded-xl p-3 flex flex-col gap-2 relative overflow-hidden group border-primary/30 shadow-[0_0_8px_rgba(0,229,255,0.2)] flex-none">
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            <div className="flex justify-between items-center px-1">
              <span className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">person</span>
                Operator
              </span>
              <span className="size-1.5 bg-primary rounded-full animate-pulse"></span>
            </div>
            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full bg-panel-light/50 border border-border-dim rounded-lg p-2 text-xs text-white placeholder-gray-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none h-24 no-scrollbar font-mono"
                placeholder="Type a command..."
              ></textarea>
              <div className="absolute bottom-2 right-2 flex gap-1">
                <button className="p-1 rounded hover:bg-panel text-gray-400 hover:text-white transition-colors" title="Attach context">
                  <span className="material-symbols-outlined text-[16px]">attach_file</span>
                </button>
                <button
                  onClick={send}
                  disabled={busy}
                  className="p-1 rounded bg-primary text-panel hover:bg-primary/90 transition-colors disabled:opacity-60"
                  title="Send command"
                >
                  <span className="material-symbols-outlined text-[16px]">arrow_upward</span>
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Stream Area */}
        <section className="flex-1 flex flex-col gap-4 min-w-[400px]">
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 flex-1 rounded-xl flex flex-col overflow-hidden relative">
            <div className="p-4 border-b border-border-dim bg-panel/80 backdrop-blur sticky top-0 z-10 flex justify-between items-center">
              <h2 className="text-white text-lg font-bold tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">stream</span>
                Live Agent Feed
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={stop}
                  disabled={!busy}
                  className="text-xs bg-panel-light hover:bg-border-dim text-gray-400 px-3 py-1.5 rounded transition-colors border border-border-dim disabled:opacity-60"
                >
                  Stop
                </button>
                <button
                  onClick={() => setStreamText("")}
                  className="text-xs bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 rounded transition-colors border border-primary/20"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar relative">
              <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: "radial-gradient(#ffffff 1px, transparent 1px)", backgroundSize: "20px 20px" }}>
              </div>
              <div className="bg-panel/80 border border-border-dim/50 rounded-xl p-4 relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs font-mono text-gray-400">
                    SESSION: {sessionId.slice(0, 8)} {lastRunId ? `// RUN: ${lastRunId.slice(0, 8)}` : ""}
                  </div>
                  <div className="text-xs font-mono text-gray-400">{busy ? "STREAMING..." : "IDLE"}</div>
                </div>
                <pre className="text-sm font-mono text-gray-200 whitespace-pre-wrap leading-relaxed min-h-[200px]">
                  {streamText || (busy ? "…" : "Send a command to start streaming.")}
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* Right Sidebar */}
        <aside className="w-[420px] flex flex-col gap-4 min-w-[380px] hidden xl:flex">
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 flex-1 rounded-xl flex flex-col overflow-hidden">
            <div className="p-3 border-b border-border-dim bg-panel/90 flex justify-between items-center">
              <div className="flex items-center gap-2 overflow-hidden">
                <span className="material-symbols-outlined text-gray-400 text-sm">description</span>
                <span className="text-sm font-mono text-white truncate">api/routes/auth.ts</span>
                <span className="size-1.5 bg-yellow-500 rounded-full ml-1" title="Unsaved changes"></span>
              </div>
              <div className="flex bg-panel-light p-0.5 rounded-lg border border-border-dim">
                <button className="px-3 py-1 rounded text-xs font-medium bg-border-dim text-white shadow-sm">Code</button>
                <button className="px-3 py-1 rounded text-xs font-medium text-gray-400 hover:text-white transition-colors">Preview</button>
              </div>
            </div>
            <div className="flex-1 bg-[#0d1117] p-4 font-mono text-sm overflow-y-auto overflow-x-auto relative">
              <div className="absolute left-0 top-4 bottom-0 w-8 text-right pr-2 text-gray-600 select-none text-xs leading-6">
                1<br />2<br />3<br />4<br />5<br />6<br />7<br />8<br />9<br />10<br />11<br />12
              </div>
              <div className="pl-8 leading-6 text-gray-300">
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">
                  <span className="text-[#ff7b72]">import</span> {"{"} Router {"}"}{" "}
                  <span className="text-[#ff7b72]">from</span>{" "}
                  <span className="text-[#a5d6ff]">&apos;express&apos;</span>;
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">
                  <span className="text-[#ff7b72]">import</span> {"{"} AuthController {"}"}{" "}
                  <span className="text-[#ff7b72]">from</span>{" "}
                  <span className="text-[#a5d6ff]">&apos;../controllers/auth&apos;</span>;
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">&nbsp;</div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors"><span className="text-[#ff7b72]">const</span> router = Router();</div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">&nbsp;</div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">
                  <span className="text-[#8b949e]">{"// Authenticate user route"}</span>
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors bg-primary/10 border-l-2 border-primary relative">
                  router.<span className="text-[#d2a8ff]">post</span>(
                  <span className="text-[#a5d6ff]">&apos;/login&apos;</span>, AuthController.login);
                  <span className="absolute right-2 top-1.5 size-2 bg-primary rounded-full animate-ping"></span>
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">
                  router.<span className="text-[#d2a8ff]">post</span>(
                  <span className="text-[#a5d6ff]">&apos;/register&apos;</span>, AuthController.register);
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">
                  router.<span className="text-[#d2a8ff]">post</span>(
                  <span className="text-[#a5d6ff]">&apos;/refresh-token&apos;</span>, AuthController.refresh);
                </div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors">&nbsp;</div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors"><span className="text-[#ff7b72]">export</span> <span className="text-[#ff7b72]">default</span> router;</div>
                <div className="group hover:bg-white/5 -mx-4 px-4 transition-colors"><span className="text-primary animate-pulse">|</span></div>
              </div>
            </div>
            <div className="p-2 border-t border-border-dim bg-panel flex justify-between items-center text-xs">
              <span className="text-gray-400">TypeScript • UTF-8</span>
              <div className="flex gap-2">
                <button className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors">
                  <span className="material-symbols-outlined text-sm">content_copy</span> Copy
                </button>
                <button className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors font-bold">
                  <span className="material-symbols-outlined text-sm">play_arrow</span> Run Test
                </button>
              </div>
            </div>
          </div>
          <div className="h-32 bg-panel/70 backdrop-blur-md border border-border-dim/50 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <h3 className="text-sm font-bold text-gray-300">Session Metrics</h3>
              <span className="material-symbols-outlined text-gray-500 text-sm">bar_chart</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-panel-light rounded p-2 border border-border-dim">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Tokens</div>
                <div className="text-lg font-mono font-bold text-white">4.2k</div>
              </div>
              <div className="bg-panel-light rounded p-2 border border-border-dim">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Cost</div>
                <div className="text-lg font-mono font-bold text-white">$0.12</div>
              </div>
              <div className="bg-panel-light rounded p-2 border border-border-dim">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Speed</div>
                <div className="text-lg font-mono font-bold text-primary">High</div>
              </div>
            </div>
          </div>
        </aside>
      </main>

      <footer className="h-8 bg-panel-light border-t border-border-dim flex items-center justify-between px-4 text-[10px] font-mono text-gray-500 select-none">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5"><div className="size-1.5 rounded-full bg-primary"></div> Connected to us-east-1</span>
          <span>Vertice Core v2.4.0</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hover:text-white cursor-pointer transition-colors">Shortcuts: ⌘K</span>
          <span className="hover:text-white cursor-pointer transition-colors">Help</span>
        </div>
      </footer>
    </div>
  );
}

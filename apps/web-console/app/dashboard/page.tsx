"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { useAguiStream, ToolCall } from "../../lib/hooks/useAguiStream";
import { StreamFeed } from "../../components/dashboard/StreamFeed";
import { FileCode, Activity, Database, Shield } from "lucide-react";

export default function Dashboard() {
  const [prompt, setPrompt] = useState("");
  const [selectedTool, setSelectedTool] = useState<ToolCall | null>(null);

  const { state, connect, stop, isStreaming } = useAguiStream();

  const sessionId = useMemo(() => {
    return globalThis.crypto?.randomUUID?.() ?? `s-${Date.now()}`;
  }, []);

  const send = useCallback(() => {
    const trimmed = prompt.trim();
    if (!trimmed || isStreaming) return;

    // Auto-select nothing on new run
    setSelectedTool(null);

    connect("/api/gateway/stream", {
      prompt: trimmed,
      session_id: sessionId,
      agent: "coder"
    });
  }, [prompt, isStreaming, sessionId, connect]);

  // Derive "Active Code Tool" if none selected?
  // Strategy: If a tool is writing code, select it automatically if nothing is selected?
  // For now, simple manual selection via feed.

  return (
    <div className="bg-background-light dark:bg-obsidian min-h-screen flex flex-col font-display text-white selection:bg-primary/30">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-border-dim bg-panel/90 backdrop-blur-md px-6 py-3">
        <div className="flex items-center gap-4">
          <Link href="/" className="size-8 text-primary flex items-center justify-center">
            <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-black font-bold text-xl">V</div>
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
            <Link href="/command-center" className="px-4 py-1.5 rounded-lg text-gray-400 text-sm font-medium hover:text-white hover:bg-border-dim/30 transition-colors">Command Center</Link>
            <Link href="/cot" className="px-4 py-1.5 rounded-lg text-gray-400 text-sm font-medium hover:text-white hover:bg-border-dim/30 transition-colors">CoT</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded bg-panel border border-border-dim`}>
            <span className={`size-2 rounded-full ${isStreaming ? "bg-primary animate-pulse" : "bg-green-500"}`}></span>
            <span className="text-xs font-mono text-gray-300">{isStreaming ? "SYSTEM: BUSY" : "SYSTEM: ONLINE"}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden p-4 gap-4 h-[calc(100vh-64px)]">
        {/* Left Sidebar - Input and Context */}
        <aside className="w-80 flex flex-col gap-4 min-w-[320px] max-w-[320px]">
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 flex-1 rounded-xl flex flex-col overflow-hidden p-3 gap-2">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <Shield size={14} />
              <span className="text-xs font-bold uppercase tracking-wider">Mission Control</span>
            </div>

            {/* Simple list of recent events or status? Keeping it clean for M2 */}
            <div className="flex-1 overflow-y-auto no-scrollbar space-y-2">
              {/* Placeholder for "Mission Objectives" - connected to real runs in future */}
              <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                <div className="text-xs text-gray-400 mb-1">CURRENT SESSION</div>
                <div className="font-mono text-xs text-primary truncate">{sessionId}</div>
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 rounded-xl p-3 flex flex-col gap-2 relative overflow-hidden group border-primary/30 shadow-[0_0_8px_rgba(0,229,255,0.2)] flex-none">
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            <div className="flex justify-between items-center px-1">
              <span className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">person</span>
                Operator
              </span>
            </div>
            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                className="w-full bg-panel-light/50 border border-border-dim rounded-lg p-2 text-xs text-white placeholder-gray-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none h-24 no-scrollbar font-mono"
                placeholder="Type a command..."
                disabled={isStreaming}
              ></textarea>
              <div className="absolute bottom-2 right-2 flex gap-1">
                <button
                  onClick={send}
                  disabled={isStreaming || !prompt.trim()}
                  className="p-1 rounded bg-primary text-panel hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
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
                <Activity size={18} className="text-primary" />
                Live Agent Feed
              </h2>
              <div className="flex gap-2">
                {isStreaming && (
                  <button
                    onClick={stop}
                    className="text-xs bg-red-500/10 hover:bg-red-500/20 text-red-500 px-3 py-1.5 rounded transition-colors border border-red-500/20"
                  >
                    Stop
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto no-scrollbar relative bg-black/20">
              <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: "radial-gradient(#ffffff 1px, transparent 1px)", backgroundSize: "20px 20px" }}></div>
              <StreamFeed state={state} onToolSelect={setSelectedTool} />
            </div>
          </div>
        </section>

        {/* Right Sidebar - Code Preview */}
        <aside className="w-[420px] flex flex-col gap-4 min-w-[380px] hidden xl:flex">
          <div className="bg-panel/70 backdrop-blur-md border border-border-dim/50 flex-1 rounded-xl flex flex-col overflow-hidden">
            <div className="p-3 border-b border-border-dim bg-panel/90 flex justify-between items-center">
              <div className="flex items-center gap-2 overflow-hidden">
                <FileCode size={16} className="text-gray-400" />
                <span className="text-sm font-mono text-white truncate">
                  {selectedTool ? `Tool Output: ${selectedTool.name}` : "No tool selected"}
                </span>
              </div>
            </div>
            <div className="flex-1 bg-[#0d1117] p-4 font-mono text-sm overflow-y-auto overflow-x-auto relative text-gray-300 leading-relaxed">
              {selectedTool ? (
                <>
                  {selectedTool.code ? (
                    <pre>{selectedTool.code}</pre>
                  ) : selectedTool.result ? (
                    <pre className="whitespace-pre-wrap">{JSON.stringify(selectedTool.result, null, 2)}</pre>
                  ) : (
                    <div className="text-gray-600 italic">Executing...</div>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
                  <Database size={24} />
                  <span>Select a tool call card to view details</span>
                </div>
              )}
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

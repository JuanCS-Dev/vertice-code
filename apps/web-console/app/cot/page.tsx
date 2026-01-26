"use client";

import Link from "next/link";

export default function CotStream() {
  return (
    <div className="bg-background-light dark:bg-background-dark font-display text-white overflow-hidden h-screen flex flex-col selection:bg-primary/30 selection:text-primary">
      {/* Header */}
      <header className="flex shrink-0 items-center justify-between whitespace-nowrap border-b border-border-color bg-surface-dark/80 backdrop-blur-md px-6 py-3 z-30">
        <div className="flex items-center gap-12">
          <div className="flex items-center gap-3 text-white">
            <Link href="/" className="size-8 text-primary flex items-center justify-center relative">
              <div className="absolute inset-0 bg-primary/20 blur-md rounded-full"></div>
              <span className="material-symbols-outlined text-3xl relative z-10">token</span>
            </Link>
            <h2 className="text-white text-xl font-bold tracking-tight">Vertice Code Web</h2>
          </div>
          <nav className="hidden md:flex items-center bg-[#020617]/50 p-1 rounded-lg border border-border-color">
            <Link href="/dashboard" className="px-5 py-1.5 text-sm font-medium text-text-muted hover:text-white rounded-md transition-all hover:bg-white/5">Stream</Link>
            <Link href="/command-center" className="px-5 py-1.5 text-sm font-medium text-text-muted hover:text-white rounded-md transition-all hover:bg-white/5">Command Center</Link>
            <Link href="/cot" className="px-5 py-1.5 text-sm font-bold text-black bg-primary rounded-md shadow-[0_0_15px_rgba(0,240,255,0.4)] transition-all">CoT</Link>
          </nav>
        </div>
        <div className="flex items-center gap-6">
          <label className="hidden lg:flex flex-col min-w-40 w-64 h-9">
            <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-[#020617]/50 border border-border-color focus-within:border-primary/50 focus-within:shadow-[0_0_10px_rgba(0,240,255,0.1)] transition-all">
              <div className="text-text-muted flex items-center justify-center pl-3">
                <span className="material-symbols-outlined text-[18px]">search</span>
              </div>
              <input className="w-full bg-transparent border-none text-xs text-white focus:ring-0 placeholder:text-text-muted/50 px-3 font-normal focus:outline-none" placeholder="Search resources..." />
            </div>
          </label>
          <div className="bg-center bg-no-repeat bg-cover rounded-full size-9 border border-border-color ring-2 ring-transparent hover:ring-primary/50 transition-all cursor-pointer" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCp49y2oVzIcsZeNkM3YCbmn6Xonwf3W-dxABf668lpwLquMrr3Xjo5UuVqAvxDX_wr6VHD5prVBzqHe7FDqIl1UhUgMpHqKiFk2apKB-8wCzVrT_6htrbMBloK3yufGajUvIGRVRkiQmDZct7z4gZiUeHUNeYw1lz0fQ8Gkv1XAQROehKwWpoQlngshXl_Hw8Z1iV9GwP-u3_tbcjEHxL0krd85Yi5ebUyA_7em9e0hfq37-YbYVrw5ShPbcyzOJMTG_KeVffH9vwG')" }}></div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden relative">
        {/* Background Effects */}
        <div className="absolute inset-0 z-0 bg-matrix-pattern opacity-30 pointer-events-none bg-[length:50px_50px]"></div>
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-background-dark/0 via-background-dark/80 to-background-dark pointer-events-none"></div>

        {/* Sidebar */}
        <aside className="hidden lg:flex w-72 flex-col justify-between bg-surface-dark/40 backdrop-blur-md border-r border-border-color z-10">
          <div className="flex flex-col h-full">
            <div className="p-5 border-b border-border-color bg-surface-dark/50">
              <div className="flex items-center justify-between mb-1">
                <h1 className="text-white text-base font-bold">Session #8X92</h1>
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary shadow-[0_0_5px_#00f0ff]"></span>
                  </span>
                  <span className="text-primary text-[10px] font-mono font-bold tracking-wider">LIVE</span>
                </div>
              </div>
              <p className="text-text-muted text-xs">Unified Agentic Workflow</p>
            </div>
            <div className="p-4 flex flex-col gap-6 overflow-y-auto">
              <div>
                <div className="text-text-subtle text-[10px] font-bold uppercase tracking-widest mb-3 pl-1">Mission Objectives</div>
                <div className="flex flex-col gap-2">
                  <a className="flex items-center gap-3 px-3 py-3 rounded-lg bg-primary/10 border border-primary/30 text-white group transition-all relative overflow-hidden" href="#">
                    <div className="absolute inset-y-0 left-0 w-1 bg-primary"></div>
                    <span className="material-symbols-outlined text-primary text-[20px]">code</span>
                    <div className="flex flex-col">
                      <span className="text-xs font-bold font-mono">utils.ts</span>
                      <span className="text-[10px] text-primary/70">Refactoring Logic</span>
                    </div>
                  </a>
                  <a className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-muted hover:bg-white/5 hover:text-white transition-colors border border-transparent hover:border-border-color" href="#">
                    <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                    <span className="text-xs font-medium">Agent: Architect</span>
                  </a>
                  <a className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-muted hover:bg-white/5 hover:text-white transition-colors border border-transparent hover:border-border-color" href="#">
                    <span className="material-symbols-outlined text-[20px]">memory</span>
                    <span className="text-xs font-medium">Memory Stack</span>
                  </a>
                </div>
              </div>
              <div className="bg-[#020617]/60 rounded-xl p-4 border border-border-color relative overflow-hidden group">
                <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                <div className="flex justify-between items-end mb-2 relative z-10">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-text-subtle uppercase font-bold tracking-wider">Token Usage</span>
                    <span className="text-xs text-white mt-0.5">Session Total</span>
                  </div>
                  <span className="text-sm text-primary font-mono font-bold drop-shadow-[0_0_5px_rgba(0,240,255,0.5)]">2,405</span>
                </div>
                <div className="w-full bg-[#1e293b] rounded-full h-1 overflow-hidden relative z-10">
                  <div className="bg-primary h-1 rounded-full shadow-[0_0_10px_#00f0ff]" style={{ width: "45%" }}></div>
                </div>
              </div>
            </div>
            <div className="p-4 border-t border-border-color mt-auto bg-surface-dark/30">
              <button className="w-full flex items-center justify-center gap-2 text-xs text-text-muted hover:text-white transition-colors py-2 rounded hover:bg-white/5">
                <span className="material-symbols-outlined text-sm">logout</span>
                Disconnect Session
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative z-10 overflow-hidden bg-background-dark/50">
          <div className="shrink-0 border-b border-border-color bg-surface-dark/60 backdrop-blur-md p-6 flex flex-col gap-5">
            <div className="flex flex-wrap justify-between items-start gap-4">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="material-symbols-outlined text-primary animate-pulse-slow">schema</span>
                  <h1 className="text-2xl font-bold text-white tracking-tight">Logic Stream Visualization</h1>
                </div>
                <p className="text-text-muted text-sm pl-9">Real-time reasoning trace & decision matrix.</p>
              </div>
              <div className="flex gap-2">
                <button className="bg-primary text-black hover:bg-white hover:text-black transition-colors rounded-lg h-9 px-4 text-xs font-bold uppercase tracking-wide flex items-center gap-2 shadow-[0_0_15px_rgba(0,240,255,0.25)] hover:shadow-[0_0_20px_rgba(0,240,255,0.5)]">
                  <span className="material-symbols-outlined filled text-[18px]">pause</span>
                  Pause Stream
                </button>
                <button className="bg-[#1e293b] border border-border-color text-text-muted hover:text-white hover:border-primary/50 transition-colors rounded-lg h-9 w-9 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">skip_next</span>
                </button>
                <Link
                  href="/settings"
                  className="bg-[#1e293b] border border-border-color text-text-muted hover:text-white hover:border-primary/50 transition-colors rounded-lg h-9 w-9 flex items-center justify-center"
                >
                  <span className="material-symbols-outlined text-[20px]">settings</span>
                </Link>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap pl-9">
              <button className="flex h-7 items-center gap-2 rounded-full bg-primary/10 border border-primary/30 px-3 hover:bg-primary/20 transition-colors group">
                <span className="material-symbols-outlined text-primary text-[16px] group-hover:drop-shadow-[0_0_5px_#00f0ff]">visibility</span>
                <span className="text-primary text-xs font-bold group-hover:drop-shadow-[0_0_5px_#00f0ff]">Show Context</span>
              </button>
              <button className="flex h-7 items-center gap-2 rounded-full bg-surface-card border border-border-color px-3 hover:border-text-muted transition-colors">
                <span className="material-symbols-outlined text-text-muted text-[16px]">error</span>
                <span className="text-text-muted text-xs font-medium">Show Errors</span>
              </button>
              <button className="flex h-7 items-center gap-2 rounded-full bg-surface-card border border-border-color px-3 hover:border-text-muted transition-colors">
                <span className="material-symbols-outlined text-text-muted text-[16px]">terminal</span>
                <span className="text-text-muted text-xs font-medium">Raw Output</span>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 md:p-10 scroll-smooth relative">
            <div className="max-w-4xl mx-auto relative pl-4 pb-20">
              <div className="absolute left-[27px] top-4 bottom-0 w-px bg-gradient-to-b from-primary via-[#0f172a] to-transparent shadow-[0_0_8px_rgba(0,240,255,0.6)]"></div>

              {/* Step 1 */}
              <div className="relative flex gap-8 mb-12 group">
                <div className="relative z-10 flex flex-col items-center">
                  <div className="size-6 rounded-full bg-primary shadow-[0_0_15px_rgba(0,240,255,0.8)] flex items-center justify-center ring-4 ring-background-dark">
                    <span className="material-symbols-outlined text-black text-[14px] font-bold">check</span>
                  </div>
                  <div className="mt-2 text-[10px] font-mono text-primary drop-shadow-[0_0_5px_rgba(0,240,255,0.8)]">00:01s</div>
                </div>
                <div className="flex-1 bg-surface-card/40 backdrop-blur-sm border border-border-color rounded-xl p-5 hover:border-primary/40 hover:shadow-[0_0_30px_-10px_rgba(0,240,255,0.1)] transition-all duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary text-xl">psychology</span>
                      <h3 className="text-lg font-bold text-white">User Intent Analysis</h3>
                    </div>
                    <span className="bg-[#020617] border border-border-color text-primary text-[10px] px-2 py-1 rounded font-mono shadow-[0_0_10px_rgba(0,240,255,0.1)]">CONFIDENCE: 98%</span>
                  </div>
                  <p className="text-text-muted text-sm">Identified request to optimize sorting algorithm in <code className="text-primary bg-primary/10 px-1 rounded border border-primary/20">utils.ts</code>.</p>
                  <div className="mt-4 pt-3 border-t border-border-color hidden group-hover:block animate-fade-in">
                    <p className="text-[10px] text-text-subtle uppercase tracking-widest mb-1">Extracted Intent</p>
                    <div className="font-mono text-xs text-primary/80 bg-[#020617] p-3 rounded border border-border-color shadow-inner">
                      &quot;optimize_sort_complexity&quot;: <span className="text-[#a5f3fc]">true</span>,<br />
                      &quot;target_file&quot;:{" "}
                      <span className="text-[#a5f3fc]">&quot;src/core/logic/utils.ts&quot;</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="relative flex gap-8 mb-12 group">
                <div className="relative z-10 flex flex-col items-center">
                  <div className="size-6 rounded-full bg-surface-dark border-2 border-primary flex items-center justify-center ring-4 ring-background-dark shadow-[0_0_10px_rgba(0,240,255,0.3)]">
                    <div className="size-2 bg-primary rounded-full shadow-[0_0_5px_#00f0ff]"></div>
                  </div>
                  <div className="mt-2 text-[10px] font-mono text-text-muted">00:04s</div>
                </div>
                <div className="flex-1 bg-surface-card/40 backdrop-blur-sm border-l-2 border-l-primary border-y border-r border-y-border-color border-r-border-color rounded-r-xl rounded-l-sm p-0 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)]">
                  <div className="p-5 border-b border-border-color flex justify-between items-center bg-white/5">
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-text-muted text-xl group-hover:text-primary transition-colors">folder_open</span>
                      <h3 className="text-lg font-bold text-white">Context Retrieval</h3>
                    </div>
                    <span className="text-xs text-text-subtle bg-[#020617] px-2 py-0.5 rounded border border-border-color">2 references loaded</span>
                  </div>
                  <div className="p-5 bg-[#020617]/30">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-[#0f172a] rounded-lg p-3 border border-border-color hover:border-primary/50 hover:shadow-[0_0_15px_rgba(0,240,255,0.1)] transition-all cursor-pointer group/file">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm text-primary">description</span>
                            <span className="text-sm font-mono text-white">utils.ts</span>
                          </div>
                          <span className="text-[10px] text-text-muted">Line 45-89</span>
                        </div>
                        <div className="font-mono text-[10px] text-text-subtle overflow-hidden whitespace-nowrap text-ellipsis opacity-60 group-hover/file:opacity-100 group-hover/file:text-primary/70 transition-colors">
                          export const bubbleSort = (arr: number[])...
                        </div>
                      </div>
                      <div className="bg-[#0f172a] rounded-lg p-3 border border-border-color hover:border-primary/50 hover:shadow-[0_0_15px_rgba(0,240,255,0.1)] transition-all cursor-pointer group/file">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm text-primary">library_books</span>
                            <span className="text-sm font-mono text-white">Algo Docs</span>
                          </div>
                          <span className="text-[10px] text-text-muted">External</span>
                        </div>
                        <div className="font-mono text-[10px] text-text-subtle overflow-hidden whitespace-nowrap text-ellipsis opacity-60 group-hover/file:opacity-100 group-hover/file:text-primary/70 transition-colors">
                          ref: sorting-complexity-guidelines.md
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="relative flex gap-8 mb-12">
                <div className="relative z-10 flex flex-col items-center">
                  <div className="relative size-6 flex items-center justify-center ring-4 ring-background-dark rounded-full">
                    <div className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-40"></div>
                    <div className="relative inline-flex rounded-full h-4 w-4 bg-primary shadow-[0_0_15px_#00f0ff]"></div>
                  </div>
                  <div className="mt-2 text-[10px] font-mono text-primary font-bold animate-pulse">NOW</div>
                </div>
                <div className="flex-1 relative">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-primary via-primary/50 to-transparent rounded-xl opacity-20 blur-md"></div>
                  <div className="relative bg-surface-dark/80 backdrop-blur-md border border-primary/50 rounded-xl p-6 shadow-[0_0_30px_-5px_rgba(0,240,255,0.15)]">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-primary text-2xl animate-pulse drop-shadow-[0_0_8px_#00f0ff]">schema</span>
                        <div>
                          <h3 className="text-xl font-bold text-white">Logic Formulation</h3>
                          <p className="text-xs text-primary font-mono mt-1 flex items-center gap-2">
                            Thinking
                            <span className="flex gap-0.5">
                              <span className="animate-bounce delay-0 w-0.5 h-0.5 bg-primary rounded-full"></span>
                              <span className="animate-bounce delay-100 w-0.5 h-0.5 bg-primary rounded-full"></span>
                              <span className="animate-bounce delay-200 w-0.5 h-0.5 bg-primary rounded-full"></span>
                            </span>
                          </p>
                        </div>
                      </div>
                      <button className="text-xs text-text-muted hover:text-primary transition-colors underline decoration-dashed decoration-primary/50 underline-offset-4">View Reasoning</button>
                    </div>
                    <div className="space-y-4">
                      <div className="flex gap-4">
                        <div className="w-0.5 bg-border-color rounded-full self-stretch relative">
                          <div className="absolute top-0 w-full h-full bg-primary/20"></div>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-white mb-1">Evaluating Big O complexity requirements.</p>
                          <p className="text-xs text-text-muted">Current Bubble Sort is <span className="text-red-400">O(n²)</span>. Refactoring to Merge Sort or Quick Sort for <span className="text-green-400">O(n log n)</span>.</p>
                        </div>
                      </div>
                      <div className="flex gap-4">
                        <div className="w-0.5 bg-gradient-to-b from-primary to-transparent rounded-full self-stretch shadow-[0_0_8px_#00f0ff]"></div>
                        <div className="flex-1">
                          <p className="text-sm text-white mb-2 font-medium">Drafting Quick Sort Implementation</p>
                          <div className="p-3 bg-[#020617] rounded border border-border-color font-mono text-xs text-text-muted relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-1 h-full bg-primary/50"></div>
                            <span className="text-primary">function</span> quickSort(arr) {"{"}<br />
                            &nbsp;&nbsp;<span className="text-primary">if</span> (arr.length &lt;= 1) <span className="text-primary">return</span> arr;<br />
                            &nbsp;&nbsp;<span className="text-text-subtle">
                              {"// Pivot selection strategy based on median-of-three..."}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 4 */}
              <div className="relative flex gap-8 opacity-50 grayscale hover:grayscale-0 hover:opacity-80 transition-all duration-500">
                <div className="relative z-10 flex flex-col items-center">
                  <div className="size-6 rounded-full bg-[#020617] border border-border-color flex items-center justify-center ring-4 ring-background-dark">
                    <div className="size-2 bg-border-color rounded-full"></div>
                  </div>
                </div>
                <div className="flex-1 bg-surface-card/20 border border-border-color rounded-xl p-5 border-dashed">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-text-muted text-xl">code</span>
                    <h3 className="text-lg font-bold text-text-muted">Code Generation & Validation</h3>
                  </div>
                  <p className="text-xs text-text-subtle mt-2">Queued for execution after logic approval.</p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

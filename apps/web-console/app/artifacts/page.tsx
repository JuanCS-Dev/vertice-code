"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type Run = {
  run_id: string;
  org_id: string;
  session_id: string;
  agent: string;
  prompt: string;
  status: string;
  created_at: string;
  updated_at: string;
  final_text?: string | null;
};

export default function ArtifactGallery() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [runsError, setRunsError] = useState<string | null>(null);

  const loadRuns = useCallback(async (signal?: AbortSignal) => {
    try {
      setLoadingRuns(true);
      setRunsError(null);
      const res = await fetch("/api/gateway/runs", {
        cache: "no-store" as RequestCache,
        signal,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as Run[];
      setRuns(Array.isArray(data) ? data : []);
    } catch (e) {
      if (signal?.aborted) return;
      setRunsError(e instanceof Error ? e.message : "failed to load runs");
    } finally {
      if (!signal?.aborted) setLoadingRuns(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadRuns(controller.signal);
    return () => controller.abort();
  }, [loadRuns]);

  return (
    <div className="bg-background-light dark:bg-obsidian min-h-screen flex flex-col font-display text-white selection:bg-primary/30">
      <div className="flex h-screen w-full">
        {/* Sidebar */}
        <aside className="hidden md:flex flex-col w-72 bg-panel/50 backdrop-blur-md border-r border-border-dim h-full shrink-0">
          <div className="p-6 flex flex-col gap-8">
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-2 rounded-lg">
                <span className="material-symbols-outlined text-primary text-2xl">view_in_ar</span>
              </div>
              <div>
                <h1 className="text-white text-lg font-bold leading-none">Vertice Studio</h1>
                <p className="text-gray-400 text-xs font-normal mt-1">Project Alpha</p>
              </div>
            </div>
            <nav className="flex flex-col gap-2">
              <Link href="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                <span className="material-symbols-outlined text-[20px]">dashboard</span>
                <span className="text-sm font-medium">Dashboard</span>
              </Link>
              <Link href="/artifacts" className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary/10 text-primary border border-primary/20">
                <span className="material-symbols-outlined text-[20px] filled">dataset</span>
                <span className="text-sm font-medium">Artifacts</span>
              </Link>
              <Link href="/command-center" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                <span className="text-sm font-medium">Command Center</span>
              </Link>
              <Link href="/cot" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                <span className="material-symbols-outlined text-[20px]">psychology</span>
                <span className="text-sm font-medium">CoT Stream</span>
              </Link>
              <Link href="/settings" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                <span className="material-symbols-outlined text-[20px]">settings</span>
                <span className="text-sm font-medium">Settings</span>
              </Link>
            </nav>
          </div>
          <div className="mt-auto p-6 border-t border-border-dim">
            <div className="flex items-center gap-3">
              <div className="size-10 rounded-full bg-center bg-cover bg-no-repeat ring-2 ring-white/10" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuAGjD81McRQverinhdmJe4oUVG7q5z6P3cU8u0kte7XNSpw4iH16RNQcegmCl0x6B0HAq8cG8RJuv0qJpsCcUPtI1LGZZ00-7vnsVVKOk7-hq4CQi5Jo_uxB0Wdia5JZNFoDMgxkAKOAFFVhWh5KOA6IBDBtWXcQbERuOcImzK2vJPZgkUrjvLMa2rOVL5O7VEkxg-xwT5G0U_pyneCj71nWJXNIEHMXOJpho2Un-jaR6W2Xny7OcdQtoC4gIUy9WHO1q2iG3lwCzsV')" }}></div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">Alex Chen</span>
                <span className="text-xs text-gray-400">Lead Engineer</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-obsidian relative">
          <header className="flex-none px-8 py-6 flex flex-col gap-4 border-b border-border-dim bg-panel/90 backdrop-blur-md z-10">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Link href="/" className="hover:text-primary transition-colors">Vertice Studio</Link>
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              <span className="hover:text-primary transition-colors cursor-pointer">Project Alpha</span>
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              <span className="text-white font-medium">Artifacts</span>
            </div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">Project Artifacts</h2>
                <p className="text-gray-400 mt-2 max-w-xl text-base">Manage code, UI components, and assets generated by your agent swarm.</p>
              </div>
              <div className="flex gap-3">
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-sm font-medium transition-all">
                  <span className="material-symbols-outlined text-[20px]">refresh</span>
                  Regenerate All
                </button>
                <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-obsidian text-sm font-bold transition-all shadow-[0_0_15px_rgba(0,229,255,0.3)]">
                  <span className="material-symbols-outlined text-[20px]">add</span>
                  New Artifact
                </button>
              </div>
            </div>
            <div className="mt-4 flex flex-col md:flex-row gap-4 justify-between items-center">
              <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 w-full md:w-auto scrollbar-hide">
                <button className="px-4 py-1.5 rounded-full bg-primary text-obsidian text-sm font-bold shadow-[0_0_10px_rgba(0,229,255,0.2)]">All</button>
                <button className="px-4 py-1.5 rounded-full bg-panel border border-white/5 hover:border-white/20 text-gray-300 hover:text-white text-sm font-medium transition-all">Code</button>
                <button className="px-4 py-1.5 rounded-full bg-panel border border-white/5 hover:border-white/20 text-gray-300 hover:text-white text-sm font-medium transition-all">UI/UX</button>
                <button className="px-4 py-1.5 rounded-full bg-panel border border-white/5 hover:border-white/20 text-gray-300 hover:text-white text-sm font-medium transition-all">Assets</button>
                <button className="px-4 py-1.5 rounded-full bg-panel border border-white/5 hover:border-white/20 text-gray-300 hover:text-white text-sm font-medium transition-all">Docs</button>
              </div>
              <div className="relative w-full md:w-72">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 material-symbols-outlined">search</span>
                <input className="w-full bg-panel border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all" placeholder="Search artifacts..." type="text" />
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-hidden flex">
            <div className="flex-1 overflow-y-auto p-8">
              <section className="mb-8 rounded-xl border border-border-dim bg-panel/50 backdrop-blur-md">
                <div className="px-4 py-3 border-b border-border-dim flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[20px] text-primary">history</span>
                    <h3 className="text-sm font-semibold text-white">Recent Runs</h3>
                  </div>
                  <button
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-xs font-medium transition-all disabled:opacity-50"
                    onClick={() => void loadRuns()}
                    disabled={loadingRuns}
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[18px]">refresh</span>
                    Refresh
                  </button>
                </div>

                <div className="p-4">
                  {runsError ? (
                    <div className="text-xs text-red-300">{runsError}</div>
                  ) : loadingRuns ? (
                    <div className="text-xs text-gray-400">Loading…</div>
                  ) : runs.length === 0 ? (
                    <div className="text-xs text-gray-400">No runs yet.</div>
                  ) : (
                    <ul className="divide-y divide-white/5">
                      {runs.slice(0, 10).map((r) => (
                        <li key={r.run_id} className="py-2 flex items-start justify-between gap-4">
                          <div className="min-w-0">
                            <div className="text-xs text-gray-300 truncate">{r.prompt || "(no prompt)"}</div>
                            <div className="mt-1 text-[10px] text-gray-500 font-mono">
                              {r.run_id} · org:{r.org_id}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-1 shrink-0">
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300">
                              {r.status}
                            </span>
                            <span className="text-[10px] text-gray-500 font-mono">
                              {new Date(r.updated_at || r.created_at).toLocaleString()}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-20">
                {/* Artifact Card 1 */}
                <div className="group relative flex flex-col aspect-square bg-panel rounded-xl overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-glow border border-border-dim hover:border-primary/50">
                  <div className="absolute top-2 right-2 z-10 px-1.5 py-0.5 bg-primary text-obsidian text-[9px] font-bold rounded uppercase tracking-wider shadow-sm">New</div>
                  <div className="px-4 py-2 border-b border-border-dim bg-panel-light flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2 truncate">
                      <span className="material-symbols-outlined text-blue-400 text-[18px]">data_object</span>
                      <span className="text-sm font-medium text-white truncate">AuthSystem.tsx</span>
                    </div>
                  </div>
                  <div className="flex-1 bg-[#0d1117] p-3 overflow-hidden relative group-hover:bg-[#161b22] transition-colors">
                    <code className="font-mono text-[10px] leading-relaxed text-gray-400 block opacity-80 select-none">
                      <span className="text-pink-400">import</span> React <span className="text-pink-400">from</span>{" "}
                      &apos;react&apos;;<br />
                      <span className="text-pink-400">import</span> {"{"} useAuth {"}"}{" "}
                      <span className="text-pink-400">from</span> &apos;@/hooks&apos;;<br />
                      <br />
                      <span className="text-blue-400">export const</span> AuthGuard = ({"{"} children {"}"}) =&gt; {"{"}<br />
                      &nbsp;&nbsp;<span className="text-blue-400">const</span> {"{"} user, loading {"}"} = useAuth();<br />
                      &nbsp;&nbsp;<span className="text-pink-400">if</span> (loading) <span className="text-pink-400">return</span> &lt;Loader /&gt;;<br />
                      &nbsp;&nbsp;<span className="text-pink-400">return</span> user ? children : &lt;Redirect /&gt;;<br />
                      {"}"}
                    </code>
                    <div className="absolute inset-0 bg-gradient-to-t from-panel to-transparent opacity-20 pointer-events-none"></div>
                    <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button className="p-2 rounded-full bg-white text-black hover:bg-primary transition-colors shadow-lg" title="View Code">
                        <span className="material-symbols-outlined text-[20px]">code</span>
                      </button>
                      <button className="p-2 rounded-full bg-panel text-white hover:bg-primary hover:text-black transition-colors shadow-lg" title="Download">
                        <span className="material-symbols-outlined text-[20px]">download</span>
                      </button>
                    </div>
                  </div>
                  <div className="px-4 py-2 border-t border-border-dim bg-panel flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="size-5 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg">A</div>
                      <span className="text-[10px] text-gray-400">Architect-V4</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">2m ago</span>
                  </div>
                </div>

                {/* Artifact Card 2 */}
                <div className="group relative flex flex-col aspect-square bg-panel rounded-xl border border-border-dim overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30">
                  <div className="px-4 py-2 border-b border-border-dim bg-panel-light flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2 truncate">
                      <span className="material-symbols-outlined text-orange-400 text-[18px]">html</span>
                      <span className="text-sm font-medium text-white truncate">LandingPage.html</span>
                    </div>
                  </div>
                  <div className="flex-1 bg-panel-light relative overflow-hidden">
                    <div className="w-full h-full bg-cover bg-top opacity-80 group-hover:opacity-100 transition-all duration-500 group-hover:scale-105" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuA-IOwGIFqnj6IVMTAr00IuZNxjfxJOXOd06JY_0c809sOPYfez0nrBYC1NDEJMxakWoL6Z17ZZtqaJWqe77nlyzG8_p4NrB-V1wOD_tHf-OvxNAHSmKpbSafq971KDQxXu4z8cymT1O1vR0sol5H9H9sDroGOMbOmJRClL8gnK4QsNd6N62Kkgvunlg-hDbg6uK5simPhLRlaHuRppkeJWmb60b-Ki957Qfpj65dKNO67gIWAV9ygpgJj2zUvrsTt7lcVzBc-Oruf2')" }}></div>
                    <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button className="p-2 rounded-full bg-white text-black hover:bg-primary transition-colors shadow-lg" title="Preview UI">
                        <span className="material-symbols-outlined text-[20px]">visibility</span>
                      </button>
                    </div>
                  </div>
                  <div className="px-4 py-2 border-t border-border-dim bg-panel flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="size-5 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg">D</div>
                      <span className="text-[10px] text-gray-400">Designer-X2</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">15m ago</span>
                  </div>
                </div>

                {/* Artifact Card 3 */}
                <div className="group relative flex flex-col aspect-square bg-panel rounded-xl border border-border-dim overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30">
                  <div className="px-4 py-2 border-b border-border-dim bg-panel-light flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2 truncate">
                      <span className="material-symbols-outlined text-yellow-400 text-[18px]">database</span>
                      <span className="text-sm font-medium text-white truncate">DatabaseSchema.sql</span>
                    </div>
                  </div>
                  <div className="flex-1 bg-[#0d1117] p-3 overflow-hidden relative group-hover:bg-[#161b22] transition-colors">
                    <div className="flex flex-col gap-2">
                      <div className="flex gap-2 items-center text-[10px] text-gray-500 font-mono border-b border-white/5 pb-1">
                        <span className="material-symbols-outlined text-[12px]">table_chart</span> users
                      </div>
                      <div className="flex gap-2 items-center text-[10px] text-gray-500 font-mono border-b border-white/5 pb-1">
                        <span className="material-symbols-outlined text-[12px]">table_chart</span> orders
                      </div>
                      <div className="flex gap-2 items-center text-[10px] text-gray-500 font-mono border-b border-white/5 pb-1">
                        <span className="material-symbols-outlined text-[12px]">table_chart</span> products
                      </div>
                      <div className="flex gap-2 items-center text-[10px] text-gray-500 font-mono border-b border-white/5 pb-1">
                        <span className="material-symbols-outlined text-[12px]">table_chart</span> analytics
                      </div>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button className="p-2 rounded-full bg-white text-black hover:bg-primary transition-colors shadow-lg">
                        <span className="material-symbols-outlined text-[20px]">edit</span>
                      </button>
                    </div>
                  </div>
                  <div className="px-4 py-2 border-t border-border-dim bg-panel flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="size-5 rounded-full bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg">S</div>
                      <span className="text-[10px] text-gray-400">SysAdmin-Bot</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">1h ago</span>
                  </div>
                </div>

                {/* Artifact Card 4 */}
                <div className="group relative flex flex-col aspect-square bg-panel rounded-xl border border-border-dim overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-primary/30">
                  <div className="px-4 py-2 border-b border-border-dim bg-panel-light flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2 truncate">
                      <span className="material-symbols-outlined text-cyan-400 text-[18px]">css</span>
                      <span className="text-sm font-medium text-white truncate">global.css</span>
                    </div>
                  </div>
                  <div className="flex-1 bg-[#0d1117] p-3 overflow-hidden relative group-hover:bg-[#161b22] transition-colors">
                    <code className="font-mono text-[10px] leading-relaxed text-gray-400 block opacity-80 select-none">
                      :root {"{"}<br />
                      &nbsp;&nbsp;--primary: <span className="text-cyan-400">#06f9f9</span>;<br />
                      &nbsp;&nbsp;--bg: <span className="text-cyan-400">#0f2323</span>;<br />
                      {"}"}<br />
                      <span className="text-yellow-400">.container</span> {"{"}<br />
                      &nbsp;&nbsp;max-width: 1200px;<br />
                      &nbsp;&nbsp;margin: 0 auto;<br />
                      {"}"}
                    </code>
                    <div className="absolute inset-0 bg-gradient-to-t from-panel to-transparent opacity-20 pointer-events-none"></div>
                    <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button className="p-2 rounded-full bg-white text-black hover:bg-primary transition-colors shadow-lg">
                        <span className="material-symbols-outlined text-[20px]">code</span>
                      </button>
                    </div>
                  </div>
                  <div className="px-4 py-2 border-t border-border-dim bg-panel flex-none flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="size-5 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg">D</div>
                      <span className="text-[10px] text-gray-400">Designer-X2</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">2h ago</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Activity Panel */}
            <aside className="hidden xl:flex flex-col w-80 bg-panel/50 border-l border-border-dim h-full overflow-y-auto shrink-0 p-6 gap-8">
              <div>
                <h3 className="text-sm uppercase tracking-widest text-gray-500 font-bold mb-4">Project Overview</h3>
                <div className="flex flex-col gap-3">
                  <div className="p-4 rounded-xl bg-panel border border-border-dim relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-6xl text-primary">deployed_code</span>
                    </div>
                    <p className="text-gray-400 text-xs font-medium">Total Artifacts</p>
                    <p className="text-2xl font-bold text-white mt-1">142</p>
                    <div className="mt-2 flex items-center gap-2 text-[10px] text-primary">
                      <span className="material-symbols-outlined text-[12px]">trending_up</span>
                      +12 this week
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-panel border border-border-dim relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-6xl text-white">code</span>
                    </div>
                    <p className="text-gray-400 text-xs font-medium">Generated LOC</p>
                    <p className="text-2xl font-bold text-white mt-1">12.5k</p>
                    <div className="w-full bg-white/10 h-1 mt-3 rounded-full overflow-hidden">
                      <div className="bg-primary h-full w-[70%]"></div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-auto pt-6 border-t border-border-dim">
                <h3 className="text-sm uppercase tracking-widest text-gray-500 font-bold mb-4">Live Activity</h3>
                <div className="flex flex-col gap-4 relative">
                  <div className="absolute left-[5px] top-2 bottom-2 w-[1px] bg-white/10"></div>
                  <div className="flex gap-3 relative">
                    <div className="size-2.5 mt-1.5 rounded-full bg-primary ring-4 ring-bg-panel z-10"></div>
                    <div>
                      <p className="text-xs text-white"><span className="text-primary font-bold">Architect-V4</span> updated <span className="text-gray-300 italic">AuthSystem.tsx</span></p>
                      <p className="text-[10px] text-gray-500 mt-0.5">2 mins ago</p>
                    </div>
                  </div>
                  <div className="flex gap-3 relative">
                    <div className="size-2.5 mt-1.5 rounded-full bg-slate-600 ring-4 ring-bg-panel z-10"></div>
                    <div>
                      <p className="text-xs text-white"><span className="text-white font-bold">Designer-X2</span> created <span className="text-gray-300 italic">LandingPage.html</span></p>
                      <p className="text-[10px] text-gray-500 mt-0.5">15 mins ago</p>
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}

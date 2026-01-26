"use client";

import Link from "next/link";

export default function CommandCenter() {
  return (
    <div className="bg-obsidian text-text-main font-body overflow-hidden h-screen flex flex-col selection:bg-neon-cyan/30 text-white">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border-dim bg-obsidian px-6 py-3 shrink-0 z-20">
        <div className="flex items-center gap-4">
          <Link href="/" className="size-8 rounded-lg bg-gradient-to-br from-neon-cyan/20 to-teal-900 border border-neon-cyan/30 flex items-center justify-center text-neon-cyan shadow-lg shadow-neon-cyan/10">
            <span className="material-symbols-outlined text-[20px]">hub</span>
          </Link>
          <div>
            <h1 className="font-display font-bold text-lg leading-tight tracking-tight text-white">Vertice Code Web</h1>
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-neon-cyan animate-pulse shadow-[0_0_8px_#00E5FF]"></span>
              <span className="text-xs text-neon-cyan font-medium tracking-wide">SYSTEM ONLINE</span>
            </div>
          </div>
        </div>
        <nav className="hidden md:flex items-center p-1 rounded-lg bg-panel border border-border-dim">
          <Link href="/dashboard" className="px-5 py-1.5 rounded text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors">Stream</Link>
          <Link href="/command-center" className="px-5 py-1.5 rounded text-sm font-medium bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20 shadow-[0_0_10px_rgba(0,229,255,0.1)]">Command Center</Link>
          <Link href="/cot" className="px-5 py-1.5 rounded text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors">CoT</Link>
        </nav>
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg text-sm font-bold transition-colors">
              <span className="material-symbols-outlined text-[18px]">pause_circle</span>
              <span>Halt</span>
            </button>
            <button className="flex items-center gap-2 px-3 py-2 bg-neon-cyan hover:bg-neon-cyan-dim text-obsidian rounded-lg text-sm font-bold shadow-lg shadow-neon-cyan/20 transition-colors">
              <span className="material-symbols-outlined text-[18px]">terminal</span>
              <span>Export Logs</span>
            </button>
          </div>
          <div className="h-8 w-px bg-border-dim mx-2"></div>
          <div className="size-9 rounded-full bg-cover bg-center ring-2 ring-border-dim" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCA5yPEowHvVicXi2t_3pQ8qEq-IResbadUZqOnLwoAHTRMFPk79eiPYhvFXiWaB1tRdg5c9BI3FoRhVudztsbSlun_urUV0VMeDPBC7cpaSASbsRhk2-ux7j_TNYAma8tDn-saTw4UVmQqoBjKFQ73yYgPlMbDmyn9t_T-DifBdEjOvgChU7nZX1vEFiF-c8TvaAWSPQofT6J49AZrOawFoCFNqJWCxLXp-HbLgmVFpC2HsyuWZv6E2vZsx9RT22_TRVTTzIRPff2S')" }}></div>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden">
        {/* Left Sidebar: Active Agents */}
        <aside className="w-72 bg-panel border-r border-border-dim flex flex-col z-10 hidden lg:flex">
          <div className="p-4 border-b border-border-dim">
            <h2 className="font-display text-xs font-bold text-neon-cyan uppercase tracking-wider mb-2">Active Agents</h2>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-2.5 top-2.5 text-gray-500 text-[18px]">search</span>
              <input className="w-full bg-obsidian border border-border-dim rounded-lg py-2 pl-9 pr-4 text-sm text-white placeholder-gray-600 focus:ring-1 focus:ring-neon-cyan focus:border-neon-cyan/50 focus:outline-none" placeholder="Filter agents..." type="text" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {/* Agent Card 1 */}
            <div className="p-3 rounded-lg bg-panel-light border border-neon-cyan/30 shadow-glow-cyan group cursor-pointer hover:bg-white/5 transition-all">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-neon-cyan/10 text-neon-cyan">
                    <span className="material-symbols-outlined text-[20px]">architecture</span>
                  </div>
                  <span className="font-display font-bold text-white text-sm">Architect</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-neon-emerald/10 text-neon-emerald border border-neon-emerald/20">ACTIVE</span>
              </div>
              <p className="text-xs text-gray-400 mb-2 font-mono">Analyzing constraints...</p>
              <div className="w-full bg-obsidian rounded-full h-1 overflow-hidden">
                <div className="bg-neon-cyan h-full rounded-full shadow-[0_0_8px_#00E5FF]" style={{ width: "75%" }}></div>
              </div>
            </div>
            {/* Agent Card 2 */}
            <div className="p-3 rounded-lg bg-panel border border-border-dim hover:border-neon-cyan/30 group cursor-pointer hover:bg-panel-light transition-all">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-neon-emerald/10 text-neon-emerald">
                    <span className="material-symbols-outlined text-[20px]">code</span>
                  </div>
                  <span className="font-display font-bold text-white text-sm">Coder Alpha</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">THINKING</span>
              </div>
              <p className="text-xs text-gray-400 mb-2 font-mono">Generating UserAuth...</p>
              <div className="w-full bg-obsidian rounded-full h-1 overflow-hidden">
                <div className="bg-neon-emerald h-full rounded-full animate-pulse shadow-[0_0_8px_#10B981]" style={{ width: "45%" }}></div>
              </div>
            </div>
            {/* Agent Card 3 */}
            <div className="p-3 rounded-lg bg-panel border border-border-dim hover:border-neon-cyan/30 group cursor-pointer hover:bg-panel-light transition-all opacity-70 hover:opacity-100">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-purple-500/10 text-purple-400">
                    <span className="material-symbols-outlined text-[20px]">rate_review</span>
                  </div>
                  <span className="font-display font-bold text-gray-300 text-sm">Reviewer</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-500/10 text-gray-400 border border-gray-500/20">IDLE</span>
              </div>
              <p className="text-xs text-gray-500 mb-2 font-mono">Awaiting PR...</p>
              <div className="w-full bg-obsidian rounded-full h-1 overflow-hidden">
                <div className="bg-gray-600 h-full rounded-full" style={{ width: "0%" }}></div>
              </div>
            </div>
            {/* Agent Card 4 */}
            <div className="p-3 rounded-lg bg-panel border border-border-dim hover:border-neon-cyan/30 group cursor-pointer hover:bg-panel-light transition-all">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-red-500/10 text-red-400">
                    <span className="material-symbols-outlined text-[20px]">security</span>
                  </div>
                  <span className="font-display font-bold text-white text-sm">SecOps</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20">MONITOR</span>
              </div>
              <p className="text-xs text-gray-400 mb-2 font-mono">Vulnerability scan...</p>
              <div className="w-full bg-obsidian rounded-full h-1 overflow-hidden">
                <div className="bg-red-500 h-full rounded-full" style={{ width: "90%" }}></div>
              </div>
            </div>
          </div>
          <div className="p-3 border-t border-border-dim bg-panel-light">
            <button className="flex items-center justify-center gap-2 w-full py-2 rounded border border-dashed border-gray-600 text-gray-400 hover:text-neon-cyan hover:border-neon-cyan hover:bg-neon-cyan/5 transition-all text-sm font-medium font-mono">
              <span className="material-symbols-outlined text-[18px]">add</span>
              DEPLOY_AGENT
            </button>
          </div>
        </aside>

        {/* Center Canvas: Agent Mesh */}
        <section className="flex-1 flex flex-col min-w-0 bg-obsidian relative">
          <div className="flex-1 relative overflow-hidden group">
            {/* CSS Grid Background */}
            <div className="absolute inset-0" style={{
              backgroundImage: "linear-gradient(rgba(0, 229, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 229, 255, 0.03) 1px, transparent 1px)",
              backgroundSize: "40px 40px"
            }}></div>

            <div className="absolute top-4 left-6 z-10 pointer-events-none">
              <h2 className="font-display text-2xl font-bold text-white tracking-tight">Agent Mesh <span className="text-neon-cyan">v2.0</span></h2>
              <p className="text-xs text-neon-cyan/70 font-mono tracking-widest mt-1">LIVE VIEW • ORCHESTRATION LAYER</p>
            </div>
            <div className="absolute top-4 right-6 z-10 flex flex-col gap-2">
              <button className="size-8 flex items-center justify-center rounded bg-panel text-gray-400 border border-border-dim hover:border-neon-cyan hover:text-neon-cyan shadow-lg transition-colors">
                <span className="material-symbols-outlined text-[20px]">add</span>
              </button>
              <button className="size-8 flex items-center justify-center rounded bg-panel text-gray-400 border border-border-dim hover:border-neon-cyan hover:text-neon-cyan shadow-lg transition-colors">
                <span className="material-symbols-outlined text-[20px]">remove</span>
              </button>
              <button className="size-8 flex items-center justify-center rounded bg-panel text-gray-400 border border-border-dim hover:border-neon-cyan hover:text-neon-cyan shadow-lg transition-colors">
                <span className="material-symbols-outlined text-[20px]">center_focus_strong</span>
              </button>
            </div>

            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              {/* SVG Lines */}
              <svg className="absolute inset-0 size-full z-0 opacity-80" style={{ overflow: "visible" }}>
                <defs>
                  <linearGradient id="lineGradient" x1="0%" x2="100%" y1="0%" y2="0%">
                    <stop offset="0%" style={{ stopColor: "#00E5FF", stopOpacity: 1 }}></stop>
                    <stop offset="100%" style={{ stopColor: "#10B981", stopOpacity: 1 }}></stop>
                  </linearGradient>
                </defs>
                <line className="opacity-30" stroke="#00E5FF" strokeWidth="1" x1="50%" x2="30%" y1="50%" y2="30%"></line>
                <line className="animate-flow" stroke="#00E5FF" strokeWidth="2" x1="50%" x2="30%" y1="50%" y2="30%" strokeDasharray="5,5"></line>
                <line stroke="#2D4046" strokeWidth="1" x1="50%" x2="70%" y1="50%" y2="35%"></line>
                <line className="opacity-30" stroke="#10B981" strokeWidth="1" x1="50%" x2="50%" y1="50%" y2="75%"></line>
                <line className="animate-flow" stroke="#10B981" strokeDasharray="2,2" strokeWidth="2" x1="50%" x2="50%" y1="50%" y2="75%"></line>
                <line stroke="#1F2E33" strokeDasharray="4 4" strokeWidth="1" x1="30%" x2="50%" y1="30%" y2="75%"></line>
              </svg>

              {/* Central Node */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-3">
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-neon-cyan/20 animate-pulse-slow scale-150"></div>
                  <div className="size-24 rounded-full bg-obsidian border-2 border-neon-cyan shadow-glow-cyan flex items-center justify-center relative z-10">
                    <span className="material-symbols-outlined text-neon-cyan text-[40px]">hub</span>
                  </div>
                  <div className="absolute -top-1 -right-1 size-5 rounded-full bg-neon-emerald border-4 border-obsidian z-20 animate-pulse"></div>
                </div>
                <div className="bg-panel/90 backdrop-blur-md px-4 py-2 rounded-lg border border-neon-cyan/30 text-center shadow-lg">
                  <p className="text-white font-bold text-sm tracking-wide">ORCHESTRATOR</p>
                  <p className="text-[10px] text-neon-cyan font-mono">ROOT_NODE • ACTIVE</p>
                </div>
              </div>

              {/* Architect Node */}
              <div className="absolute top-[30%] left-[30%] -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2">
                <div className="size-16 rounded-full bg-obsidian border-2 border-neon-cyan shadow-[0_0_20px_rgba(0,229,255,0.2)] flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-neon-cyan text-[28px]">architecture</span>
                </div>
                <div className="bg-panel/80 backdrop-blur-sm px-2 py-1 rounded border border-neon-cyan/20">
                  <p className="text-gray-200 font-medium text-xs font-mono">ARCHITECT_01</p>
                </div>
                <div className="absolute top-1/2 left-full ml-4 bg-neon-cyan/10 text-neon-cyan text-[10px] px-2 py-1 rounded border border-neon-cyan/20 whitespace-nowrap animate-bounce font-mono">
                  Sending specs...
                </div>
              </div>

              {/* Coder Node */}
              <div className="absolute top-[75%] left-[50%] -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2">
                <div className="size-16 rounded-full bg-obsidian border-2 border-neon-emerald shadow-[0_0_20px_rgba(16,185,129,0.2)] flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-neon-emerald text-[28px]">code</span>
                </div>
                <div className="bg-panel/80 backdrop-blur-sm px-2 py-1 rounded border border-neon-emerald/20">
                  <p className="text-gray-200 font-medium text-xs font-mono">CODER_ALPHA</p>
                </div>
              </div>

              {/* Reviewer Node */}
              <div className="absolute top-[35%] left-[70%] -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 opacity-50">
                <div className="size-14 rounded-full bg-obsidian border-2 border-purple-500/30 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-purple-400 text-[24px]">rate_review</span>
                </div>
                <div className="bg-panel/80 backdrop-blur-sm px-2 py-1 rounded border border-purple-500/10">
                  <p className="text-gray-400 font-medium text-xs font-mono">REVIEWER</p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Terminal */}
          <div className="h-64 bg-obsidian border-t border-border-dim flex flex-col shrink-0 z-20">
            <div className="flex items-center justify-between px-4 py-2 bg-panel border-b border-border-dim">
              <div className="flex items-center gap-2 text-neon-cyan">
                <span className="material-symbols-outlined text-[16px]">terminal</span>
                <h3 className="font-display font-bold text-xs tracking-wider uppercase">System Events Terminal</h3>
              </div>
              <div className="flex gap-3 text-xs font-mono">
                <span className="text-neon-emerald flex items-center gap-1"><span className="size-1.5 rounded-full bg-neon-emerald animate-pulse"></span> Live Connection</span>
                <span className="text-gray-500">v2.4.1</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed no-scrollbar bg-obsidian/50">
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:01]</span>
                <span className="text-neon-cyan font-bold">INFO</span>
                <span className="text-gray-300">System initialized. Orchestrator ready.</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:02]</span>
                <span className="text-neon-cyan font-bold">INFO</span>
                <span className="text-gray-300">Loading agent configuration map from /config/agents.json</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:05]</span>
                <span className="text-neon-cyan font-bold">ARCH</span>
                <span className="text-gray-300">Validating architectural constraints for module &apos;UserAuth&apos;.</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:08]</span>
                <span className="text-neon-cyan font-bold">ARCH</span>
                <span className="text-gray-300">Constraint check passed. Handoff to <span className="text-neon-emerald">Coder_Alpha</span>.</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded bg-amber-900/10 border-l-2 border-amber-500/50 my-1">
                <span className="text-gray-600 select-none">[14:02:10]</span>
                <span className="text-neon-amber font-bold">WARN</span>
                <span className="text-amber-100">Network latency spike detected (200ms) on node #4.</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:11]</span>
                <span className="text-neon-emerald font-bold">CODE</span>
                <span className="text-gray-300">
                  Coder_Alpha started task: &quot;Implement JWT middleware&quot;.
                </span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded transition-colors border-l-2 border-transparent hover:border-neon-cyan">
                <span className="text-gray-600 select-none">[14:02:15]</span>
                <span className="text-neon-emerald font-bold">CODE</span>
                <span className="text-gray-300">Generating unit tests...</span>
              </div>
              <div className="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded animate-pulse bg-neon-cyan/5 border-l-2 border-neon-cyan mt-1">
                <span className="text-gray-600 select-none">[14:02:18]</span>
                <span className="text-white font-bold">SYS</span>
                <span className="text-neon-cyan">Token stream optimization active. +12% efficiency.</span>
              </div>
            </div>
          </div>
        </section>

        {/* Right Sidebar: Telemetry */}
        <aside className="w-80 bg-panel border-l border-border-dim flex flex-col overflow-y-auto hidden md:flex">
          <div className="p-4 border-b border-border-dim">
            <h2 className="font-display text-xs font-bold text-neon-cyan uppercase tracking-wider">Performance Telemetry</h2>
          </div>
          <div className="p-4 space-y-6">
            <div className="bg-panel-light rounded-xl p-4 border border-border-dim hover:border-neon-cyan/30 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <p className="text-gray-400 text-xs font-medium font-mono uppercase">Token Velocity</p>
                <span className="text-neon-emerald text-xs font-bold flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">trending_up</span>
                  +12%
                </span>
              </div>
              <div className="flex items-baseline gap-2 mb-4">
                <h3 className="text-3xl font-display font-bold text-white text-neon">480</h3>
                <span className="text-gray-500 text-xs font-mono">t/s</span>
              </div>
              <div className="h-16 w-full">
                {/* SVG Graph Placeholder */}
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 40">
                  <defs>
                    <linearGradient id="grad1" x1="0%" x2="0%" y1="0%" y2="100%">
                      <stop offset="0%" style={{ stopColor: "#00E5FF", stopOpacity: 0.3 }}></stop>
                      <stop offset="100%" style={{ stopColor: "#00E5FF", stopOpacity: 0 }}></stop>
                    </linearGradient>
                  </defs>
                  <path d="M0 35 Q 10 30, 20 32 T 40 25 T 60 15 T 80 20 T 100 5" fill="none" stroke="#00E5FF" strokeWidth="2"></path>
                  <path d="M0 35 Q 10 30, 20 32 T 40 25 T 60 15 T 80 20 T 100 5 V 40 H 0 Z" fill="url(#grad1)" stroke="none"></path>
                </svg>
              </div>
            </div>

            <div className="bg-panel-light rounded-xl p-4 border border-border-dim hover:border-neon-cyan/30 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <p className="text-gray-400 text-xs font-medium font-mono uppercase">Success Rate</p>
                <span className="text-neon-emerald text-xs font-bold">+0.5%</span>
              </div>
              <div className="flex items-baseline gap-2 mb-4">
                <h3 className="text-3xl font-display font-bold text-white text-neon">98.2%</h3>
              </div>
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-400 font-mono">
                    <span>BUILD</span>
                    <span className="text-neon-cyan">99%</span>
                  </div>
                  <div className="w-full bg-obsidian rounded-full h-1">
                    <div className="bg-neon-cyan h-full rounded-full shadow-[0_0_5px_#00E5FF]" style={{ width: "99%" }}></div>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-400 font-mono">
                    <span>TEST</span>
                    <span className="text-neon-emerald">96%</span>
                  </div>
                  <div className="w-full bg-obsidian rounded-full h-1">
                    <div className="bg-neon-emerald h-full rounded-full shadow-[0_0_5px_#10B981]" style={{ width: "96%" }}></div>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-400 font-mono">
                    <span>DEPLOY</span>
                    <span className="text-white">100%</span>
                  </div>
                  <div className="w-full bg-obsidian rounded-full h-1">
                    <div className="bg-white h-full rounded-full" style={{ width: "100%" }}></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-panel-light rounded-xl p-4 border border-border-dim hover:border-neon-cyan/30 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <p className="text-gray-400 text-xs font-medium font-mono uppercase">Autonomous Loops</p>
              </div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-2xl font-display font-bold text-white">12<span className="text-gray-500 text-lg">/20</span></h3>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wide">Current Iteration</p>
                </div>
                <div className="size-10 rounded-full border-4 border-obsidian border-t-neon-cyan shadow-[0_0_10px_rgba(0,229,255,0.2)] flex items-center justify-center rotate-45">
                </div>
              </div>
              <div className="grid grid-cols-4 gap-1 h-8 items-end">
                <div className="bg-neon-cyan/40 h-[40%] rounded-sm"></div>
                <div className="bg-neon-cyan/60 h-[70%] rounded-sm"></div>
                <div className="bg-neon-cyan h-[60%] rounded-sm shadow-[0_0_5px_#00E5FF]"></div>
                <div className="bg-border-dim h-[30%] rounded-sm"></div>
              </div>
            </div>

            <div className="pt-4 border-t border-border-dim">
              <div className="flex justify-between items-center mb-2">
                <p className="text-gray-400 text-xs font-medium font-mono uppercase">System Load</p>
                <span className="text-neon-cyan text-xs font-mono font-bold">34%</span>
              </div>
              <div className="w-full bg-obsidian rounded h-1 overflow-hidden flex">
                <div className="w-[10%] bg-neon-emerald"></div>
                <div className="w-[15%] bg-neon-cyan"></div>
                <div className="w-[9%] bg-white"></div>
                <div className="flex-1 bg-transparent"></div>
              </div>
              <div className="flex justify-between text-[10px] text-gray-500 mt-1 font-mono">
                <span>CPU</span>
                <span>MEM</span>
                <span>NET</span>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

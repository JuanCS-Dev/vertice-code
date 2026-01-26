"use client";

import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="bg-background-light dark:bg-obsidian-deep min-h-screen flex flex-col font-display text-slate-900 dark:text-white overflow-x-hidden antialiased selection:bg-primary selection:text-obsidian">
      {/* Sticky Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 w-full border-b border-white/5 bg-obsidian/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <div className="flex items-center gap-3 text-white">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <span className="material-symbols-outlined text-[24px]">token</span>
            </div>
            <h2 className="text-lg font-bold tracking-tight uppercase">Vertice</h2>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <Link href="#" className="text-sm font-medium text-gray-300 hover:text-primary transition-colors">Features</Link>
            <Link href="#" className="text-sm font-medium text-gray-300 hover:text-primary transition-colors">Documentation</Link>
            <Link href="#" className="text-sm font-medium text-gray-300 hover:text-primary transition-colors">Resources</Link>
            <Link href="#" className="text-sm font-medium text-gray-300 hover:text-primary transition-colors">Pricing</Link>
          </div>
          <div className="flex items-center gap-4">
            <Link href="#" className="hidden sm:block text-sm font-bold text-white hover:text-primary transition-colors">
              Login
            </Link>
            <Link href="/dashboard" className="flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-bold text-obsidian hover:bg-white hover:shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all duration-300">
              Enter Portal
            </Link>
          </div>
        </div>
      </nav>

      {/* Immersive Hero Section */}
      <section className="relative flex min-h-screen w-full flex-col items-center justify-center pt-16">
        {/* Abstract Background */}
        <div className="absolute inset-0 z-0 bg-obsidian">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#1a2c2c] via-obsidian to-obsidian-deep opacity-80"></div>
          {/* Subtle Grid overlay - simulated with CSS since external SVG might fail */}
          <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
        </div>

        <div className="relative z-10 flex w-full max-w-4xl flex-col items-center gap-10 px-4 text-center">
          <div className="flex flex-col gap-4 animate-fade-in-up">
            <h1 className="text-4xl font-black leading-tight tracking-tight text-white sm:text-6xl lg:text-7xl">
              One Action. <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-white">Infinite Possibilities.</span>
            </h1>
            <p className="text-lg font-light text-gray-400 sm:text-xl">
              Experience the direct-to-agent interface.
            </p>
          </div>

          {/* The Agent Input */}
          <div className="w-full max-w-2xl transform transition-all duration-500 hover:scale-[1.01]">
            <div className="group relative flex items-center overflow-hidden rounded-xl border border-white/10 bg-white/5 p-2 shadow-2xl backdrop-blur-xl transition-all focus-within:border-primary/50 focus-within:bg-obsidian focus-within:shadow-[0_0_30px_rgba(0,229,255,0.2)]">
              <div className="flex h-12 w-12 items-center justify-center text-primary/70 group-focus-within:text-primary">
                <span className="material-symbols-outlined text-[28px]">terminal</span>
              </div>
              <input
                autoFocus
                className="flex-1 bg-transparent px-2 py-4 text-lg font-medium text-white placeholder-gray-500 focus:outline-none focus:ring-0 sm:text-xl"
                placeholder="Command the agent..."
                type="text"
              />
              <div className="hidden sm:flex items-center pr-2">
                <span className="mr-3 text-xs font-mono text-gray-600">PRESS ENTER</span>
                <button className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-obsidian shadow-lg transition-transform hover:bg-white active:scale-95">
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </div>
            </div>

            {/* Simulated connection status */}
            <div className="mt-3 flex items-center justify-center gap-2 text-xs font-mono text-primary/60">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              SYSTEM ONLINE // WAITING FOR INPUT
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 animate-bounce text-gray-600">
          <span className="material-symbols-outlined">keyboard_arrow_down</span>
        </div>
      </section>

      {/* Minimalist Feature Grid */}
      <section className="relative w-full bg-obsidian-deep py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mb-16 max-w-2xl">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Why Vertice?</h2>
            <p className="mt-4 text-lg leading-8 text-gray-400">
              Designed for the next generation of intelligence. Pure function, zero friction.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="group flex flex-col gap-4 border-l border-white/10 pl-6 transition-colors hover:border-primary/50">
              <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-obsidian text-primary shadow-inner">
                <span className="material-symbols-outlined text-[32px]">psychology</span>
              </div>
              <h3 className="text-xl font-bold text-white group-hover:text-primary transition-colors">
                Neural Processing
              </h3>
              <p className="text-base leading-relaxed text-gray-500">
                Advanced algorithms that adapt to your workflow instantly. Our models learn from context, not just keywords.
              </p>
            </div>
            {/* Feature 2 */}
            <div className="group flex flex-col gap-4 border-l border-white/10 pl-6 transition-colors hover:border-primary/50">
              <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-obsidian text-primary shadow-inner">
                <span className="material-symbols-outlined text-[32px]">rocket_launch</span>
              </div>
              <h3 className="text-xl font-bold text-white group-hover:text-primary transition-colors">
                Instant Deployment
              </h3>
              <p className="text-base leading-relaxed text-gray-500">
                Ship your agent interactions to production with zero latency. From prompt to deployed API in milliseconds.
              </p>
            </div>
            {/* Feature 3 */}
            <div className="group flex flex-col gap-4 border-l border-white/10 pl-6 transition-colors hover:border-primary/50">
              <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-obsidian text-primary shadow-inner">
                <span className="material-symbols-outlined text-[32px]">encrypted</span>
              </div>
              <h3 className="text-xl font-bold text-white group-hover:text-primary transition-colors">
                Secure Enclaves
              </h3>
              <p className="text-base leading-relaxed text-gray-500">
                Enterprise-grade security ensuring your data remains isolated. Your intellectual property never leaves the vault.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section (Pre-Footer) */}
      <section className="relative overflow-hidden bg-obsidian py-20 border-t border-white/5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,_var(--tw-gradient-stops))] from-primary/5 to-transparent"></div>
        <div className="relative mx-auto flex max-w-7xl flex-col items-center justify-center px-6 text-center lg:px-8">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Ready to enter the new era?</h2>
          <div className="mt-8 flex items-center justify-center gap-4">
            <button className="rounded-md bg-white px-6 py-3 text-sm font-bold text-obsidian hover:bg-gray-200 transition-colors">
              Read Documentation
            </button>
            <button className="rounded-md border border-primary/30 bg-primary/10 px-6 py-3 text-sm font-bold text-primary hover:bg-primary/20 transition-colors backdrop-blur-sm">
              View Pricing
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-obsidian-deep py-12">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-8 md:flex-row">
            <div className="flex items-center gap-2 text-white opacity-50">
              <span className="material-symbols-outlined text-[20px]">token</span>
              <span className="text-sm font-semibold">Vertice Studio</span>
            </div>
            <div className="flex gap-8 text-sm text-gray-500">
              <Link href="#" className="hover:text-primary transition-colors">Privacy Policy</Link>
              <Link href="#" className="hover:text-primary transition-colors">Terms of Service</Link>
            </div>
            <div className="flex gap-6">
              <Link href="#" className="text-gray-500 hover:text-primary transition-colors">
                <span className="material-symbols-outlined">public</span>
              </Link>
              <Link href="#" className="text-gray-500 hover:text-primary transition-colors">
                <span className="material-symbols-outlined">code</span>
              </Link>
              <Link href="#" className="text-gray-500 hover:text-primary transition-colors">
                <span className="material-symbols-outlined">forum</span>
              </Link>
            </div>
          </div>
          <div className="mt-8 text-center text-xs text-gray-600 md:text-left">
            © 2026 Vertice Studio. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

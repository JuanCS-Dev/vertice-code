import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft, MessageSquare, CreditCard, Shield, Terminal, Users, Cpu } from 'lucide-react';

export const metadata = {
  title: 'Vertice Code | User Manual',
  description: 'Complete documentation for the Vertice Code ecosystem.',
};

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-zinc-300 font-sans selection:bg-primary/20">

      {/* Navbar */}
      <header className="h-16 border-b border-white/10 flex items-center px-6 sticky top-0 bg-[#050505]/95 backdrop-blur-md z-50">
        <Link href="/" className="mr-8 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="font-mono font-bold text-white tracking-widest">
          VERTICE<span className="text-primary">.DOCS</span>
        </div>
        <div className="ml-auto flex gap-4">
          <Link href="https://github.com/juan-dev/vertice-code" target="_blank" className="text-sm hover:text-white transition-colors">
            GitHub
          </Link>
          <Link href="/chat">
            <Button size="sm" variant="outline" className="font-mono text-xs border-primary/20 text-primary hover:bg-primary/10">
              OPEN CONSOLE
            </Button>
          </Link>
        </div>
      </header>

      <div className="container mx-auto flex pt-10 px-4 gap-12">

        {/* Sidebar */}
        <aside className="w-64 hidden lg:block sticky top-28 h-[calc(100vh-8rem)] overflow-y-auto pr-4">
          <nav className="space-y-8">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3">The Trinity</h3>
              <ul className="space-y-2 border-l border-white/10 ml-1">
                <li><a href="#chat-system" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Chat System (SaaS)</a></li>
                <li><a href="#tui-cli" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">TUI & CLI</a></li>
                <li><a href="#meta-agent" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Prometheus (L4)</a></li>
              </ul>
            </div>

            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Enterprise Core</h3>
              <ul className="space-y-2 border-l border-white/10 ml-1">
                <li><a href="#billing" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Billing & Plans</a></li>
                <li><a href="#security" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Security & Auth</a></li>
                <li><a href="#multi-tenancy" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Multi-Tenancy</a></li>
              </ul>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 max-w-3xl pb-20">

          {/* Introduction */}
          <div className="mb-16">
            <h1 className="text-4xl font-bold text-white tracking-tight mb-4">Vertice Code User Manual</h1>
            <p className="text-lg leading-relaxed text-zinc-400">
              Vertice Code is a <strong>Collective AI Platform</strong> designed for high-performance engineering teams.
              It unifies Human Intent, AI Execution, and Institutional Memory into a single "Trinity" system.
            </p>
          </div>

          <hr className="border-white/10 mb-16" />

          {/* Chat System */}
          <section id="chat-system" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <MessageSquare className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Chat System (SaaS)</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                The core interface for interacting with Vertice. It is not just a chatbot, but a
                <strong> stateful engineering partner</strong>. Acessible via <code>/chat</code>.
              </p>

              <h3 className="text-white text-xl font-bold mt-8 mb-4">Features</h3>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6 not-prose">
                <li className="bg-white/5 border border-white/10 p-4 rounded-lg">
                  <span className="text-white font-bold block mb-1">Streaming Protocol</span>
                  Real-time token generation with Vercel AI SDK Data Stream Protocol. Zero latency perception.
                </li>
                <li className="bg-white/5 border border-white/10 p-4 rounded-lg">
                  <span className="text-white font-bold block mb-1">ACID Persistence</span>
                  All conversations are stored in PostgreSQL with strict transaction integrity. History never vanishes.
                </li>
              </ul>

              <h3 className="text-white text-xl font-bold mt-8 mb-4">Model Selection</h3>
              <p>
                The system intelligent routes your request based on complexity:
              </p>
              <ul className="list-disc pl-4 space-y-2 mt-2">
                <li><strong>Gemini 1.5 Pro:</strong> For complex reasoning and architecture (Pro Tier).</li>
                <li><strong>Gemini 1.5 Flash:</strong> For high-speed tasks and simple queries (Free Tier).</li>
              </ul>
            </div>
          </section>

          {/* TUI & CLI */}
          <section id="tui-cli" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                <Terminal className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">TUI & CLI</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                The "Power User" interface. Designed for 10x Engineers who live in the terminal.
              </p>

              <div className="bg-[#0A0A0A] border border-white/10 rounded-xl p-6 my-6 font-mono text-sm">
                <p className="text-zinc-500 mb-2"># Install locally</p>
                <p className="text-white mb-4">$ pip install vertice-code</p>

                <p className="text-zinc-500 mb-2"># Launch TUI (Textual UI)</p>
                <p className="text-white mb-4">$ vertice</p>

                <p className="text-zinc-500 mb-2"># Run Headless command</p>
                <p className="text-white">$ vertice -p "Refactor src/main.py"</p>
              </div>

              <p>
                <strong>Note:</strong> The TUI renders at 60fps and supports mouse interaction.
                It connects to the same backend as the Web App, sharing memory and context.
              </p>
            </div>
          </section>

          {/* Prometheus */}
          <section id="meta-agent" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-red-500/10 rounded-lg text-red-400">
                <Cpu className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Prometheus Meta-Agent</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                <strong>Level 4 Autonomy.</strong> Prometheus is the "Self-Evolution" engine of Vertice.
                It runs in the background (CI/CD loop) to improve the codebase without human intervention.
              </p>
              <ul className="list-disc pl-4 space-y-2 mt-4">
                <li><strong>Self-Correction:</strong> Detects bugs and proposes fixes (Tribunal System).</li>
                <li><strong>Evolution:</strong> Optimizes its own prompts and tools over time.</li>
                <li><strong>Verification:</strong> Runs `verify_prometheus.py` before every release to ensure sanity.</li>
              </ul>
            </div>
          </section>

          {/* Billing */}
          <section id="billing" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-green-500/10 rounded-lg text-green-400">
                <CreditCard className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Billing & Plans</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                Vertice offers transparent pricing integrated with <strong>Stripe</strong>.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-8 not-prose">
                {/* Free Tier */}
                <div className="border border-white/10 rounded-xl p-6 bg-white/5">
                  <h4 className="text-xl font-bold text-white mb-2">Free Tier</h4>
                  <p className="text-3xl font-bold text-white mb-4">$0<span className="text-sm font-normal text-zinc-500">/mo</span></p>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    <li className="flex items-center gap-2">✓ Gemini 1.5 Flash</li>
                    <li className="flex items-center gap-2">✓ Basic Chat History</li>
                    <li className="flex items-center gap-2">✓ Community Support</li>
                  </ul>
                </div>

                {/* Pro Tier */}
                <div className="border border-primary/20 rounded-xl p-6 bg-primary/5 relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-primary text-black text-xs font-bold px-3 py-1">POPULAR</div>
                  <h4 className="text-xl font-bold text-white mb-2">Pro Tier</h4>
                  <p className="text-3xl font-bold text-white mb-4">$29<span className="text-sm font-normal text-zinc-500">/mo</span></p>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    <li className="flex items-center gap-2">✓ Gemini 1.5 Pro (Enterprise)</li>
                    <li className="flex items-center gap-2">✓ Unlimited History</li>
                    <li className="flex items-center gap-2">✓ TUI & CLI Access</li>
                    <li className="flex items-center gap-2">✓ Priority Processing</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Security */}
          <section id="security" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                <Shield className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Security & Auth</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                Security is not an addon; it is the foundation. We employ a <strong>Zero-Trust Architecture</strong>.
              </p>
              <ul className="list-disc pl-4 space-y-2 mt-4">
                <li><strong>Authentication:</strong> Google OAuth 2.0 via Firebase Admin.</li>
                <li><strong>Token Revocation:</strong> Logging out instantly invalidates access tokens globally. No "zombie sessions".</li>
                <li><strong>Rate Limiting:</strong> DDoS protection active on all API endpoints.</li>
                <li><strong>Auditing:</strong> All sensitive actions are logged in an immutable audit trail.</li>
              </ul>
            </div>
          </section>

          {/* Multi-Tenancy */}
          <section id="multi-tenancy" className="mb-20 scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-yellow-500/10 rounded-lg text-yellow-400">
                <Users className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Multi-Tenancy</h2>
            </div>
            <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
              <p>
                Your data is yours. Vertice uses <strong>Strict Logical Isolation</strong> to ensure no data leakage between tenants.
              </p>
              <p>
                Every resource (chat, document, setting) is tagged with a unique `tenant_id`.
                The backend middleware enforces this isolation at the database query level.
                We permit <strong>NO CROSS-TENANT ACCESS</strong>, verified by our `verify_multitenancy.py` E2E test.
              </p>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}

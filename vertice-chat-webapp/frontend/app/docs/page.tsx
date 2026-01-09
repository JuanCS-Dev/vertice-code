import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Book, Code, Terminal, Shield } from 'lucide-react';

export const metadata = {
  title: 'Documentation | Vertice-Code',
  description: 'The Sovereign Developer Manual',
};

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-zinc-300 font-sans selection:bg-primary/20">
      
      {/* Navbar */}
      <header className="h-16 border-b border-white/10 flex items-center px-6 sticky top-0 bg-[#050505]/80 backdrop-blur-md z-50">
        <Link href="/" className="mr-8 hover:text-white transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="font-mono font-bold text-white tracking-widest">
          VERTICE<span className="text-primary">.DOCS</span>
        </div>
        <div className="ml-auto">
            <Link href="/chat">
                <Button size="sm" variant="outline" className="font-mono text-xs border-primary/20 text-primary hover:bg-primary/10">
                    OPEN CONSOLE
                </Button>
            </Link>
        </div>
      </header>

      <div className="container mx-auto flex pt-10 px-4 gap-12">
        
        {/* Sidebar */}
        <aside className="w-64 hidden lg:block sticky top-28 h-[calc(100vh-8rem)]">
          <nav className="space-y-8">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Core Concepts</h3>
              <ul className="space-y-2 border-l border-white/10 ml-1">
                <li><a href="#philosophy" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Sovereign Philosophy</a></li>
                <li><a href="#architecture" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">System Architecture</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Features</h3>
              <ul className="space-y-2 border-l border-white/10 ml-1">
                <li><a href="#chat" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Generative Chat</a></li>
                <li><a href="#artifacts" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">Artifacts Canvas</a></li>
                <li><a href="#github" className="block pl-4 border-l border-transparent hover:border-primary hover:text-primary transition-all text-sm">GitHub Deep Sync</a></li>
              </ul>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 max-w-3xl pb-20">
            
            <section id="philosophy" className="mb-16">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <Shield className="h-6 w-6" />
                    </div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">The Sovereign Philosophy</h1>
                </div>
                <div className="prose prose-invert prose-p:text-zinc-400 prose-headings:text-white max-w-none">
                    <p className="text-lg leading-relaxed">
                        Vertice-Code is not a tool; it is a manifesto. In an age of "AI Wrappers" and dependency hell, 
                        we believe in <strong className="text-white">Sovereign Intelligence</strong>.
                    </p>
                    <p>
                        Your code, your reasoning, and your infrastructure should belong to you. 
                        Vertice acts as a bridge between human intent (Divine Inspiration) and machine execution (Absolute Precision), 
                        without the noise of intermediary SaaS bloat.
                    </p>
                </div>
            </section>

            <section id="artifacts" className="mb-16">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <Code className="h-6 w-6" />
                    </div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">Artifacts Canvas</h2>
                </div>
                <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
                    <p>
                        Stop copying and pasting code. The Artifacts Canvas is a live, sandboxed environment where 
                        Vertice generates full-stack components, scripts, and documents.
                    </p>
                    <div className="bg-[#0A0A0A] border border-white/10 rounded-xl p-6 my-6">
                        <h4 className="text-sm font-bold text-white uppercase mb-4">How to use</h4>
                        <ol className="space-y-3 list-decimal list-inside text-sm">
                            <li>Ask Vertice to <code className="text-primary">"Create a React component for a sales chart"</code></li>
                            <li>The <strong>Canvas</strong> will open automatically on the right.</li>
                            <li>You can <strong>Edit</strong> the code directly (Monaco Editor).</li>
                            <li>The <strong>Preview</strong> updates instantly as you type or as the AI generates.</li>
                        </ol>
                    </div>
                </div>
            </section>

            <section id="github" className="mb-16">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                        <Terminal className="h-6 w-6" />
                    </div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">GitHub Deep Sync</h2>
                </div>
                <div className="prose prose-invert prose-p:text-zinc-400 max-w-none">
                    <p>
                        Vertice doesn't just read your code; it lives in your repository.
                        By installing the Vertice GitHub App, you enable autonomous code reviews and pull request management.
                    </p>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6 not-prose">
                        <li className="bg-white/5 border border-white/10 p-4 rounded-lg">
                            <span className="text-primary font-bold block mb-1">Auto-Review</span>
                            Detects security flaws and anti-patterns in every PR.
                        </li>
                        <li className="bg-white/5 border border-white/10 p-4 rounded-lg">
                            <span className="text-primary font-bold block mb-1">Self-Healing</span>
                            Suggests fixes and can commit them directly if authorized.
                        </li>
                    </ul>
                </div>
            </section>

        </main>
      </div>
    </div>
  );
}

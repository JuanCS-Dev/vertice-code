'use client';

import { DemoPlaceholder } from '@/components/landing/demo-placeholder';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { ArrowRight, Terminal, Zap, Shield, Globe } from 'lucide-react';

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const handleStart = () => {
    if (user) {
      router.push('/chat');
    } else {
      router.push('/sign-in');
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-foreground flex flex-col items-center p-4 overflow-x-hidden selection:bg-primary/20">
        {/* Ambient Glows */}
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[100px] pointer-events-none" />

        {/* Hero Section */}
        <section className="text-center space-y-8 max-w-4xl pt-32 pb-16 relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <div className="inline-flex items-center gap-2 px-3 py-1 border border-primary/20 rounded-full bg-primary/5 text-primary text-[10px] font-mono tracking-[0.2em] uppercase mb-4 shadow-[0_0_15px_rgba(212,255,0,0.1)]">
                <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
                Sovereign Intelligence • V3.0
            </div>
            
            <h1 className="text-6xl md:text-8xl font-bold tracking-tight text-white">
                Code at the edge of <br />
                <span className="text-primary neon-text italic">Consciousness</span>
            </h1>
            
            <p className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed font-mono">
                Forget wrappers. Vertice is a sovereign development engine where 
                <span className="text-white"> divine inspiration</span> meets 
                <span className="text-white"> alien-grade precision</span>.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                <Button 
                    onClick={handleStart}
                    size="lg" 
                    className="text-lg px-10 h-14 rounded-xl font-bold shadow-[0_0_30px_rgba(212,255,0,0.2)] hover:shadow-[0_0_40px_rgba(212,255,0,0.4)] transition-all bg-primary text-black hover:bg-primary/90 group"
                >
                    {loading ? "Initializing..." : "Start Creating"} 
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Link href="/docs">
                    <Button variant="outline" size="lg" className="text-lg px-10 h-14 rounded-xl border-white/10 hover:bg-white/5 hover:text-white transition-all bg-transparent font-mono text-zinc-400">
                        View Codex
                    </Button>
                </Link>
            </div>
        </section>

        {/* Features Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full py-20 relative z-10">
            <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-primary/20 transition-all group">
                <Terminal className="h-8 w-8 text-primary mb-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                <h3 className="text-white font-bold mb-2">Native Execution</h3>
                <p className="text-sm text-zinc-500 font-mono">Full-stack sandboxes integrated directly into your reasoning flow.</p>
            </div>
            <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-primary/20 transition-all group">
                <Shield className="h-8 w-8 text-primary mb-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                <h3 className="text-white font-bold mb-2">Self-Governing</h3>
                <p className="text-sm text-zinc-500 font-mono">Autonomous PR reviews and security hardening enforced by Noesis.</p>
            </div>
            <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-primary/20 transition-all group">
                <Globe className="h-8 w-8 text-primary mb-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                <h3 className="text-white font-bold mb-2">Global State</h3>
                <p className="text-sm text-zinc-500 font-mono">Your context follows you across terminal, web, and distributed nodes.</p>
            </div>
        </section>

        {/* Demo Section */}
        <div className="w-full px-4 animate-in fade-in slide-in-from-bottom-20 duration-1000 delay-300">
            <div className="text-center mb-8">
                <h2 className="text-sm font-bold text-zinc-700 tracking-[0.3em] uppercase">Observation Deck</h2>
            </div>
            <DemoPlaceholder />
        </div>
        
        {/* Footer */}
        <footer className="mt-32 py-12 text-center border-t border-white/5 w-full bg-[#080808]">
            <div className="flex justify-center gap-8 mb-6">
                <Link href="https://github.com/JuanCS-Dev/vertice-code" className="text-zinc-600 hover:text-primary transition-colors font-mono text-xs">GITHUB</Link>
                <Link href="/docs" className="text-zinc-600 hover:text-primary transition-colors font-mono text-xs">CODEX</Link>
                <Link href="/admin" className="text-zinc-600 hover:text-primary transition-colors font-mono text-xs">SOVEREIGN</Link>
            </div>
            <p className="font-mono text-[9px] text-zinc-700 tracking-tighter uppercase opacity-50">
                © 2026 Vertice AI. This is a Sovereign Node.
            </p>
        </footer>
    </div>
  );
}
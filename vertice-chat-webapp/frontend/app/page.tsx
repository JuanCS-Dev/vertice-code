'use client';

import { DemoPlaceholder } from '@/components/landing/demo-placeholder';
import { PricingSection } from '@/components/landing/pricing-section';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { ArrowRight, Terminal, Shield, Globe, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

// Stats Data
const STATS = [
    { value: '97', label: 'AI Agents', suffix: '+' },
    { value: '46', label: 'Native Tools', suffix: '' },
    { value: '5', label: 'LLM Providers', suffix: '' },
    { value: '∞', label: 'Context Window', suffix: '' },
];

// Tech Stack
const TECH_STACK = [
    { name: 'Vertex AI', icon: '🧠' },
    { name: 'Firebase', icon: '🔥' },
    { name: 'Cloud Run', icon: '☁️' },
    { name: 'Stripe', icon: '💳' },
    { name: 'Gemini', icon: '♊' },
];

function FeatureCard({ icon, title, description, delay }: { icon: React.ReactNode, title: string, description: string, delay: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay }}
            className="p-8 rounded-2xl bg-white/[0.02] border border-white/[0.06] hover:border-cyan-500/30 hover:bg-white/[0.04] transition-all duration-500 group relative overflow-hidden"
        >
            {/* Gradient border on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/10 to-blue-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative z-10">
                <div className="mb-6 bg-white/[0.03] w-14 h-14 rounded-xl flex items-center justify-center border border-white/[0.05] group-hover:border-cyan-500/30 group-hover:bg-cyan-500/10 transition-all duration-300 group-hover:scale-110">
                    {icon}
                </div>
                <h3 className="text-xl text-white font-semibold mb-3 tracking-wide group-hover:text-cyan-100 transition-colors">{title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed font-light group-hover:text-zinc-400 transition-colors">
                    {description}
                </p>
            </div>
        </motion.div>
    );
}

function StatCard({ value, label, suffix, delay }: { value: string, label: string, suffix: string, delay: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay }}
            className="text-center p-6 rounded-xl bg-white/[0.02] border border-white/5 hover:border-cyan-500/20 transition-all duration-300"
        >
            <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                {value}<span className="text-cyan-400">{suffix}</span>
            </div>
            <div className="text-xs text-zinc-500 uppercase tracking-widest font-medium">{label}</div>
        </motion.div>
    );
}

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
        <div className="flex flex-col min-h-screen bg-[#050505] text-foreground font-sans selection:bg-cyan-500/20">

            {/* Navigation Bar */}
            <nav className="fixed top-0 w-full z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="font-mono font-bold text-white tracking-widest text-lg">
                        VERTICE<span className="text-cyan-400">.AI</span>
                    </Link>
                    <div className="hidden md:flex items-center gap-8">
                        <a href="#features" className="text-sm text-zinc-500 hover:text-white transition-colors">Features</a>
                        <a href="#stats" className="text-sm text-zinc-500 hover:text-white transition-colors">Stats</a>
                        <a href="#pricing" className="text-sm text-zinc-500 hover:text-white transition-colors">Pricing</a>
                        <Link href="/docs" className="text-sm text-zinc-500 hover:text-white transition-colors">Docs</Link>
                    </div>
                    <Button onClick={handleStart} size="sm" className="bg-white text-black hover:bg-zinc-200 font-medium">
                        {user ? 'Console' : 'Sign In'}
                    </Button>
                </div>
            </nav>

            {/* Ambient Background */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3], x: [0, 50, 0], y: [0, -50, 0] }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] bg-cyan-500/10 rounded-full blur-[150px] mix-blend-screen"
                />
                <motion.div
                    animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3], x: [0, -30, 0], y: [0, 50, 0] }}
                    transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                    className="absolute bottom-[-10%] right-[-5%] w-[50vw] h-[50vw] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen"
                />
            </div>

            <main className="flex-grow w-full relative z-10 flex flex-col items-center justify-center pt-16">
                {/* Hero Section */}
                <section className="relative w-full max-w-7xl mx-auto px-6 pt-24 pb-32 flex flex-col items-center justify-center min-h-[85vh]">

                    {/* Badge */}
                    <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="mb-10">
                        <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] backdrop-blur-md shadow-[0_0_15px_-5px_rgba(6,182,212,0.3)] hover:bg-white/[0.05] hover:border-cyan-500/30 transition-all duration-300">
                            <div className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.8)]"></span>
                            </div>
                            <span className="text-[12px] font-medium tracking-[0.2em] text-cyan-100/80 uppercase">
                                Host: Vertice-AI <span className="mx-2 text-white/20">|</span> v3.0 Active
                            </span>
                        </div>
                    </motion.div>

                    {/* Headline */}
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1, delay: 0.2 }} className="text-center mb-10">
                        <h1 className="text-5xl sm:text-6xl md:text-8xl font-medium tracking-tight text-white leading-[1.1]">
                            The interface for<br />
                            <span className="relative inline-block pb-4 mt-2">
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#e2e8f0] via-[#22d3ee] to-[#3b82f6] animate-gradient-fast">
                                    Fluid Intelligence
                                </span>
                                <span className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-blue-600/10 blur-3xl -z-10 animate-pulse-slow"></span>
                            </span>
                        </h1>
                    </motion.div>

                    {/* Subheadline */}
                    <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4 }} className="text-lg md:text-xl text-zinc-400 text-center max-w-2xl leading-relaxed font-light mb-12 mx-auto">
                        A sovereign environment where reasoning meets execution.<br className="hidden md:block" />
                        <span className="text-zinc-300">Think. Iterate. Deploy.</span>
                    </motion.p>

                    {/* CTAs */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }} className="flex flex-col sm:flex-row gap-6 w-full justify-center items-center">
                        <Button onClick={handleStart} size="lg" className="h-14 px-10 rounded-xl bg-white text-black hover:bg-zinc-200 font-semibold text-base transition-all min-w-[180px] shadow-[0_0_20px_-5px_rgba(255,255,255,0.4)] hover:shadow-[0_0_30px_-5px_rgba(255,255,255,0.6)] hover:scale-105">
                            {loading ? "Initializing..." : "Initialize Session"}
                            <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                        <Link href="/docs">
                            <Button variant="ghost" size="lg" className="h-14 px-10 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.05] border border-white/10 hover:border-white/30 font-medium text-base transition-all min-w-[180px]">
                                <Terminal className="mr-2 h-5 w-5" />
                                View Codex
                            </Button>
                        </Link>
                    </motion.div>
                </section>

                {/* Features Grid */}
                <section id="features" className="w-full max-w-7xl mx-auto px-6 mb-32 scroll-mt-20">
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }} className="text-center mb-16">
                        <h2 className="text-3xl font-semibold text-white mb-4">Built Different</h2>
                        <p className="text-zinc-500">Not another wrapper. A sovereign development engine.</p>
                    </motion.div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard icon={<Terminal className="h-6 w-6 text-cyan-400" />} title="Native Execution" description="Full-stack sandboxes integrated directly into your reasoning flow. No more context switching." delay={0.8} />
                        <FeatureCard icon={<Shield className="h-6 w-6 text-cyan-400" />} title="Self-Governing" description="Autonomous PR reviews and security hardening enforced by Noesis. Zero-trust by default." delay={0.9} />
                        <FeatureCard icon={<Globe className="h-6 w-6 text-cyan-400" />} title="Global State" description="Your context follows you across terminal, web, and distributed nodes. Omnipresence achieved." delay={1.0} />
                    </div>
                </section>

                {/* Stats Section */}
                <section id="stats" className="w-full max-w-5xl mx-auto px-6 mb-32 scroll-mt-20">
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }} className="text-center mb-12">
                        <h2 className="text-2xl font-semibold text-white mb-2">By The Numbers</h2>
                        <p className="text-zinc-600 text-sm">The machinery behind the magic</p>
                    </motion.div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {STATS.map((stat, i) => (
                            <StatCard key={stat.label} value={stat.value} label={stat.label} suffix={stat.suffix} delay={1.2 + i * 0.1} />
                        ))}
                    </div>
                </section>

                {/* Tech Stack Section */}
                <section className="w-full max-w-4xl mx-auto px-6 mb-32">
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }} className="text-center mb-10">
                        <p className="text-xs text-zinc-600 uppercase tracking-widest mb-6">Powered By</p>
                        <div className="flex flex-wrap justify-center gap-8">
                            {TECH_STACK.map((tech) => (
                                <div key={tech.name} className="flex items-center gap-2 px-4 py-2 bg-white/[0.02] border border-white/5 rounded-full hover:border-white/10 transition-colors">
                                    <span className="text-lg">{tech.icon}</span>
                                    <span className="text-sm text-zinc-500">{tech.name}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </section>

                {/* Quote Section */}
                <section className="w-full max-w-3xl mx-auto px-6 mb-32">
                    <motion.blockquote initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }} className="text-center p-10 bg-white/[0.01] border border-white/5 rounded-2xl">
                        <Sparkles className="h-6 w-6 text-cyan-400 mx-auto mb-6" />
                        <p className="text-xl md:text-2xl text-zinc-300 font-light leading-relaxed mb-6 italic">
                            &quot;The best code is the code you never had to write. The second best is the code an AI writes while understanding your intent.&quot;
                        </p>
                        <cite className="text-sm text-zinc-600 not-italic">— The Vertice Manifesto</cite>
                    </motion.blockquote>
                </section>

                {/* Pricing Section */}
                <section id="pricing" className="w-full relative z-10 scroll-mt-20">
                    <PricingSection />
                </section>

                {/* Demo */}
                <div className="w-full max-w-6xl mx-auto px-6 mb-20">
                    <div className="flex items-center justify-center gap-6 mb-12 opacity-30">
                        <div className="h-px w-24 bg-gradient-to-r from-transparent to-white" />
                        <span className="text-[10px] font-mono text-white tracking-[0.5em] uppercase">System Observation Deck</span>
                        <div className="h-px w-24 bg-gradient-to-l from-transparent to-white" />
                    </div>
                    <div className="rounded-2xl overflow-hidden border border-white/10 shadow-[0_0_100px_-20px_rgba(0,0,0,0.8)] bg-[#0A0A0A] relative group">
                        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                        <DemoPlaceholder />
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="w-full py-8 text-center border-t border-white/5 bg-[#030303] relative z-10">
                <div className="flex justify-center gap-8 mb-4">
                    <Link href="https://github.com/JuanCS-Dev/vertice-code" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">GitHub</Link>
                    <Link href="/docs" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Codex</Link>
                    <Link href="/admin" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Sovereign</Link>
                    <Link href="/privacy" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Privacy</Link>
                    <Link href="/terms" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Terms</Link>
                </div>
                <p className="text-[10px] text-zinc-700 font-mono tracking-widest uppercase opacity-50">
                    © 2026 Vertice AI • Sovereign Node
                </p>
            </footer>
        </div>
    );
}
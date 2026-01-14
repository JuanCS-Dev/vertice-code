'use client';

import { DemoPlaceholder } from '@/components/landing/demo-placeholder';
import { PricingSection } from '@/components/landing/pricing-section';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { ArrowRight, Terminal, Zap, Shield, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

function FeatureCard({ icon, title, description, delay }: { icon: React.ReactNode, title: string, description: string, delay: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay }}
            className="p-8 rounded-2xl bg-white/[0.02] border border-white/[0.06] hover:border-white/10 hover:bg-white/[0.04] transition-all duration-300 group"
        >
            <div className="mb-6 bg-white/[0.03] w-12 h-12 rounded-lg flex items-center justify-center border border-white/[0.05] group-hover:border-white/10 transition-colors">
                {icon}
            </div>
            <h3 className="text-xl text-white font-medium mb-3 tracking-wide">{title}</h3>
            <p className="text-sm text-zinc-500 leading-relaxed font-light">
                {description}
            </p>
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
            {/* Ambient Background - Living & Breathing */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <motion.div
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                        x: [0, 50, 0],
                        y: [0, -50, 0]
                    }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] bg-cyan-500/10 rounded-full blur-[150px] mix-blend-screen"
                />
                <motion.div
                    animate={{
                        scale: [1, 1.1, 1],
                        opacity: [0.3, 0.6, 0.3],
                        x: [0, -30, 0],
                        y: [0, 50, 0]
                    }}
                    transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                    className="absolute bottom-[-10%] right-[-5%] w-[50vw] h-[50vw] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen"
                />
                <motion.div
                    animate={{
                        opacity: [0.01, 0.03, 0.01]
                    }}
                    transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.02] bg-center"
                />
            </div>

            <main className="flex-grow w-full relative z-10 flex flex-col items-center justify-center">
                {/* Hero Section */}
                <section className="relative w-full max-w-7xl mx-auto px-6 pt-32 pb-40 flex flex-col items-center justify-center min-h-[90vh]">

                    {/* Badge - Alien Glass */}
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="mb-10"
                    >
                        <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] backdrop-blur-md shadow-[0_0_15px_-5px_rgba(6,182,212,0.3)] hover:bg-white/[0.05] hover:border-cyan-500/30 transition-all duration-300 group cursor-default">
                            <div className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.8)]"></span>
                            </div>
                            <span className="text-[12px] font-medium tracking-[0.2em] text-cyan-100/80 uppercase group-hover:text-cyan-200 transition-colors">
                                Host: Vertice-AI
                                <span className="mx-2 text-white/20">|</span>
                                v3.0 Active
                            </span>
                        </div>
                    </motion.div>

                    {/* Headline - Massive & Glowing */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }} // Custom ease
                        className="text-center mb-10 relative z-20"
                    >
                        <h1 className="text-5xl sm:text-6xl md:text-8xl font-medium tracking-tight text-white leading-[1.1] md:leading-[1.1]">
                            The interface for<br />
                            <span className="relative inline-block pb-4 mt-2">
                                {/* Gradient Text - Fixed for Tailwind v4 (Explicit Colors) */}
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#e2e8f0] via-[#22d3ee] to-[#3b82f6] animate-gradient-fast backdrop-blur-sm relative z-10">
                                    Fluid Intelligence
                                </span>
                                {/* Glow Effect Behind */}
                                <span className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-blue-600/10 blur-3xl -z-10 animate-pulse-slow"></span>
                            </span>
                        </h1>
                    </motion.div>

                    {/* Subheadline - Glassy & Crisp */}
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.4 }}
                        className="text-lg md:text-xl text-zinc-400 text-center max-w-2xl leading-relaxed font-light mb-12 tracking-wide mx-auto"
                    >
                        A sovereign environment where reasoning meets execution.<br className="hidden md:block" />
                        <span className="text-zinc-300">Think. Iterate. Deploy.</span>
                    </motion.p>

                    {/* CTAs - High Performance */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.6 }}
                        className="flex flex-col sm:flex-row gap-6 w-full justify-center items-center"
                    >
                        <Button
                            onClick={handleStart}
                            size="lg"
                            className="h-14 px-10 rounded-xl bg-white text-black hover:bg-zinc-200 font-semibold text-base transition-all min-w-[180px] shadow-[0_0_20px_-5px_rgba(255,255,255,0.4)] hover:shadow-[0_0_30px_-5px_rgba(255,255,255,0.6)] hover:scale-105"
                        >
                            {loading ? "Initializing..." : "Initialize Session"}
                            <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                        <Link href="/docs">
                            <Button variant="ghost" size="lg" className="h-14 px-10 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.05] border border-white/10 hover:border-white/30 font-medium text-base transition-all min-w-[180px] backdrop-blur-sm">
                                <Terminal className="mr-2 h-5 w-5" />
                                View Codex
                            </Button>
                        </Link>
                    </motion.div>
                </section>

                {/* Features Grid - Staggered Entry */}
                <div className="w-full max-w-7xl mx-auto px-6 mb-40">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={<Terminal className="h-6 w-6 text-cyan-400" />}
                            title="Native Execution"
                            description="Full-stack sandboxes integrated directly into your reasoning flow. No more context switching."
                            delay={0.8}
                        />
                        <FeatureCard
                            icon={<Shield className="h-6 w-6 text-cyan-400" />}
                            title="Self-Governing"
                            description="Autonomous PR reviews and security hardening enforced by Noesis. Zero-trust by default."
                            delay={0.9}
                        />
                        <FeatureCard
                            icon={<Globe className="h-6 w-6 text-cyan-400" />}
                            title="Global State"
                            description="Your context follows you across terminal, web, and distributed nodes. Omnipresence achieved."
                            delay={1.0}
                        />
                    </div>
                </div>

                {/* Pricing Section */}
                <section className="w-full relative z-10">
                    <PricingSection />
                </section>

                {/* Demo Placeholder */}
                <div className="w-full max-w-6xl mx-auto px-6 mb-20 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
                    <div className="flex items-center justify-center gap-6 mb-12 opacity-30">
                        <div className="h-px w-24 bg-gradient-to-r from-transparent to-white" />
                        <span className="text-[10px] font-mono text-white tracking-[0.5em] uppercase text-shadow-glow">System Observation Deck</span>
                        <div className="h-px w-24 bg-gradient-to-l from-transparent to-white" />
                    </div>
                    <div className="rounded-2xl overflow-hidden border border-white/10 shadow-[0_0_100px_-20px_rgba(0,0,0,0.8)] bg-[#0A0A0A] relative group">
                        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                        <DemoPlaceholder />
                    </div>
                </div>
            </main>

            <footer className="w-full py-8 text-center border-t border-white/5 bg-[#030303] relative z-10">
                <div className="flex justify-center gap-8 mb-4">
                    <Link href="https://github.com/JuanCS-Dev/vertice-code" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">GitHub</Link>
                    <Link href="/docs" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Codex</Link>
                    <Link href="/admin" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs font-medium">Sovereign</Link>
                </div>
                <p className="text-[10px] text-zinc-700 font-mono tracking-widest uppercase opacity-50">
                    © 2026 Vertice AI • Sovereign Node
                </p>
            </footer>
        </div>
    );
}
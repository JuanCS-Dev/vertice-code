/**
 * Vertice Code - The AI-Native Web IDE
 * 
 * "The Operating System for AI Engineers"
 * 
 * Features:
 * - Immersive Cyberpunk/Dark UI
 * - Framer Motion Animations
 * - Interactive Terminal Simulation
 * - Clear Value Proposition for "Web Code App"
 */
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Terminal, 
  Cpu, 
  Shield, 
  Zap, 
  Globe, 
  Code2, 
  Bot, 
  Layers,
  ArrowRight,
  Play,
  Command
} from 'lucide-react';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!loading && user) {
      router.push('/chat');
    }
  }, [user, loading, router]);

  if (!mounted || loading) return null;

  if (user) return null; // Will redirect

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white selection:bg-cyan-500/30 overflow-x-hidden">
      
      {/* Background Grid Effect */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent"></div>
      </div>

      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">Vertice<span className="text-cyan-500">Code</span></span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="https://github.com/vertice-ai" className="text-sm text-zinc-400 hover:text-white transition-colors hidden md:block">GitHub</Link>
            <Link href="/docs" className="text-sm text-zinc-400 hover:text-white transition-colors hidden md:block">Documentation</Link>
            <Link href="/sign-in">
              <Button variant="ghost" className="text-zinc-300 hover:text-white hover:bg-white/5">Sign In</Button>
            </Link>
            <Link href="/sign-up">
              <Button className="bg-cyan-500 hover:bg-cyan-400 text-black font-semibold shadow-lg shadow-cyan-500/20 transition-all">
                Start Coding
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 overflow-hidden">
        <div className="container mx-auto relative z-10">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            
            {/* Hero Text */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="lg:w-1/2 text-center lg:text-left"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-cyan-400 mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                v2.0 Public Beta is Live
              </div>
              
              <h1 className="text-5xl lg:text-7xl font-bold leading-tight mb-6 tracking-tight">
                The <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">OS</span> for <br/>
                AI Engineers
              </h1>
              
              <p className="text-xl text-zinc-400 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                Stop coding alone. Vertice Code orchestrates autonomous squads of agents to build, test, and deploy your software in a secure WebAssembly sandbox.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
                <Link href="/sign-up" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto h-12 px-8 bg-white text-black hover:bg-zinc-200 font-bold text-base">
                    <Command className="w-4 h-4 mr-2" /> Launch Terminal
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="w-full sm:w-auto h-12 px-8 border-white/20 hover:bg-white/5 hover:text-white hover:border-white/40">
                  <Play className="w-4 h-4 mr-2" /> Watch Demo
                </Button>
              </div>

              <div className="mt-10 flex items-center justify-center lg:justify-start gap-4 text-sm text-zinc-500">
                <div className="flex items-center gap-1">
                  <Shield className="w-4 h-4" /> ISO 42001 Ready
                </div>
                <div className="w-1 h-1 bg-zinc-700 rounded-full"></div>
                <div className="flex items-center gap-1">
                  <Zap className="w-4 h-4" /> Wasm Speed
                </div>
                <div className="w-1 h-1 bg-zinc-700 rounded-full"></div>
                <div className="flex items-center gap-1">
                  <Globe className="w-4 h-4" /> Global CDN
                </div>
              </div>
            </motion.div>

            {/* Hero Visual (Mock IDE) */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="lg:w-1/2 w-full"
            >
              <div className="relative rounded-xl border border-white/10 bg-[#0f0f0f] shadow-2xl shadow-cyan-500/10 overflow-hidden group">
                {/* Window Controls */}
                <div className="h-10 border-b border-white/5 bg-[#1a1a1a] flex items-center px-4 justify-between">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <div className="text-xs text-zinc-500 font-mono">agent_orchestrator.py — Vertice IDE</div>
                  <div className="w-10"></div>
                </div>

                {/* IDE Content */}
                <div className="p-6 font-mono text-sm leading-6 h-[400px] overflow-hidden relative">
                  {/* Glowing Effect behind text */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-cyan-500/5 rounded-full blur-[100px] pointer-events-none"></div>
                  
                  <div className="flex">
                    <div className="text-zinc-700 mr-4 select-none text-right w-8">
                      1<br/>2<br/>3<br/>4<br/>5<br/>6<br/>7<br/>8<br/>9<br/>10<br/>11
                    </div>
                    <div>
                      <span className="text-purple-400">import</span> <span className="text-white">vertice</span> <span className="text-purple-400">as</span> <span className="text-white">vt</span>
                      <br/><br/>
                      <span className="text-zinc-500"># Define an autonomous squad</span><br/>
                      <span className="text-blue-400">squad</span> = vt.<span className="text-yellow-300">create_squad</span>([<br/>
                      &nbsp;&nbsp;vt.Agent(role=<span className="text-green-400">"Architect"</span>),<br/>
                      &nbsp;&nbsp;vt.Agent(role=<span className="text-green-400">"Engineer"</span>, language=<span className="text-green-400">"rust"</span>),<br/>
                      &nbsp;&nbsp;vt.Agent(role=<span className="text-green-400">"QA"</span>)<br/>
                      ])<br/><br/>
                      <span className="text-zinc-500"># Execute mission in parallel</span><br/>
                      <span className="text-purple-400">await</span> squad.<span className="text-yellow-300">execute</span>(<br/>
                      &nbsp;&nbsp;<span className="text-green-400">"Refactor the billing module for high concurrency"</span><br/>
                      )<br/>
                      <span className="text-cyan-400 animate-pulse">_</span>
                    </div>
                  </div>
                </div>
                
                {/* Floating "AI Processing" Badge */}
                <div className="absolute bottom-6 right-6 bg-[#1a1a1a]/90 backdrop-blur border border-cyan-500/30 rounded-lg p-3 flex items-center gap-3 shadow-lg">
                  <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                  <div className="text-xs text-cyan-200">Architect Agent Planning...</div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-24 bg-[#050505]">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">Built for the <span className="text-cyan-500">Next Era</span> of Code</h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">Traditional IDEs were built for humans typing characters. Vertice is built for Squads generating systems.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Bot className="w-8 h-8 text-cyan-400" />}
              title="Multi-Agent Squads"
              description="Don't just chat with one bot. Spin up a specialized team (Architect, Dev, QA) that shares context and solves complex problems."
            />
            <FeatureCard 
              icon={<Cpu className="w-8 h-8 text-purple-400" />}
              title="Wasm Sandboxing"
              description="Execute untrusted AI-generated code securely in milliseconds using our specialized WebAssembly runtime."
            />
            <FeatureCard 
              icon={<Layers className="w-8 h-8 text-blue-400" />}
              title="Memory Vault"
              description="Persistent, vector-based memory that learns from your codebase and adapts to your team's coding style."
            />
            <FeatureCard 
              icon={<Code2 className="w-8 h-8 text-green-400" />}
              title="Live Preview"
              description="See your changes instantly. Vertice spins up ephemeral environments to render React, Python, and Node apps."
            />
            <FeatureCard 
              icon={<Shield className="w-8 h-8 text-red-400" />}
              title="Enterprise Grade"
              description="ISO 42001 ready. Role-based access control, audit logs, and on-premise deployment options."
            />
            <FeatureCard 
              icon={<Globe className="w-8 h-8 text-yellow-400" />}
              title="Merchant of Record"
              description="Monetize your agents. Built-in Stripe integration allows you to sell your specialized agents to other devs."
            />
          </div>
        </div>
      </section>

      {/* CTA Bottom */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0a] to-[#111] z-0"></div>
        <div className="container mx-auto px-6 relative z-10 text-center">
          <h2 className="text-4xl lg:text-5xl font-bold mb-8">Ready to upgrade your workflow?</h2>
          <Link href="/sign-up">
            <Button size="lg" className="h-14 px-10 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-lg shadow-lg shadow-cyan-500/25 rounded-full transition-all hover:scale-105">
              Get Started for Free
            </Button>
          </Link>
          <p className="mt-6 text-zinc-500 text-sm">No credit card required • Free tier includes 100k tokens/mo</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 bg-[#050505] text-sm">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-zinc-500" />
            <span className="font-semibold text-zinc-300">Vertice Code</span>
          </div>
          <div className="flex gap-8 text-zinc-500">
            <Link href="#" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms</Link>
            <Link href="#" className="hover:text-white transition-colors">Status</Link>
            <Link href="#" className="hover:text-white transition-colors">Twitter</Link>
          </div>
          <div className="text-zinc-600">
            © 2026 Vertice AI Inc.
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-[#111] border border-white/5 hover:border-white/10 transition-all hover:bg-[#151515] group">
      <div className="mb-4 p-3 bg-black/50 rounded-xl inline-block group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-2 text-zinc-100">{title}</h3>
      <p className="text-zinc-400 leading-relaxed">{description}</p>
    </div>
  );
}
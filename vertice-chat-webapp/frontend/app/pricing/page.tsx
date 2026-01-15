'use client';

import { PricingSection } from '@/components/landing/pricing-section';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PricingPage() {
    return (
        <div className="min-h-screen bg-[#050505] text-foreground font-sans selection:bg-cyan-500/20">
            {/* Ambient Background */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-cyan-500/5 rounded-full blur-[120px] mix-blend-screen" />
                <div className="absolute bottom-[-10%] right-[-5%] w-[40vw] h-[40vw] bg-blue-600/5 rounded-full blur-[100px] mix-blend-screen" />
            </div>

            {/* Header */}
            <header className="relative z-10 h-16 border-b border-white/5 flex items-center px-6 bg-[#050505]/95 backdrop-blur-md">
                <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-sm">Back to Home</span>
                </Link>
                <div className="mx-auto font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.PRICING</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative z-10 max-w-7xl mx-auto px-6 py-16">
                <PricingSection />

                {/* FAQ Section */}
                <section className="mt-24">
                    <h2 className="text-2xl font-semibold text-white text-center mb-12">
                        Frequently Asked Questions
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                            <h3 className="text-white font-medium mb-2">Can I switch plans?</h3>
                            <p className="text-zinc-500 text-sm">
                                Yes! You can upgrade or downgrade at any time. Changes take effect immediately.
                            </p>
                        </div>
                        <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                            <h3 className="text-white font-medium mb-2">What happens if I exceed my limits?</h3>
                            <p className="text-zinc-500 text-sm">
                                Overages are billed at the per-token rate for your plan. You can set alerts to avoid surprises.
                            </p>
                        </div>
                        <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                            <h3 className="text-white font-medium mb-2">Is there a free trial?</h3>
                            <p className="text-zinc-500 text-sm">
                                Developer and Team plans include a 14-day free trial. No credit card required.
                            </p>
                        </div>
                        <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                            <h3 className="text-white font-medium mb-2">What payment methods do you accept?</h3>
                            <p className="text-zinc-500 text-sm">
                                All major credit cards via Stripe. Enterprise plans support invoicing.
                            </p>
                        </div>
                    </div>
                </section>
            </main>

            {/* Footer */}
            <footer className="relative z-10 py-8 text-center border-t border-white/5 bg-[#030303]">
                <div className="flex justify-center gap-6 mb-3">
                    <Link href="/privacy" className="text-zinc-700 hover:text-zinc-400 transition-colors text-[10px]">Privacy</Link>
                    <Link href="/terms" className="text-zinc-700 hover:text-zinc-400 transition-colors text-[10px]">Terms</Link>
                </div>
                <p className="text-[10px] text-zinc-700 font-mono tracking-widest uppercase opacity-50">
                    © 2026 Vertice AI • Sovereign Node
                </p>
            </footer>
        </div>
    );
}

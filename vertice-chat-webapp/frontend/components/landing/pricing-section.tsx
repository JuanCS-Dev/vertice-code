'use client';

import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface PricingTier {
    name: string;
    price: string;
    period: string;
    description: string;
    features: { name: string; included: boolean }[];
    cta: string;
    popular?: boolean;
    href: string;
}

const TIERS: PricingTier[] = [
    {
        name: 'Free',
        price: '$0',
        period: '/forever',
        description: 'Start exploring the future of code.',
        features: [
            { name: '1,000 tokens/day', included: true },
            { name: '5 chat sessions', included: true },
            { name: 'Basic artifacts', included: true },
            { name: 'TUI access', included: false },
            { name: 'MCP integration', included: false },
            { name: 'Priority models', included: false },
        ],
        cta: 'Get Started',
        href: '/sign-up?plan=free',
    },
    {
        name: 'Developer',
        price: '$19',
        period: '/month',
        description: 'For individual builders shipping fast.',
        features: [
            { name: '50k tokens/day', included: true },
            { name: 'Unlimited chat', included: true },
            { name: 'Full artifacts system', included: true },
            { name: 'TUI access', included: true },
            { name: 'MCP integration', included: false },
            { name: 'Priority models', included: false },
        ],
        cta: 'Start Free Trial',
        popular: true,
        href: '/sign-up?plan=developer',
    },
    {
        name: 'Team',
        price: '$49',
        period: '/seat/month',
        description: 'Collaborative AI for ambitious teams.',
        features: [
            { name: '200k tokens/day per seat', included: true },
            { name: 'Unlimited everything', included: true },
            { name: 'Full artifacts + sharing', included: true },
            { name: 'TUI + CLI access', included: true },
            { name: 'MCP integration', included: true },
            { name: 'Priority models', included: true },
        ],
        cta: 'Contact Sales',
        href: '/sign-up?plan=team',
    },
];

export function PricingSection() {
    return (
        <section className="w-full py-24">
            {/* Header */}
            <div className="text-center mb-16">
                <div className="flex items-center justify-center gap-4 mb-6 opacity-40">
                    <div className="h-px w-16 bg-gradient-to-r from-transparent to-white/30" />
                    <span className="text-[10px] font-mono text-white tracking-[0.3em] uppercase">Pricing</span>
                    <div className="h-px w-16 bg-gradient-to-l from-transparent to-white/30" />
                </div>
                <h2 className="text-4xl font-semibold text-white mb-4">
                    Choose Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Power Level</span>
                </h2>
                <p className="text-zinc-400 max-w-xl mx-auto">
                    Pay only for what you use. Scale as you grow. Cancel anytime.
                </p>
            </div>

            {/* Pricing Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                {TIERS.map((tier) => (
                    <div
                        key={tier.name}
                        className={cn(
                            "relative p-8 rounded-2xl border transition-all duration-300",
                            tier.popular
                                ? "bg-white/[0.04] border-cyan-500/30 hover:border-cyan-500/50 shadow-[0_0_40px_rgba(34,211,238,0.1)]"
                                : "bg-white/[0.02] border-white/5 hover:border-white/10 hover:bg-white/[0.04]"
                        )}
                    >
                        {/* Popular Badge */}
                        {tier.popular && (
                            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                <span className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest bg-cyan-500 text-black rounded-full">
                                    Most Popular
                                </span>
                            </div>
                        )}

                        {/* Tier Header */}
                        <div className="mb-6">
                            <h3 className="text-lg font-medium text-white mb-1">{tier.name}</h3>
                            <p className="text-zinc-500 text-sm">{tier.description}</p>
                        </div>

                        {/* Price */}
                        <div className="mb-6">
                            <span className="text-4xl font-bold text-white">{tier.price}</span>
                            <span className="text-zinc-500 text-sm">{tier.period}</span>
                        </div>

                        {/* Features */}
                        <ul className="space-y-3 mb-8">
                            {tier.features.map((feature) => (
                                <li key={feature.name} className="flex items-center gap-3 text-sm">
                                    {feature.included ? (
                                        <Check className="h-4 w-4 text-cyan-400 shrink-0" />
                                    ) : (
                                        <X className="h-4 w-4 text-zinc-600 shrink-0" />
                                    )}
                                    <span className={feature.included ? "text-zinc-300" : "text-zinc-600"}>
                                        {feature.name}
                                    </span>
                                </li>
                            ))}
                        </ul>

                        {/* CTA */}
                        <Link href={tier.href} className="block">
                            <Button
                                className={cn(
                                    "w-full h-11 rounded-lg font-medium text-sm transition-all",
                                    tier.popular
                                        ? "bg-white text-black hover:bg-zinc-200"
                                        : "bg-white/5 text-white hover:bg-white/10 border border-white/10"
                                )}
                            >
                                {tier.cta}
                            </Button>
                        </Link>
                    </div>
                ))}
            </div>

            {/* Enterprise CTA */}
            <div className="text-center mt-12">
                <p className="text-zinc-500 text-sm mb-4">
                    Need custom limits, SLAs, or dedicated support?
                </p>
                <Link href="/sign-up?plan=enterprise">
                    <Button variant="ghost" className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10">
                        Contact for Enterprise →
                    </Button>
                </Link>
            </div>
        </section>
    );
}

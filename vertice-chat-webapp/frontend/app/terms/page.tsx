import Link from 'next/link';
import { ArrowLeft, FileText, Scale, AlertTriangle, CreditCard, XCircle, Globe } from 'lucide-react';

export const metadata = {
    title: 'Terms of Service | Vertice Code',
    description: 'Terms and conditions for using Vertice Code platform.',
};

const SECTIONS = [
    {
        id: 'acceptance',
        icon: FileText,
        iconColor: 'text-cyan-400',
        title: '1. Acceptance of Terms',
        content: `By accessing or using Vertice Code ("Service"), you agree to be bound by these Terms of Service ("Terms").
    If you do not agree, do not use the Service. We reserve the right to update these Terms at any time.`,
    },
    {
        id: 'license',
        icon: Scale,
        iconColor: 'text-green-400',
        title: '2. License Grant',
        content: `We grant you a limited, non-exclusive, non-transferable, revocable license to use the Service for your
    internal business or personal purposes. This license does not include the right to sublicense, resell, or redistribute the Service.`,
    },
    {
        id: 'restrictions',
        icon: AlertTriangle,
        iconColor: 'text-yellow-400',
        title: '3. Prohibited Uses',
        items: [
            'Reverse engineering, decompiling, or attempting to extract source code',
            'Using the Service to generate harmful, illegal, or malicious content',
            'Circumventing usage limits or authentication mechanisms',
            'Sharing account credentials or API keys with third parties',
            'Automated scraping or excessive API calls beyond rate limits',
        ],
    },
    {
        id: 'billing',
        icon: CreditCard,
        iconColor: 'text-blue-400',
        title: '4. Billing & Payments',
        content: `Paid subscriptions are billed in advance on a monthly or annual basis. All fees are non-refundable except
    as required by law. We use Stripe for payment processing. You are responsible for providing accurate billing information.`,
    },
    {
        id: 'termination',
        icon: XCircle,
        iconColor: 'text-red-400',
        title: '5. Termination',
        content: `We may suspend or terminate your access at any time for violation of these Terms or for any other reason
    with 30 days notice. Upon termination, your right to use the Service ceases immediately. You may export your data
    before termination via our GDPR endpoints.`,
    },
];

const JURISDICTIONS = [
    { flag: '🇧🇷', country: 'Brazil', court: 'São Paulo, SP', law: 'Brazilian Civil Code' },
    { flag: '🇺🇸', country: 'United States', court: 'Delaware', law: 'Delaware General Corporation Law' },
    { flag: '🇪🇺', country: 'European Union', court: 'Dublin, Ireland', law: 'Irish Contract Law + GDPR' },
];

export default function TermsPage() {
    return (
        <div className="min-h-screen bg-[#050505] text-zinc-300 font-sans selection:bg-primary/20">

            {/* Header */}
            <header className="h-16 border-b border-white/10 flex items-center px-6 sticky top-0 bg-[#050505]/95 backdrop-blur-md z-50">
                <Link href="/" className="mr-8 hover:text-white transition-colors">
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <div className="font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.TERMS</span>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-16">

                {/* Title */}
                <div className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 bg-cyan-500/10 rounded-xl">
                            <FileText className="h-8 w-8 text-cyan-400" />
                        </div>
                        <h1 className="text-4xl font-bold text-white tracking-tight">Terms of Service</h1>
                    </div>
                    <p className="text-lg text-zinc-400 leading-relaxed">
                        Effective: January 2026. By using Vertice Code, you agree to these terms.
                    </p>
                </div>

                {/* Sections */}
                <div className="space-y-12 mb-16">
                    {SECTIONS.map((section) => (
                        <section key={section.id} id={section.id} className="scroll-mt-24">
                            <div className="flex items-center gap-3 mb-4">
                                <section.icon className={`h-5 w-5 ${section.iconColor}`} />
                                <h2 className="text-xl font-bold text-white">{section.title}</h2>
                            </div>
                            {section.content && (
                                <p className="text-zinc-400 leading-relaxed pl-8">{section.content}</p>
                            )}
                            {section.items && (
                                <ul className="pl-8 space-y-2 mt-4">
                                    {section.items.map((item, idx) => (
                                        <li key={idx} className="flex items-start gap-3 text-zinc-400">
                                            <span className="text-red-500 mt-1">•</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    ))}
                </div>

                {/* Jurisdiction */}
                <section className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <Globe className="h-5 w-5 text-purple-400" />
                        <h2 className="text-xl font-bold text-white">6. Governing Law & Jurisdiction</h2>
                    </div>
                    <p className="text-zinc-400 mb-6 pl-8">
                        Disputes will be resolved in the courts of your country of residence:
                    </p>
                    <div className="grid md:grid-cols-3 gap-4">
                        {JURISDICTIONS.map((j) => (
                            <div key={j.country} className="p-5 bg-white/[0.02] border border-white/5 rounded-xl">
                                <div className="text-2xl mb-2">{j.flag}</div>
                                <h3 className="text-white font-medium mb-1">{j.country}</h3>
                                <p className="text-sm text-zinc-500">Court: {j.court}</p>
                                <p className="text-xs text-zinc-600 mt-1">{j.law}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Disclaimer */}
                <section className="mb-16 p-6 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
                    <h2 className="text-lg font-bold text-yellow-400 mb-3">7. Disclaimer of Warranties</h2>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                        THE SERVICE IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTY OF ANY KIND. WE DISCLAIM ALL WARRANTIES,
                        EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
                        WE DO NOT GUARANTEE UNINTERRUPTED ACCESS OR ERROR-FREE OPERATION.
                    </p>
                </section>

                {/* Limitation of Liability */}
                <section className="mb-16 p-6 bg-red-500/5 border border-red-500/20 rounded-xl">
                    <h2 className="text-lg font-bold text-red-400 mb-3">8. Limitation of Liability</h2>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                        IN NO EVENT SHALL VERTICE AI BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL,
                        OR PUNITIVE DAMAGES. OUR TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT PAID BY YOU IN THE 12 MONTHS
                        PRECEDING THE CLAIM.
                    </p>
                </section>

                {/* Contact */}
                <section className="p-6 bg-white/[0.02] border border-white/5 rounded-xl text-center">
                    <h2 className="text-xl font-bold text-white mb-2">Questions?</h2>
                    <p className="text-zinc-500 text-sm">
                        Contact us at{' '}
                        <a href="mailto:legal@vertice.ai" className="text-cyan-400 hover:underline">
                            legal@vertice.ai
                        </a>
                    </p>
                </section>

            </main>

            {/* Footer */}
            <footer className="w-full py-8 text-center border-t border-white/5 bg-[#030303]">
                <div className="flex justify-center gap-6 mb-3">
                    <Link href="/" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs">Home</Link>
                    <Link href="/privacy" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs">Privacy Policy</Link>
                </div>
                <p className="text-[10px] text-zinc-700 font-mono tracking-widest uppercase opacity-50">
                    © 2026 Vertice AI • Sovereign Node
                </p>
            </footer>
        </div>
    );
}

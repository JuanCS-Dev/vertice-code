import Link from 'next/link';
import { ArrowLeft, Shield, Globe, Database, Clock, Users, FileDown, Trash2, Edit } from 'lucide-react';

export const metadata = {
    title: 'Privacy Policy | Vertice Code',
    description: 'How Vertice Code collects, uses, and protects your data across Brazil (LGPD), EU (GDPR), and US (CCPA).',
};

const DATA_COLLECTED = [
    { category: 'Account Data', items: 'Email, name, profile picture', purpose: 'Authentication and personalization' },
    { category: 'Usage Data', items: 'Chat history, feature usage, performance metrics', purpose: 'Service improvement and billing' },
    { category: 'Technical Data', items: 'IP address (anonymized), device info, browser type', purpose: 'Security and debugging' },
];

const DATA_RETENTION = [
    { type: 'Chat History', period: '30 days', reason: 'Active session support' },
    { type: 'Account Data', period: 'Account active + 3 years', reason: 'Legal compliance' },
    { type: 'Billing Records', period: '7 years', reason: 'Tax and regulatory requirements' },
];

const DATA_SHARING = [
    { recipient: 'Google Cloud (Firestore)', purpose: 'Database storage', location: 'Multi-region' },
    { recipient: 'Google Vertex AI', purpose: 'AI model inference', location: 'United States' },
    { recipient: 'Stripe', purpose: 'Payment processing', location: 'United States' },
];

const USER_RIGHTS = [
    { right: 'Access', description: 'Request a copy of all your data', endpoint: '/api/gdpr/data-access', icon: FileDown },
    { right: 'Rectification', description: 'Correct inaccurate personal data', endpoint: '/api/gdpr/data-rectification', icon: Edit },
    { right: 'Erasure', description: 'Request deletion of your data', endpoint: '/api/gdpr/data-erasure', icon: Trash2 },
    { right: 'Portability', description: 'Export your data in JSON format', endpoint: '/api/gdpr/data-portability', icon: FileDown },
];

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-[#050505] text-zinc-300 font-sans selection:bg-primary/20">

            {/* Header */}
            <header className="h-16 border-b border-white/10 flex items-center px-6 sticky top-0 bg-[#050505]/95 backdrop-blur-md z-50">
                <Link href="/" className="mr-8 hover:text-white transition-colors">
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <div className="font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.PRIVACY</span>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-16">

                {/* Title */}
                <div className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 bg-cyan-500/10 rounded-xl">
                            <Shield className="h-8 w-8 text-cyan-400" />
                        </div>
                        <h1 className="text-4xl font-bold text-white tracking-tight">Privacy Policy</h1>
                    </div>
                    <p className="text-lg text-zinc-400 leading-relaxed">
                        Last updated: January 2026. This policy applies to users in Brazil (LGPD),
                        European Union (GDPR), and United States (CCPA).
                    </p>
                </div>

                {/* Data Collection */}
                <section className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <Database className="h-5 w-5 text-blue-400" />
                        <h2 className="text-2xl font-bold text-white">Data We Collect</h2>
                    </div>
                    <div className="space-y-4">
                        {DATA_COLLECTED.map((item) => (
                            <div key={item.category} className="p-5 bg-white/[0.02] border border-white/5 rounded-xl">
                                <h3 className="text-white font-medium mb-1">{item.category}</h3>
                                <p className="text-sm text-zinc-500 mb-2">{item.items}</p>
                                <p className="text-xs text-zinc-600">Purpose: {item.purpose}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Data Retention */}
                <section className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <Clock className="h-5 w-5 text-yellow-400" />
                        <h2 className="text-2xl font-bold text-white">Data Retention</h2>
                    </div>
                    <div className="overflow-hidden rounded-xl border border-white/5">
                        <table className="w-full text-sm">
                            <thead className="bg-white/[0.02]">
                                <tr>
                                    <th className="text-left p-4 text-zinc-400 font-medium">Data Type</th>
                                    <th className="text-left p-4 text-zinc-400 font-medium">Retention Period</th>
                                    <th className="text-left p-4 text-zinc-400 font-medium">Reason</th>
                                </tr>
                            </thead>
                            <tbody>
                                {DATA_RETENTION.map((item) => (
                                    <tr key={item.type} className="border-t border-white/5">
                                        <td className="p-4 text-white">{item.type}</td>
                                        <td className="p-4 text-cyan-400 font-mono">{item.period}</td>
                                        <td className="p-4 text-zinc-500">{item.reason}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>

                {/* Data Sharing */}
                <section className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <Users className="h-5 w-5 text-purple-400" />
                        <h2 className="text-2xl font-bold text-white">Data Sharing</h2>
                    </div>
                    <p className="text-zinc-400 mb-6">
                        We share data only with essential service providers. We do NOT sell your data.
                    </p>
                    <div className="grid gap-4">
                        {DATA_SHARING.map((item) => (
                            <div key={item.recipient} className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-xl">
                                <div>
                                    <span className="text-white font-medium">{item.recipient}</span>
                                    <span className="text-zinc-600 text-sm ml-2">— {item.purpose}</span>
                                </div>
                                <span className="text-xs text-zinc-600 bg-white/5 px-2 py-1 rounded">{item.location}</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Your Rights */}
                <section className="mb-16">
                    <div className="flex items-center gap-3 mb-6">
                        <Globe className="h-5 w-5 text-green-400" />
                        <h2 className="text-2xl font-bold text-white">Your Rights (LGPD / GDPR / CCPA)</h2>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                        {USER_RIGHTS.map((item) => (
                            <div key={item.right} className="p-5 bg-white/[0.02] border border-white/5 rounded-xl hover:border-cyan-500/30 transition-colors">
                                <div className="flex items-center gap-3 mb-2">
                                    <item.icon className="h-4 w-4 text-cyan-400" />
                                    <h3 className="text-white font-medium">Right to {item.right}</h3>
                                </div>
                                <p className="text-sm text-zinc-500 mb-3">{item.description}</p>
                                <code className="text-xs text-cyan-400/70 bg-cyan-500/5 px-2 py-1 rounded font-mono">
                                    {item.endpoint}
                                </code>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Regional Compliance */}
                <section className="mb-16">
                    <h2 className="text-2xl font-bold text-white mb-6">Regional Compliance</h2>
                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="p-5 bg-green-500/5 border border-green-500/20 rounded-xl">
                            <h3 className="text-green-400 font-bold mb-2">🇧🇷 LGPD (Brazil)</h3>
                            <p className="text-sm text-zinc-500">Lei Geral de Proteção de Dados. Full compliance with Articles 7, 15, 16, 17, and 18.</p>
                        </div>
                        <div className="p-5 bg-blue-500/5 border border-blue-500/20 rounded-xl">
                            <h3 className="text-blue-400 font-bold mb-2">🇪🇺 GDPR (EU)</h3>
                            <p className="text-sm text-zinc-500">General Data Protection Regulation. Articles 15-20 fully implemented.</p>
                        </div>
                        <div className="p-5 bg-red-500/5 border border-red-500/20 rounded-xl">
                            <h3 className="text-red-400 font-bold mb-2">🇺🇸 CCPA (California)</h3>
                            <p className="text-sm text-zinc-500">California Consumer Privacy Act. Right to know, delete, and opt-out supported.</p>
                        </div>
                    </div>
                </section>

                {/* Contact */}
                <section className="p-6 bg-white/[0.02] border border-white/5 rounded-xl text-center">
                    <h2 className="text-xl font-bold text-white mb-2">Questions?</h2>
                    <p className="text-zinc-500 text-sm">
                        Contact our Data Protection Officer at{' '}
                        <a href="mailto:privacy@vertice.ai" className="text-cyan-400 hover:underline">
                            privacy@vertice.ai
                        </a>
                    </p>
                </section>

            </main>

            {/* Footer */}
            <footer className="w-full py-8 text-center border-t border-white/5 bg-[#030303]">
                <div className="flex justify-center gap-6 mb-3">
                    <Link href="/" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs">Home</Link>
                    <Link href="/terms" className="text-zinc-600 hover:text-cyan-400 transition-colors text-xs">Terms of Service</Link>
                </div>
                <p className="text-[10px] text-zinc-700 font-mono tracking-widest uppercase opacity-50">
                    © 2026 Vertice AI • Sovereign Node
                </p>
            </footer>
        </div>
    );
}

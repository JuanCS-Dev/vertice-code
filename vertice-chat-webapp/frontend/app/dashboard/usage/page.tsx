'use client';

import { useAuth } from '@/context/auth-context';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { ArrowLeft, BarChart3, Calendar, TrendingUp } from 'lucide-react';

interface DailyUsage {
    date: string;
    tokens: number;
    sessions: number;
}

const MOCK_USAGE: DailyUsage[] = [
    { date: '2026-01-14', tokens: 12450, sessions: 7 },
    { date: '2026-01-13', tokens: 45200, sessions: 12 },
    { date: '2026-01-12', tokens: 38000, sessions: 9 },
    { date: '2026-01-11', tokens: 22500, sessions: 5 },
    { date: '2026-01-10', tokens: 31000, sessions: 8 },
    { date: '2026-01-09', tokens: 28700, sessions: 6 },
    { date: '2026-01-08', tokens: 41000, sessions: 11 },
];

function UsageContent() {
    const { user } = useAuth();
    const totalTokens = MOCK_USAGE.reduce((acc, d) => acc + d.tokens, 0);
    const totalSessions = MOCK_USAGE.reduce((acc, d) => acc + d.sessions, 0);
    const avgDaily = Math.round(totalTokens / MOCK_USAGE.length);

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            {/* Header */}
            <header className="h-16 border-b border-white/5 flex items-center px-6 bg-[#050505]/95 backdrop-blur-md">
                <Link href="/dashboard" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-sm">Back to Dashboard</span>
                </Link>
                <div className="mx-auto font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.USAGE</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-5xl mx-auto px-6 py-8">
                <h1 className="text-2xl font-semibold text-white mb-8">Usage Analytics</h1>

                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-cyan-500/10 rounded-lg">
                                <BarChart3 className="h-4 w-4 text-cyan-400" />
                            </div>
                            <span className="text-sm font-medium text-zinc-400">Total Tokens (7d)</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{totalTokens.toLocaleString()}</div>
                    </div>

                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Calendar className="h-4 w-4 text-primary" />
                            </div>
                            <span className="text-sm font-medium text-zinc-400">Total Sessions (7d)</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{totalSessions}</div>
                    </div>

                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-green-500/10 rounded-lg">
                                <TrendingUp className="h-4 w-4 text-green-400" />
                            </div>
                            <span className="text-sm font-medium text-zinc-400">Avg Daily Tokens</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{avgDaily.toLocaleString()}</div>
                    </div>
                </div>

                {/* Usage Table */}
                <div className="rounded-2xl bg-[#0A0A0A] border border-white/5 overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/5 bg-white/[0.02]">
                        <h2 className="text-sm font-bold uppercase tracking-widest text-zinc-400">Daily Breakdown</h2>
                    </div>
                    <table className="w-full">
                        <thead className="bg-black/40 text-zinc-500 text-xs uppercase tracking-widest">
                            <tr>
                                <th className="px-6 py-4 text-left">Date</th>
                                <th className="px-6 py-4 text-right">Tokens</th>
                                <th className="px-6 py-4 text-right">Sessions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {MOCK_USAGE.map((day) => (
                                <tr key={day.date} className="hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4 text-white font-mono text-sm">{day.date}</td>
                                    <td className="px-6 py-4 text-right text-zinc-300">{day.tokens.toLocaleString()}</td>
                                    <td className="px-6 py-4 text-right text-zinc-300">{day.sessions}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </main>
        </div>
    );
}

export default function UsagePage() {
    return (
        <ProtectedRoute>
            <UsageContent />
        </ProtectedRoute>
    );
}

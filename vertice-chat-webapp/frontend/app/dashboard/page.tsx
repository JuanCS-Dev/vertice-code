'use client';

import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { ArrowLeft, Zap, CreditCard, Settings, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface UsageStats {
    tokensUsed: number;
    tokensLimit: number;
    sessionsToday: number;
    currentPlan: string;
    billingCycle: string;
}

function DashboardContent() {
    const { user } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<UsageStats>({
        tokensUsed: 12450,
        tokensLimit: 50000,
        sessionsToday: 7,
        currentPlan: 'Developer',
        billingCycle: 'Jan 1 - Jan 31, 2026',
    });

    const usagePercent = Math.round((stats.tokensUsed / stats.tokensLimit) * 100);

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            {/* Header */}
            <header className="h-16 border-b border-white/5 flex items-center px-6 bg-[#050505]/95 backdrop-blur-md">
                <Link href="/chat" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-sm">Back to Chat</span>
                </Link>
                <div className="mx-auto font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.DASHBOARD</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-sm font-bold">
                        {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-6xl mx-auto px-6 py-8">
                {/* Welcome */}
                <div className="mb-8">
                    <h1 className="text-2xl font-semibold text-white">
                        Welcome back, {user?.displayName?.split(' ')[0] || 'Developer'}
                    </h1>
                    <p className="text-zinc-500 text-sm mt-1">
                        {stats.currentPlan} Plan • {stats.billingCycle}
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
                    {/* Usage Card */}
                    <div className="md:col-span-2 p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-cyan-500/10 rounded-lg">
                                    <Zap className="h-4 w-4 text-cyan-400" />
                                </div>
                                <span className="text-sm font-medium text-zinc-400">Token Usage</span>
                            </div>
                            <span className="text-xs text-zinc-600">{usagePercent}% used</span>
                        </div>
                        <div className="text-3xl font-bold text-white mb-2">
                            {stats.tokensUsed.toLocaleString()} <span className="text-zinc-500 text-lg font-normal">/ {stats.tokensLimit.toLocaleString()}</span>
                        </div>
                        <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all"
                                style={{ width: `${usagePercent}%` }}
                            />
                        </div>
                    </div>

                    {/* Sessions Card */}
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <BarChart3 className="h-4 w-4 text-primary" />
                            </div>
                            <span className="text-sm font-medium text-zinc-400">Sessions</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{stats.sessionsToday}</div>
                        <div className="text-xs text-zinc-600 mt-1">Today</div>
                    </div>

                    {/* Plan Card */}
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-2 bg-green-500/10 rounded-lg">
                                <CreditCard className="h-4 w-4 text-green-400" />
                            </div>
                            <span className="text-sm font-medium text-zinc-400">Plan</span>
                        </div>
                        <div className="text-xl font-bold text-white">{stats.currentPlan}</div>
                        <Link href="/pricing" className="text-xs text-cyan-400 mt-1 hover:underline">
                            Upgrade →
                        </Link>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Link href="/dashboard/usage" className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all group">
                        <BarChart3 className="h-6 w-6 text-cyan-400 mb-4" />
                        <h3 className="text-lg font-medium text-white mb-1">Usage Analytics</h3>
                        <p className="text-sm text-zinc-500">View detailed usage history and trends</p>
                    </Link>

                    <Link href="/dashboard/settings" className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all group">
                        <Settings className="h-6 w-6 text-cyan-400 mb-4" />
                        <h3 className="text-lg font-medium text-white mb-1">Account Settings</h3>
                        <p className="text-sm text-zinc-500">Manage profile, API keys, and preferences</p>
                    </Link>

                    <Link href="/pricing" className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all group">
                        <CreditCard className="h-6 w-6 text-cyan-400 mb-4" />
                        <h3 className="text-lg font-medium text-white mb-1">Billing & Plans</h3>
                        <p className="text-sm text-zinc-500">Manage subscription and payment methods</p>
                    </Link>
                </div>
            </main>
        </div>
    );
}

export default function DashboardPage() {
    return (
        <ProtectedRoute>
            <DashboardContent />
        </ProtectedRoute>
    );
}

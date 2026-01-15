'use client';

import { useAuth } from '@/context/auth-context';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { ArrowLeft, User, Key, Bell, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

function SettingsContent() {
    const { user } = useAuth();

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            {/* Header */}
            <header className="h-16 border-b border-white/5 flex items-center px-6 bg-[#050505]/95 backdrop-blur-md">
                <Link href="/dashboard" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-sm">Back to Dashboard</span>
                </Link>
                <div className="mx-auto font-mono font-bold text-white tracking-widest">
                    VERTICE<span className="text-cyan-400">.SETTINGS</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-3xl mx-auto px-6 py-8">
                <h1 className="text-2xl font-semibold text-white mb-8">Account Settings</h1>

                {/* Profile Section */}
                <section className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                            <User className="h-4 w-4 text-cyan-400" />
                        </div>
                        <h2 className="text-lg font-medium text-white">Profile</h2>
                    </div>
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5 space-y-4">
                        <div>
                            <Label className="text-zinc-400 text-sm">Email</Label>
                            <Input
                                value={user?.email || ''}
                                disabled
                                className="mt-1 bg-white/5 border-white/10 text-white"
                            />
                        </div>
                        <div>
                            <Label className="text-zinc-400 text-sm">Display Name</Label>
                            <Input
                                defaultValue={user?.displayName || ''}
                                className="mt-1 bg-white/5 border-white/10 text-white"
                                placeholder="Your name"
                            />
                        </div>
                        <Button className="bg-white text-black hover:bg-zinc-200">
                            Save Changes
                        </Button>
                    </div>
                </section>

                {/* API Keys Section */}
                <section className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                            <Key className="h-4 w-4 text-cyan-400" />
                        </div>
                        <h2 className="text-lg font-medium text-white">API Keys</h2>
                    </div>
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <p className="text-zinc-500 text-sm mb-4">
                            Generate API keys to access Vertice programmatically via CLI or MCP.
                        </p>
                        <Button variant="outline" className="border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/10">
                            Generate New Key
                        </Button>
                    </div>
                </section>

                {/* Notifications Section */}
                <section className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                            <Bell className="h-4 w-4 text-cyan-400" />
                        </div>
                        <h2 className="text-lg font-medium text-white">Notifications</h2>
                    </div>
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-white font-medium">Usage Alerts</p>
                                <p className="text-zinc-500 text-sm">Get notified when approaching usage limits</p>
                            </div>
                            <input type="checkbox" defaultChecked className="w-5 h-5 accent-cyan-500" />
                        </div>
                    </div>
                </section>

                {/* Security Section */}
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-red-500/10 rounded-lg">
                            <Shield className="h-4 w-4 text-red-400" />
                        </div>
                        <h2 className="text-lg font-medium text-white">Security</h2>
                    </div>
                    <div className="p-6 rounded-2xl bg-[#0A0A0A] border border-white/5">
                        <Button variant="outline" className="border-red-500/20 text-red-400 hover:bg-red-500/10">
                            Delete Account
                        </Button>
                    </div>
                </section>
            </main>
        </div>
    );
}

export default function SettingsPage() {
    return (
        <ProtectedRoute>
            <SettingsContent />
        </ProtectedRoute>
    );
}

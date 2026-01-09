'use client';

import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Activity, Users, AlertTriangle, Database, ArrowLeft } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import Link from 'next/link';

function AdminContent() {
  const { user } = useAuth();
  const router = useRouter();
  
  const [stats] = useState({
    users: 124,
    activeSessions: 18,
    errorRate: '0.2%',
    dbSize: '450MB'
  });

  useEffect(() => {
    if (user && user.email !== 'juancs.d3v@gmail.com') {
      router.push('/chat');
    }
  }, [user, router]);

  return (
    <div className="min-h-screen bg-[#050505] text-white p-8 font-sans selection:bg-primary/20">
      <header className="flex justify-between items-center mb-12">
        <div className="flex items-center gap-6">
            <Link href="/chat" className="p-2 hover:bg-white/5 rounded-lg transition-colors group">
                <ArrowLeft className="h-5 w-5 text-zinc-500 group-hover:text-white" />
            </Link>
            <div>
                <h1 className="text-3xl font-bold font-mono tracking-tight uppercase">Sovereign Control</h1>
                <p className="text-zinc-500 font-mono text-[10px] tracking-widest mt-1 uppercase">Node: GCP-VERTICE-AI-01</p>
            </div>
        </div>
        <div className="flex items-center gap-4 bg-primary/5 px-4 py-2 rounded-full border border-primary/10">
            <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(212,255,0,0.5)]"></div>
            <span className="text-[10px] font-bold font-mono text-primary uppercase tracking-widest">System Operational</span>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <div className="bg-[#0A0A0A] border border-white/5 p-6 rounded-2xl hover:border-primary/20 transition-all group">
            <div className="flex justify-between items-start mb-6">
                <div className="p-2.5 bg-blue-500/5 rounded-xl text-blue-400 group-hover:bg-blue-500/10 transition-colors">
                    <Users className="h-5 w-5" />
                </div>
                <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">Population</span>
            </div>
            <div className="text-4xl font-bold tracking-tighter">{stats.users}</div>
            <div className="text-[10px] text-green-500 mt-3 font-mono">↑ 12.4% WEEKLY_GROWTH</div>
        </div>

        <div className="bg-[#0A0A0A] border border-white/5 p-6 rounded-2xl hover:border-primary/20 transition-all group">
            <div className="flex justify-between items-start mb-6">
                <div className="p-2.5 bg-primary/5 rounded-xl text-primary group-hover:bg-primary/10 transition-colors">
                    <Activity className="h-5 w-5" />
                </div>
                <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">Neural Load</span>
            </div>
            <div className="text-4xl font-bold tracking-tighter">{stats.activeSessions}</div>
            <div className="text-[10px] text-zinc-500 mt-3 font-mono">PEAK_CONCURRENCY: 42</div>
        </div>

        <div className="bg-[#0A0A0A] border border-white/5 p-6 rounded-2xl hover:border-primary/20 transition-all group">
            <div className="flex justify-between items-start mb-6">
                <div className="p-2.5 bg-red-500/5 rounded-xl text-red-400 group-hover:bg-red-500/10 transition-colors">
                    <AlertTriangle className="h-5 w-5" />
                </div>
                <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">Integrity</span>
            </div>
            <div className="text-4xl font-bold tracking-tighter">{stats.errorRate}</div>
            <div className="text-[10px] text-zinc-500 mt-3 font-mono">STABLE_EQUILIBRIUM</div>
        </div>

        <div className="bg-[#0A0A0A] border border-white/5 p-6 rounded-2xl hover:border-primary/20 transition-all group">
            <div className="flex justify-between items-start mb-6">
                <div className="p-2.5 bg-purple-500/5 rounded-xl text-purple-400 group-hover:bg-purple-500/10 transition-colors">
                    <Database className="h-5 w-5" />
                </div>
                <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">Cortex Size</span>
            </div>
            <div className="text-4xl font-bold tracking-tighter">{stats.dbSize}</div>
            <div className="text-[10px] text-zinc-500 mt-3 font-mono">BACKEND: FIRESTORE_NATIVE</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-8 py-5 border-b border-white/5 flex justify-between items-center bg-white/[0.01]">
            <h3 className="font-bold text-xs uppercase tracking-[0.2em] text-zinc-400 flex items-center gap-3">
                <span className="w-1 h-1 bg-primary rounded-full animate-ping" />
                Access Frequency Logs
            </h3>
            <button className="text-[10px] font-bold text-primary uppercase tracking-widest hover:underline transition-all">Export CSV</button>
        </div>
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
                <thead className="bg-black/40 text-zinc-500 font-mono text-[10px] uppercase tracking-widest">
                    <tr>
                        <th className="px-8 py-4 border-b border-white/5">Principal Identity</th>
                        <th className="px-8 py-4 border-b border-white/5">Manifestation Type</th>
                        <th className="px-8 py-4 border-b border-white/5">Integrity Check</th>
                        <th className="px-8 py-4 border-b border-white/5">Temporal Sync</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                            <td className="px-8 py-5 text-zinc-300 group-hover:text-white transition-colors">user_{i}@Brainfarma.com</td>
                            <td className="px-8 py-5 text-zinc-500 uppercase tracking-tighter">React_Artifact_Generation</td>
                            <td className="px-8 py-5">
                                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-green-500/10 text-green-500 rounded-full text-[9px] font-bold uppercase tracking-widest border border-green-500/20">
                                    <div className="w-1 h-1 bg-green-500 rounded-full shadow-[0_0_5px_rgba(34,197,94,0.5)]" />
                                    PASSED
                                </span>
                            </td>
                            <td className="px-8 py-5 text-zinc-600">{i * 2} minutes ago</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute>
      <AdminContent />
    </ProtectedRoute>
  );
}
'use client';

import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/sign-in');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-2 border-primary border-t-transparent rounded-full animate-spin shadow-[0_0_15px_rgba(212,255,0,0.2)]" />
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-[0.3em]">Syncing Neural Link...</span>
        </div>
      </div>
    );
  }

  return user ? <>{children}</> : null;
}

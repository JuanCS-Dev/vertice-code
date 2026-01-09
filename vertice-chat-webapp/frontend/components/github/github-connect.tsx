'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Github, ExternalLink, ShieldCheck, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export function GitHubConnect() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = () => {
    setIsConnecting(true);
    // Simulate GitHub OAuth flow
    setTimeout(() => {
      setIsConnected(true);
      setIsConnecting(false);
    }, 2000);
  };

  return (
    <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-900 rounded-lg">
            <Github className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-white font-bold text-sm tracking-tight">GitHub Synchronization</h3>
            <p className="text-[10px] text-zinc-500 font-mono">Status: {isConnected ? "LINKED" : "UNLINKED"}</p>
          </div>
        </div>
        {isConnected && (
            <div className="flex items-center gap-1 text-[10px] text-primary font-bold uppercase tracking-widest bg-primary/10 px-2 py-1 rounded-full">
                <ShieldCheck className="h-3 w-3" /> Secure
            </div>
        )}
      </div>

      {!isConnected ? (
        <div className="space-y-4">
          <p className="text-xs text-zinc-400 leading-relaxed font-mono">
            Enable Vertice to manifest changes directly into your repositories. 
            Required for Auto-Review and Pull Request automation.
          </p>
          <Button 
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full bg-white hover:bg-zinc-200 text-black font-bold h-11"
          >
            {isConnecting ? (
                <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Connecting...
                </>
            ) : (
                <>
                    Connect Account
                    <ExternalLink className="ml-2 h-4 w-4" />
                </>
            )}
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
            <div className="p-4 rounded-xl bg-black/40 border border-white/5">
                <div className="flex justify-between items-center mb-3">
                    <span className="text-[10px] font-bold text-zinc-500 uppercase">Authenticated As</span>
                    <span className="text-[10px] font-mono text-zinc-600">ID: 123456</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-zinc-800 border border-white/10" />
                    <div>
                        <p className="text-sm font-bold text-white leading-none">JuanCS-Dev</p>
                        <p className="text-[10px] text-zinc-500 mt-1">Sovereign Architect</p>
                    </div>
                </div>
            </div>
            <Button 
                variant="outline" 
                className="w-full h-11 border-white/10 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/20 text-zinc-500 transition-all font-mono text-xs"
                onClick={() => setIsConnected(false)}
            >
                Terminate Connection
            </Button>
        </div>
      )}
    </div>
  );
}

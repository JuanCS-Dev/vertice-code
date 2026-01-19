'use client';

import { useEffect, useRef } from 'react';
import { MessageBubble } from './message-bubble';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Sparkles, Terminal, Code, Cpu } from 'lucide-react';

interface ChatMessagesProps {
  messages: any[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 h-full min-h-[500px] animate-in fade-in duration-1000">
        <div className="text-center space-y-10 max-w-2xl relative">
          {/* Decorative Elements */}
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative">
            <div className="w-20 h-20 rounded-3xl bg-[#0A0A0A] border border-primary/20 flex items-center justify-center mx-auto shadow-[0_0_40px_rgba(212,255,0,0.1)] relative z-10 group transition-all hover:border-primary/50">
                <Sparkles className="h-10 w-10 text-primary animate-pulse" />
            </div>
            {/* Orbital Rings */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 border border-white/5 rounded-full animate-[spin_10s_linear_infinite]" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-white/5 rounded-full animate-[spin_15s_linear_infinite_reverse]" />
          </div>

          <div className="space-y-4">
            <h2 className="text-4xl font-bold tracking-tighter text-white">
              Sovereign Console <span className="text-primary opacity-50 font-mono text-xl ml-2">v3.0</span>
            </h2>
            <p className="text-zinc-500 font-mono text-sm max-w-md mx-auto leading-relaxed">
              Connection established. The Architect is ready to manifest your intent into high-fidelity code.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
            <button className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] hover:border-primary/30 hover:bg-white/[0.04] transition-all group">
              <div className="flex items-center gap-3 mb-2">
                <Code className="h-4 w-4 text-primary opacity-50 group-hover:opacity-100" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">Blueprint</span>
              </div>
              <p className="text-xs text-zinc-500 group-hover:text-zinc-300 transition-colors">"Generate a React dashboard with real-time analytics..."</p>
            </button>

            <button className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] hover:border-primary/30 hover:bg-white/[0.04] transition-all group">
              <div className="flex items-center gap-3 mb-2">
                <Terminal className="h-4 w-4 text-primary opacity-50 group-hover:opacity-100" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">Logic Gate</span>
              </div>
              <p className="text-xs text-zinc-500 group-hover:text-zinc-300 transition-colors">"Explain the memory synchronization patterns in Rust..."</p>
            </button>
          </div>

          <div className="pt-8 flex items-center justify-center gap-6 opacity-30 grayscale hover:opacity-100 hover:grayscale-0 transition-all duration-500">
             <div className="flex flex-col items-center gap-1">
                <Cpu className="h-4 w-4" />
                <span className="text-[8px] font-mono uppercase tracking-tighter">Vertex AI</span>
             </div>
             <div className="w-1 h-1 rounded-full bg-zinc-800" />
             <div className="flex flex-col items-center gap-1">
                <div className="h-4 w-4 font-bold text-[10px] flex items-center justify-center">A</div>
                <span className="text-[8px] font-mono uppercase tracking-tighter">Anthropic</span>
             </div>
             <div className="w-1 h-1 rounded-full bg-zinc-800" />
             <div className="flex flex-col items-center gap-1">
                <div className="h-4 w-4 font-bold text-[10px] flex items-center justify-center italic">G</div>
                <span className="text-[8px] font-mono uppercase tracking-tighter">Gemini SOTA</span>
             </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 h-full pr-4">
      <div className="max-w-3xl mx-auto space-y-8 py-10">
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id || index}
            message={{
                ...message,
                role: message.role === 'data' ? 'assistant' : message.role
            }}
          />
        ))}

        {isLoading && (
          <div className="flex flex-col gap-3 p-5 rounded-2xl bg-primary/[0.02] border border-primary/10 max-w-[240px] animate-in fade-in slide-in-from-bottom-4 duration-500 shadow-xl">
            <div className="flex items-center gap-3 text-primary">
              <div className="relative">
                <Loader2 className="h-5 w-5 animate-spin" />
                <div className="absolute inset-0 bg-primary/20 blur-md rounded-full animate-pulse" />
              </div>
              <span className="text-[10px] font-bold tracking-[0.2em] uppercase neon-text">Synthesizing</span>
            </div>
            <div className="space-y-1.5">
                <div className="h-1 w-full bg-primary/10 rounded-full overflow-hidden">
                    <div className="h-full bg-primary animate-[shimmer_2s_infinite]" />
                </div>
                <div className="text-[9px] text-zinc-600 font-mono flex justify-between">
                    <span>REASONING ACTIVE</span>
                    <span className="animate-pulse">OPUS 4.5</span>
                </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} className="h-1" />
      </div>
    </ScrollArea>
  );
}

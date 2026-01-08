'use client';

import { useEffect, useRef } from 'react';
import { useCurrentSession } from '@/lib/stores/chat-store';
import { MessageBubble } from './message-bubble';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2 } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chat-store';

export function ChatMessages() {
  const session = useCurrentSession();
  const { isLoading } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages]);

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p>Selecione ou crie uma conversa</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="max-w-4xl mx-auto space-y-4">
        {session.messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <h2 className="text-xl font-semibold mb-2">
              Bem-vindo ao Vertice Chat
            </h2>
            <p className="text-sm mb-4">
              Comece uma conversa com nossa IA avançada
            </p>
            <div className="text-xs space-y-1 opacity-70">
              <p>• Suporte a múltiplos modelos (Claude, GPT, Gemini)</p>
              <p>• Execução segura de código</p>
              <p>• Artefatos e exportação</p>
            </div>
          </div>
        ) : (
          <>
            {session.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {isLoading && (
              <div className="flex flex-col gap-2 p-4 rounded-xl bg-cyan-500/5 border border-cyan-500/20 max-w-[200px]">
                <div className="flex items-center gap-2 text-cyan-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-xs font-bold tracking-widest uppercase">Noesis Active</span>
                </div>
                <div className="text-[10px] text-zinc-500 font-mono animate-pulse">
                  Opus 4.5 synthesizing...
                </div>
              </div>
            )}
          </>
        )}

        {/* Invisible element for scrolling */}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
}
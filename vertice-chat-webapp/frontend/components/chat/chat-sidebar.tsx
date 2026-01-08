'use client';

import { useState } from 'react';
import { useChatStore, useSessionsList } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Plus,
  MessageSquare,
  Trash2,
  MoreHorizontal,
  Settings
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

export function ChatSidebar() {
  const {
    currentSessionId,
    createSession,
    setCurrentSession,
    deleteSession,
    clearSession
  } = useChatStore();
  const sessions = useSessionsList();

  const handleNewChat = () => {
    createSession();
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Tem certeza que deseja excluir esta conversa?')) {
      deleteSession(sessionId);
    }
  };

  const handleClearSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Tem certeza que deseja limpar todas as mensagens desta conversa?')) {
      clearSession(sessionId);
    }
  };

  return (
    <div className="w-80 border-r border-zinc-800 flex flex-col bg-[#050505] text-zinc-400">
      {/* Sovereign Header */}
      <div className="p-6 border-b border-white/5 space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Plus className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-widest uppercase">Command Center</h2>
            <div className="text-[10px] text-cyan-500 font-mono tracking-tighter">SOVEREIGN MODE V3.0</div>
          </div>
        </div>
        
        <Button
          onClick={handleNewChat}
          className="w-full bg-zinc-900 border border-white/10 hover:bg-zinc-800 hover:border-cyan-500/50 text-zinc-300 transition-all duration-300"
          variant="outline"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nova Conversa
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-3">
          {sessions.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <div className="w-12 h-12 rounded-full bg-zinc-900 flex items-center justify-center mx-auto mb-4 opacity-20">
                <MessageSquare className="h-6 w-6" />
              </div>
              <p className="text-xs uppercase tracking-widest font-bold">No sessions found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    "group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-300",
                    currentSessionId === session.id 
                      ? "bg-cyan-500/5 border border-cyan-500/20 text-white shadow-[0_0_15px_rgba(6,182,212,0.05)]" 
                      : "hover:bg-zinc-900 border border-transparent text-zinc-500 hover:text-zinc-300"
                  )}
                  onClick={() => setCurrentSession(session.id)}
                >
                  {currentSessionId === session.id && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-cyan-500 rounded-r-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"></div>
                  )}
                  
                  <MessageSquare className={cn(
                    "h-4 w-4 flex-shrink-0 transition-colors",
                    currentSessionId === session.id ? "text-cyan-400" : "text-zinc-600 group-hover:text-zinc-400"
                  )} />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {session.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(session.updatedAt), {
                        addSuffix: true,
                        locale: ptBR
                      })}
                    </p>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => handleClearSession(session.id, e)}
                        className="text-orange-600"
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        Limpar Conversa
                      </DropdownMenuItem>
                      <Separator className="my-1" />
                      <DropdownMenuItem
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Excluir Conversa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
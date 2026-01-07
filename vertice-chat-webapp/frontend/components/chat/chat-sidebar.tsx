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
    <div className="w-80 border-r border-border flex flex-col bg-muted/10">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <Button
          onClick={handleNewChat}
          className="w-full justify-start"
          variant="outline"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nova Conversa
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {sessions.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Nenhuma conversa ainda</p>
              <p className="text-xs mt-1">Comece uma nova conversa</p>
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    "group flex items-center gap-2 p-3 rounded-lg cursor-pointer hover:bg-accent transition-colors",
                    currentSessionId === session.id && "bg-accent"
                  )}
                  onClick={() => setCurrentSession(session.id)}
                >
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />

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
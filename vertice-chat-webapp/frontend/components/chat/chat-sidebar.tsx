'use client';

import { useChatStore, useSessionsList } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Plus,
  MessageSquare,
  Trash2,
  MoreHorizontal,
  Settings,
  Book,
  ShieldAlert,
  LogOut,
  User as UserIcon
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { useAuth } from '@/context/auth-context';

export function ChatSidebar({ className }: { className?: string }) {
  const {
    currentSessionId,
    createSession,
    setCurrentSession,
    deleteSession,
  } = useChatStore();
  const sessions = useSessionsList();
  const { user, signOut } = useAuth();

  const handleNewChat = () => {
    createSession();
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this session?')) {
      deleteSession(sessionId);
    }
  };

  return (
    <div className={cn("w-80 border-r border-white/5 flex flex-col bg-[#050505] text-zinc-400 h-full", className)}>
      {/* Sovereign Header */}
      <div className="p-6 border-b border-white/5 space-y-4">
        <Link href="/" className="flex items-center gap-3 mb-2 group">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-[0_0_15px_rgba(212,255,0,0.3)] transition-transform group-hover:scale-105">
            <span className="text-black font-bold text-lg">V</span>
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-widest uppercase">Console</h2>
            <div className="text-[10px] text-primary font-mono tracking-tighter">SOVEREIGN V3.0</div>
          </div>
        </Link>
        
        <Button
          onClick={handleNewChat}
          className="w-full bg-primary text-black hover:bg-primary/90 font-bold border-none transition-all duration-300 shadow-[0_0_10px_rgba(212,255,0,0.1)]"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Session
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-3">
          {sessions.length === 0 ? (
            <div className="text-center text-zinc-600 py-12">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-20" />
              <p className="text-[10px] uppercase tracking-widest font-bold">No history</p>
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    "group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200",
                    currentSessionId === session.id 
                      ? "bg-white/5 text-white" 
                      : "hover:bg-white/5 text-zinc-500 hover:text-zinc-300"
                  )}
                  onClick={() => setCurrentSession(session.id)}
                >
                  <MessageSquare className={cn(
                    "h-4 w-4 flex-shrink-0",
                    currentSessionId === session.id ? "text-primary" : "text-zinc-700"
                  )} />

                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">
                      {session.title || "Untitled Session"}
                    </p>
                  </div>

                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-all"
                  >
                    <Trash2 className="h-3.3 w-3.3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer Navigation */}
      <div className="p-4 border-t border-white/5 bg-[#080808]">
        <nav className="space-y-1 mb-4">
            <Link href="/docs" className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 text-sm transition-colors group">
                <Book className="h-4 w-4 text-zinc-600 group-hover:text-primary" />
                <span>Documentation</span>
            </Link>
            
            {user?.email === 'juancs.d3v@gmail.com' && (
                <Link href="/admin" className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 text-sm transition-colors group">
                    <ShieldAlert className="h-4 w-4 text-zinc-600 group-hover:text-red-500" />
                    <span>Sovereign Control</span>
                </Link>
            )}
        </nav>

        <Separator className="bg-white/5 mb-4" />

        {/* User Section */}
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-full bg-zinc-900 border border-white/10 flex items-center justify-center overflow-hidden">
                    {user?.photoURL ? (
                        <img src={user.photoURL} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                        <UserIcon className="h-4 w-4 text-zinc-600" />
                    )}
                </div>
                <div className="min-w-0">
                    <p className="text-[10px] font-bold text-white truncate uppercase tracking-tighter">
                        {user?.displayName || user?.email?.split('@')[0] || "Sovereign User"}
                    </p>
                    <p className="text-[9px] text-zinc-600 font-mono">Verified Node</p>
                </div>
            </div>
            
            <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => signOut()}
                className="h-8 w-8 text-zinc-600 hover:text-red-500 hover:bg-red-500/10 rounded-lg"
                title="Sign Out"
            >
                <LogOut className="h-4 w-4" />
            </Button>
        </div>
      </div>
    </div>
  );
}

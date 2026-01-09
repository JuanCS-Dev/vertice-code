'use client';

import { useChat } from '@ai-sdk/react';
import { useState, useEffect } from 'react';
import { ChatSidebar } from './chat-sidebar';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { ArtifactsPanel } from '../artifacts/artifacts-panel';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PanelRightClose, Code } from 'lucide-react';
import { useAuth } from '@/context/auth-context';
import { useArtifactsStore } from '@/lib/stores/artifacts-store';

// FIX: Define a compatible interface for the hook result
interface ChatHookResult {
  messages: any[];
  append: (message: any) => Promise<void>;
  reload: () => Promise<void>;
  stop: () => void;
  isLoading: boolean;
  input?: string;
  setInput?: (value: string) => void;
  handleInputChange?: (e: any) => void;
  handleSubmit?: (e: any) => void;
}

export function ChatInterface() {
  const [inputValue, setInputValue] = useState('');
  const [isArtifactOpen, setIsArtifactOpen] = useState(false);
  const { user } = useAuth();
  const [headers, setHeaders] = useState<Record<string, string>>({});
  
  const { createArtifact, updateArtifact } = useArtifactsStore();

  // Fetch token and set headers
  useEffect(() => {
    async function getToken() {
        if (user) {
            const token = await user.getIdToken();
            setHeaders({
                'Authorization': `Bearer ${token}`
            });
        }
    }
    getToken();
  }, [user]);

  // Hook into AI SDK Chat
  const chat = useChat({
    initialMessages: [],
    headers: headers,
    onToolCall: ({ toolCall }: any) => {
        // Handle Generative UI Tool Calls
        if (toolCall?.toolName === 'create_artifact') {
            const { title, language, content } = toolCall.args;
            const artifactId = createArtifact(title || 'untitled.txt', 'file');
            if (content) {
                updateArtifact(artifactId, { content, language });
            }
            setIsArtifactOpen(true);
        }
        
        if (toolCall?.toolName === 'update_artifact') {
            const { id, content } = toolCall.args;
            updateArtifact(id, { content });
            setIsArtifactOpen(true);
        }
    }
  }) as unknown as ChatHookResult;

  const { messages, append, isLoading } = chat;

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;
    
    if (append) {
        append({
            role: 'user',
            content: inputValue,
        });
    }
    setInputValue('');
  };

  // Shortcut Cmd+B
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setIsArtifactOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      <div className="hidden md:flex w-64 border-r border-white/5 bg-card/50">
        <ChatSidebar />
      </div>

      <div className="flex-1 flex flex-row overflow-hidden relative">
        <div className={cn(
          "flex flex-col h-full transition-all duration-300 ease-in-out relative z-10",
          isArtifactOpen ? "w-[35%] min-w-[400px] border-r border-white/5 shadow-2xl" : "w-full mx-auto"
        )}>
            {!isArtifactOpen && (
                <div className="absolute top-4 right-4 z-50">
                    <Button 
                        variant="outline" 
                        size="icon"
                        onClick={() => setIsArtifactOpen(true)}
                        className="rounded-full shadow-lg border-primary/20 hover:border-primary hover:text-primary transition-colors bg-black/50 backdrop-blur"
                    >
                        <Code className="h-4 w-4" />
                    </Button>
                </div>
            )}

          <div className="flex-1 overflow-y-auto p-4 scrollbar-thin bg-background">
            <div className={cn("mx-auto h-full", isArtifactOpen ? "w-full" : "max-w-3xl")}>
                <ChatMessages messages={messages} isLoading={isLoading} />
            </div>
          </div>
          
          <div className="p-4 bg-background/80 backdrop-blur-md border-t border-white/5">
            <div className={cn("mx-auto", isArtifactOpen ? "w-full" : "max-w-3xl")}>
                <ChatInput 
                    value={inputValue}
                    onChange={handleInputChange}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                />
            </div>
          </div>
        </div>

        {isArtifactOpen && (
          <div className="flex-1 h-full bg-[#0d0d0d] relative flex flex-col animate-in slide-in-from-right-10 duration-300 shadow-[-20px_0_50px_rgba(0,0,0,0.5)]">
             <div className="h-12 border-b border-white/5 flex items-center justify-between px-4 bg-background/50">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-500">Manifestation Canvas</span>
                </div>
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => setIsArtifactOpen(false)}
                    className="h-8 w-8 text-zinc-600 hover:text-white"
                >
                    <PanelRightClose className="h-4 w-4" />
                </Button>
             </div>
             
             <div className="flex-1 overflow-hidden">
                <ArtifactsPanel />
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
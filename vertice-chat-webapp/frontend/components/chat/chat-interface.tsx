'use client';

import { useChat } from '@ai-sdk/react';
import { useRef, useEffect, useState } from 'react';
import { useOpenResponses } from '@/hooks/use-open-responses';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { ChatSidebar } from './chat-sidebar';
import { ArtifactsPanel } from '../artifacts/artifacts-panel';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { PanelRightClose, Code, Settings } from 'lucide-react';
import { useAuth } from '@/context/auth-context';
import { useArtifactsStore } from '@/lib/stores/artifacts-store';
import { ErrorBoundary } from '@/components/ui/error-boundary';

// Define explicit Message interface to fix type errors
interface ToolInvocation {
  toolCallId: string;
  toolName: string;
  args: any;
  state: 'call' | 'result';
}

interface Message {
  id: string;
  role: 'system' | 'user' | 'assistant' | 'data' | 'tool';
  content: string;
  toolInvocations?: ToolInvocation[];
  [key: string]: any;
}

export function ChatInterface() {
  console.log('[DEBUG] ChatInterface Render Cycle Start');

  const [inputValue, setInputValue] = useState('');
  const [isArtifactOpen, setIsArtifactOpen] = useState(false);
  const [protocol, setProtocol] = useState<'vercel' | 'open_responses'>('vercel');
  const { user } = useAuth();
  const [headers, setHeaders] = useState<Record<string, string>>({});

  // FIX: Use stable references to Zustand store functions to prevent infinite loops
  const storeRef = useRef(useArtifactsStore.getState());

  // FIX: Track processed tool invocations to prevent duplicate processing
  const processedToolCalls = useRef<Set<string>>(new Set());

  // Subscribe to store changes to keep refs updated
  useEffect(() => {
    const unsubscribe = useArtifactsStore.subscribe((state) => {
      storeRef.current = state;
    });
    return unsubscribe;
  }, []);

  // Fetch token and set headers - CRITICAL FIX: Depend on user.uid, not user object
  useEffect(() => {
    console.log('[DEBUG] Auth Effect Run. User UID:', user?.uid);
    async function getToken() {
      if (user?.uid) {
        try {
          const token = await user.getIdToken();
          setHeaders({
            'Authorization': `Bearer ${token}`
          });
        } catch (err) {
          console.error('[DEBUG] Failed to get ID token', err);
        }
      }
    }
    getToken();
  }, [user?.uid, user]);

   // Hook into AI SDK Chat with data stream protocol (Vercel)
   const vercelChat = useChat({
     // api: '/api/chat', // Default is /api/chat, commenting out to fix Type Error
     // headers, // Headers passed dynamically in handleSubmit
     // streamProtocol: 'data',
     id: 'sovereign-chat', // Explicit ID
     onError: (error) => {
       console.error('[DEBUG] Vercel useChat Error:', error);
     },
     onFinish: () => {
       console.log('[DEBUG] Vercel useChat Finish');
     }
   });

   // Hook into Open Responses protocol
   const openResponsesChat = useOpenResponses({
     apiUrl: '/api/chat',
     onError: (error) => {
       console.error('[DEBUG] Open Responses Error:', error);
     },
     onFinish: (usage) => {
       console.log('[DEBUG] Open Responses Finish:', usage);
     }
   });

   // Use the appropriate chat hook based on protocol
   const chat = protocol === 'vercel' ? vercelChat : openResponsesChat;
   const messages = protocol === 'vercel' ? vercelChat.messages : openResponsesChat.messages;
   const isLoading = protocol === 'vercel' ? vercelChat.isLoading : openResponsesChat.isLoading;
   const sendMessage = protocol === 'vercel' ? vercelChat.sendMessage || vercelChat.append : openResponsesChat.sendMessage;

   console.log('[DEBUG] Using protocol:', protocol);
   console.log('[DEBUG] Chat hook result keys:', Object.keys(chat || {}));

  // FIX: Reactive Tool Handling with proper guards against infinite loops
  useEffect(() => {
    // Guard against undefined/null messages
    if (!messages || !messages.length) return;

    const lastMessage = messages[messages.length - 1] as Message;

    // Check for tool invocations in the last message
    if (lastMessage.toolInvocations) {
      lastMessage.toolInvocations.forEach((toolInvocation) => {
        // FIX: Skip if already processed (prevents infinite loop)
        if (processedToolCalls.current.has(toolInvocation.toolCallId)) return;

        // FIX: Only process on 'result' state (not 'call') to ensure completion
        if (toolInvocation.toolName === 'create_artifact' && toolInvocation.state === 'result') {
          console.log('[DEBUG] Processing create_artifact', toolInvocation.toolCallId);
          processedToolCalls.current.add(toolInvocation.toolCallId);
          const { title, language, content } = toolInvocation.args;
          const artifactId = storeRef.current.createArtifact(title || 'untitled.txt', 'file');
          if (content) {
            storeRef.current.updateArtifact(artifactId, { content, language });
          }
          setIsArtifactOpen(true);
        }

        if (toolInvocation.toolName === 'update_artifact' && toolInvocation.state === 'result') {
          console.log('[DEBUG] Processing update_artifact', toolInvocation.toolCallId);
          processedToolCalls.current.add(toolInvocation.toolCallId);
          const { id, content } = toolInvocation.args;
          storeRef.current.updateArtifact(id, { content });
          setIsArtifactOpen(true);
        }
      });
    }
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;

    console.log('[DEBUG] Submitting with Headers:', headers); // LOG HEADERS

    // CRITICAL FIX: Fallback to sendMessage if append is missing
    const sendFunc = typeof append === 'function' ? append : sendMessage;

    if (typeof sendFunc !== 'function') {
      console.error('[CRITICAL] append is not a function!', { append, sendMessage });
      alert('System Error: Chat functionality unavailable (API Mismatch). Check console.');
      return;
    }

    try {
      // Add protocol to the request data
      const messageData = {
        role: 'user',
        content: inputValue,
        protocol: protocol, // Add protocol to request
      };

      if (protocol === 'vercel') {
        await sendFunc(messageData, { headers });
      } else {
        // For Open Responses, call sendMessage directly with content
        await sendMessage(inputValue);
      }
    } catch (err) {
      console.error('[CRITICAL] Send Failed', err);
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
        <ErrorBoundary name="ChatSidebar">
          <ChatSidebar />
        </ErrorBoundary>
      </div>

      <div className="flex-1 flex flex-row overflow-hidden relative">
        <div className={cn(
          "flex flex-col h-full transition-all duration-300 ease-in-out relative z-10",
          isArtifactOpen ? "w-[35%] min-w-[400px] border-r border-white/5 shadow-2xl" : "w-full mx-auto"
        )}>
           {!isArtifactOpen && (
             <div className="absolute top-4 right-4 z-50 flex gap-2">
               <Select value={protocol} onValueChange={(value: 'vercel' | 'open_responses') => setProtocol(value)}>
                 <SelectTrigger className="w-[140px] bg-black/50 backdrop-blur border-primary/20">
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   <SelectItem value="vercel">Vercel Protocol</SelectItem>
                   <SelectItem value="open_responses">Open Responses</SelectItem>
                 </SelectContent>
               </Select>
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
              <ErrorBoundary name="ChatMessages">
                <ChatMessages messages={messages} isLoading={isLoading} />
              </ErrorBoundary>
            </div>
          </div>

          <div className="p-4 bg-background/80 backdrop-blur-md border-t border-white/5">
            <div className={cn("mx-auto", isArtifactOpen ? "w-full" : "max-w-3xl")}>
              <ErrorBoundary name="ChatInput">
                <ChatInput
                  value={inputValue}
                  onChange={handleInputChange}
                  onSubmit={handleSubmit}
                  isLoading={isLoading}
                />
              </ErrorBoundary>
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
              <ErrorBoundary name="ArtifactsPanel">
                <ArtifactsPanel />
              </ErrorBoundary>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

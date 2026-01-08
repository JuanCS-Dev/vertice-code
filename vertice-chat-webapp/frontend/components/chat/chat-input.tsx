'use client';

import { useState, useRef, FormEvent, useEffect } from 'react';
import { useChatStore, useCurrentSession } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Square, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CommandPalette } from '@/components/commands/command-palette';
import { commandRegistry } from '@/lib/commands';
import { VoiceInput } from '@/components/voice/voice-input';

export function ChatInput() {
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showVoiceInput, setShowVoiceInput] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { addMessage, setLoading, setError } = useChatStore();
  const session = useCurrentSession();

  // Initialize commands on mount
  useEffect(() => {
    // Import and initialize commands
    import('@/lib/commands').then(({ initializeCommands }) => {
      initializeCommands();
    });
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!message.trim() || !session || isSubmitting) return;

    const userMessage = message.trim();
    setMessage('');
    setIsSubmitting(true);
    setLoading(true);
    setError(null);
    setShowCommandPalette(false);

    try {
      // Add user message to chat
      addMessage(session.id, {
        role: 'user',
        content: userMessage,
      });

      // Check if it's a slash command
      if (userMessage.startsWith('/')) {
        const result = await commandRegistry.execute(userMessage, {
          sessionId: session.id,
          userId: 'user-123', // TEMPORARY: Replace with actual Clerk user ID in Phase 6 when auth backend is deployed
        });

        // Handle command result
        if (result.type === 'error') {
          setError(result.content);
          setLoading(false);
        } else {
          // Add command result as assistant message
          addMessage(session.id, {
            role: 'assistant',
            content: result.content,
            metadata: {
              ...result.metadata,
            },
          });
          setLoading(false);
        }
      } else {
        // Regular chat message - backend integration will be implemented in Phase 6
        // For now, simulate a response
        setTimeout(() => {
          addMessage(session.id, {
            role: 'assistant',
            content: `Obrigado pela sua mensagem: "${userMessage}". Esta é uma resposta simulada. Em breve integraremos com a API real.`,
            metadata: {
              model: session.model,
              tokens: 150,
              cost: 0.0012,
              executionTime: 0.8,
            },
          });
          setLoading(false);
        }, 1000);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setError('Erro ao enviar mensagem. Tente novamente.');
      setLoading(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setMessage(value);
    adjustTextareaHeight();

    // Show command palette for slash commands
    setShowCommandPalette(value.startsWith('/'));
  };

  const handleCommandExecute = (command: string) => {
    setMessage(command);
    setShowCommandPalette(false);
    // Focus back to textarea
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleVoiceTranscription = (text: string) => {
    setMessage(prev => prev + (prev ? ' ' : '') + text);
    setShowVoiceInput(false);
    // Focus back to textarea
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleVoiceError = (error: string) => {
    // Show error in chat or as toast
    console.error('Voice input error:', error);
    setShowVoiceInput(false);
  };

  return (
    <div className="relative space-y-4">
      {/* Voice Input */}
      {showVoiceInput && (
        <VoiceInput
          onTranscription={handleVoiceTranscription}
          onError={handleVoiceError}
          className="mb-2"
        />
      )}

      <form onSubmit={handleSubmit} className="flex gap-3 items-end bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-2 transition-all duration-300 focus-within:border-cyan-500/50 focus-within:shadow-[0_0_20px_rgba(6,182,212,0.1)]">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Execute sovereign commands or brainstorm with Opus 4.5... (/ for tools)"
            className="min-h-[44px] max-h-[300px] bg-transparent border-none focus-visible:ring-0 resize-none py-3 px-4 text-zinc-200 placeholder:text-zinc-600"
            disabled={isSubmitting}
          />

          {message.length > 0 && (
            <div className="absolute bottom-2 right-2 text-[10px] font-mono text-zinc-700 tracking-tighter">
              {message.length} CHARS
            </div>
          )}
        </div>

        <div className="flex gap-2 pb-1.5 pr-1.5">
          {/* Voice Input Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setShowVoiceInput(!showVoiceInput)}
            disabled={isSubmitting}
            className={cn(
              "h-9 w-9 rounded-xl hover:bg-white/5 transition-colors",
              showVoiceInput && "text-red-500 bg-red-500/10"
            )}
          >
            <Mic className="h-4 w-4" />
          </Button>

          <Button
            type="submit"
            variant="neon"
            size="icon"
            disabled={!message.trim() || isSubmitting || !session}
            className={cn(
              "h-9 w-9 rounded-xl transition-all duration-300",
              isSubmitting && "animate-pulse scale-95"
            )}
          >
            {isSubmitting ? (
              <Square className="h-4 w-4 fill-current" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onExecute={handleCommandExecute}
        inputValue={message}
        onInputChange={setMessage}
      />
    </div>
  );
}
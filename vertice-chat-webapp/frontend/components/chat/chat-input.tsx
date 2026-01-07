'use client';

import { useState, useRef, FormEvent } from 'react';
import { useChatStore, useCurrentSession } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Square } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ChatInput() {
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { addMessage, setLoading, setError } = useChatStore();
  const session = useCurrentSession();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!message.trim() || !session || isSubmitting) return;

    const userMessage = message.trim();
    setMessage('');
    setIsSubmitting(true);
    setLoading(true);
    setError(null);

    try {
      // Add user message to chat
      addMessage(session.id, {
        role: 'user',
        content: userMessage,
      });

      // TODO: Send to backend API and get response
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
    setMessage(e.target.value);
    adjustTextareaHeight();
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="flex-1 relative">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua mensagem... (Shift+Enter para nova linha)"
          className="min-h-[44px] max-h-[200px] resize-none pr-12"
          disabled={isSubmitting}
        />

        {message.length > 0 && (
          <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
            {message.length}
          </div>
        )}
      </div>

      <Button
        type="submit"
        size="icon"
        disabled={!message.trim() || isSubmitting || !session}
        className={cn(
          "flex-shrink-0",
          isSubmitting && "animate-pulse"
        )}
      >
        {isSubmitting ? (
          <Square className="h-4 w-4" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  );
}
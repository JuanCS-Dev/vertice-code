'use client';

import { useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Square, Mic, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => void;
  onSubmit: (e?: React.FormEvent) => void;
  isLoading: boolean;
}

export function ChatInput({ value, onChange, onSubmit, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={onSubmit} className="relative flex items-end gap-2 bg-[#0a0a0a] border border-[#333] rounded-xl p-2 shadow-2xl transition-all duration-300 focus-within:border-primary/50 focus-within:shadow-[0_0_20px_rgba(212,255,0,0.1)]">
        
        {/* Attachment Button */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-10 w-10 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 mb-[1px]"
        >
          <Paperclip className="h-5 w-5" />
        </Button>

        <Textarea
          ref={textareaRef}
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          className="flex-1 min-h-[44px] max-h-[200px] bg-transparent border-none focus-visible:ring-0 resize-none py-3 px-2 text-foreground placeholder:text-muted-foreground/50 text-base"
          disabled={isLoading}
          rows={1}
        />

        {/* Right Actions */}
        <div className="flex gap-1 pb-[1px]">
            {/* Voice Button */}
            <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5"
            >
                <Mic className="h-5 w-5" />
            </Button>

            {/* Send/Stop Button */}
            <Button
                type="submit"
                size="icon"
                disabled={!value.trim() && !isLoading}
                className={cn(
                "h-10 w-10 rounded-lg transition-all duration-200",
                isLoading 
                    ? "bg-red-500/10 text-red-500 hover:bg-red-500/20" 
                    : "bg-primary text-black hover:bg-primary/90"
                )}
            >
                {isLoading ? (
                <Square className="h-4 w-4 fill-current" />
                ) : (
                <Send className="h-5 w-5 ml-0.5" />
                )}
            </Button>
        </div>
      </form>
      
      <div className="text-center mt-2 text-[10px] text-muted-foreground/40 font-mono">
        Vertice Sovereign AI • Phase 3.0
      </div>
    </div>
  );
}

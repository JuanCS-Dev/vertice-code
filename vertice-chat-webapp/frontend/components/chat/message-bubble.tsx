'use client';

import { memo } from 'react';
import { Message } from '@/lib/stores/chat-store';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Copy, User, Bot, Clock, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { MarkdownRenderer } from './markdown-renderer';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { motion } from 'framer-motion';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = memo(function MessageBubble({
  message
}: MessageBubbleProps) {
  const { toast } = useToast();

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      toast({
        title: "Copiado com Sucesso",
        description: "Conteúdo transferido para a área de transferência.",
        className: "border-primary/20 bg-background/80 backdrop-blur-xl"
      });
    } catch (err) {
      toast({
        title: "Erro na Cópia",
        description: "Não foi possível acessar a área de transferência.",
        variant: "destructive",
      });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      className={cn(
        "flex gap-4 group relative py-2",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* Avatar - System/Bot */}
      {!isUser && (
        <Avatar className="h-9 w-9 flex-shrink-0 border border-white/10 shadow-[0_0_15px_-3px_rgba(6,182,212,0.15)] ring-1 ring-white/5">
          <AvatarFallback className="bg-card text-primary font-bold">
            {isSystem ? 'S' : <Bot className="h-5 w-5" />}
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message Content Area */}
      <div className={cn(
        "max-w-[85%] space-y-1.5",
        isUser ? "order-first" : "order-last"
      )}>
        {/* Metadata Header */}
        <div className={cn(
          "flex items-center gap-2 text-[10px] uppercase tracking-widest font-medium text-muted-foreground/60 px-1",
          isUser ? "justify-end" : "justify-start"
        )}>
          {isSystem && <span className="text-primary font-bold">System Override</span>}
          {message.metadata?.model && (
            <span className="flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-primary/50"></span>
              {message.metadata.model.split('-')[0]}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-2.5 w-2.5" />
            {(() => {
              const date = message.timestamp instanceof Date ? message.timestamp : new Date(message.timestamp);
              const isValid = !isNaN(date.getTime());
              return isValid ? formatDistanceToNow(date, {
                addSuffix: true,
                locale: ptBR
              }) : 'agora';
            })()}
          </span>
        </div>

        {/* The Bubble Artifact */}
        <div className={cn(
          "relative rounded-2xl px-6 py-5 shadow-sm transition-all duration-500 overflow-hidden",
          isUser
            ? "bg-[#0891b2] text-white ml-auto shadow-[0_4px_20px_-5px_rgba(8,145,178,0.4)] border border-white/20"
            : "bg-card border border-white/5 backdrop-blur-xl group-hover:border-primary/20 group-hover:shadow-[0_0_30px_-10px_rgba(6,182,212,0.05)]"
        )}>
          {/* Subtle Shine Effect for User Bubble */}
          {isUser && (
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
          )}

          <div className={cn(
            "prose prose-sm max-w-none dark:prose-invert",
            "prose-p:leading-relaxed prose-pre:my-4",
            isUser ? "prose-p:text-white/95" : "prose-p:text-zinc-300"
          )}>
            {isUser ? (
              <div className="whitespace-pre-wrap font-sans text-[15px]">{message.content}</div>
            ) : (
              <MarkdownRenderer content={message.content} />
            )}
          </div>
        </div>

        {/* Footer Metrics & Actions */}
        <div className={cn(
          "flex items-center gap-3 text-[10px] font-mono font-medium text-muted-foreground/40 h-6 px-1 transition-opacity duration-300",
          isUser ? "justify-end opacity-0 group-hover:opacity-100" : "justify-between"
        )}>
          <div className="flex items-center gap-3">
            {!isUser && message.metadata?.executionTime && (
              <span className="flex items-center gap-1 text-primary/60">
                <Zap className="h-3 w-3" />
                {(message.metadata.executionTime * 1000).toFixed(0)}ms
              </span>
            )}
            {!isUser && message.metadata?.tokens && (
              <span className="border-l border-white/5 pl-3">
                {message.metadata.tokens.toLocaleString()} tks
              </span>
            )}
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-full hover:bg-white/5 hover:text-primary transition-colors opacity-0 group-hover:opacity-100"
            onClick={copyToClipboard}
            title="Copiar conteúdo"
          >
            <Copy className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Avatar - User */}
      {isUser && (
        <Avatar className="h-9 w-9 flex-shrink-0 border border-white/10 shadow-lg">
          <AvatarFallback className="bg-secondary/50 text-secondary-foreground backdrop-blur-md">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
});
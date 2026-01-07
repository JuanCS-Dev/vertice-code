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
        title: "Copiado!",
        description: "Mensagem copiada para a área de transferência.",
      });
    } catch (err) {
      toast({
        title: "Erro",
        description: "Não foi possível copiar a mensagem.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className={cn(
      "flex gap-3 group",
      isUser ? "justify-end" : "justify-start"
    )}>
      {/* Avatar */}
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            {isSystem ? 'S' : <Bot className="h-4 w-4" />}
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message Content */}
      <div className={cn(
        "max-w-[80%] space-y-2",
        isUser ? "order-first" : "order-last"
      )}>
        {/* Message Header */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {isSystem && <Badge variant="secondary" className="text-xs">Sistema</Badge>}
          {message.metadata?.model && (
            <Badge variant="outline" className="text-xs">
              {message.metadata.model.split('-')[0].toUpperCase()}
            </Badge>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDistanceToNow(message.timestamp, {
              addSuffix: true,
              locale: ptBR
            })}
          </span>
        </div>

        {/* Message Bubble */}
        <div className={cn(
          "rounded-lg px-4 py-3 shadow-sm",
          isUser
            ? "bg-primary text-primary-foreground ml-auto"
            : isSystem
              ? "bg-muted border border-border"
              : "bg-card border border-border"
        )}>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {isUser ? (
              <div className="whitespace-pre-wrap">{message.content}</div>
            ) : (
              <MarkdownRenderer content={message.content} />
            )}
          </div>
        </div>

        {/* Message Footer */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            {message.metadata?.executionTime && (
              <span className="flex items-center gap-1">
                <Zap className="h-3 w-3" />
                {(message.metadata.executionTime * 1000).toFixed(0)}ms
              </span>
            )}
            {message.metadata?.tokens && (
              <span>
                {message.metadata.tokens.toLocaleString()} tokens
              </span>
            )}
            {message.metadata?.cost && (
              <span>
                ${message.metadata.cost.toFixed(4)}
              </span>
            )}
          </div>

          {/* Copy Button */}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={copyToClipboard}
            title="Copiar mensagem"
          >
            <Copy className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
});
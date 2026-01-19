'use client';

import { useChat } from 'ai/react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, User, Bot } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export default function ChatPage() {
  const [input, setInput] = useState('');

  const { messages, handleSubmit, isLoading, error } = useChat({
    // Use custom fetch to point to our FastAPI endpoint
    fetch: async (url, options) => {
      // Override the URL to point to our FastAPI backend
      const fastApiUrl = url.replace('/api/chat', 'http://localhost:8000/api/v1/chat');
      return fetch(fastApiUrl, options);
    },
    streamProtocol: 'text', // Start with text protocol for compatibility
    onToolCall: async (toolCall) => {
      console.log('Tool called:', toolCall);
      // Handle tool calls here if needed
    },
    onError: (error) => {
      console.error('Chat error:', error);
    },
  });

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    handleSubmit(e, {
      data: {
        messages: [...messages, { role: 'user', content: input }],
      },
    });
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Vertice-Code AI IDE</h1>
            <Badge variant="outline" className="text-xs">
              2026 Preview
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={isLoading ? "destructive" : "default"}>
              {isLoading ? "Processing..." : "Ready"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <Card key={message.id} className={`max-w-2xl ${
              message.role === 'user'
                ? 'ml-auto bg-primary text-primary-foreground'
                : 'mr-auto bg-muted'
            }`}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2 text-sm">
                  {message.role === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                  <span>{message.role === 'user' ? 'You' : 'Vertice-Code'}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="whitespace-pre-wrap text-sm">
                  {message.content}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <Card className="max-w-2xl mr-auto bg-muted animate-pulse">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">
                    Vertice-Code is thinking...
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error display */}
          {error && (
            <Card className="max-w-2xl mr-auto bg-destructive/10 border-destructive">
              <CardContent className="p-4">
                <div className="text-sm text-destructive">
                  Error: {error.message}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t bg-card p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleFormSubmit} className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Vertice-Code anything... (Generative UI & Artifacts coming in Phase 2)"
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          <div className="mt-2 text-xs text-muted-foreground">
            Phase 1: AI SDK Protocol | Phase 2: Generative UI & Artifacts | Phase 3: GitHub Deep Sync
          </div>
        </div>
      </div>
    </div>
  );
}

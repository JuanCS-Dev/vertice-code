'use client';

import { useEffect } from 'react';
import { useChatStore } from '@/lib/stores/chat-store';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { ChatMessages } from '@/components/chat/chat-messages';
import { ChatInput } from '@/components/chat/chat-input';
import { ChatSettings } from '@/components/chat/chat-settings';
import { Button } from '@/components/ui/button';
import { Settings, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ChatPage() {
  const { currentSessionId, createSession } = useChatStore();

  // Create initial session if none exists
  useEffect(() => {
    if (!currentSessionId) {
      createSession();
    }
  }, [currentSessionId, createSession]);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <ChatSidebar />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            <h1 className="text-lg font-semibold">Vertice Chat</h1>
          </div>

          <div className="flex items-center gap-2">
            <ChatSettings />
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-hidden">
          <ChatMessages />
        </div>

        {/* Input Area */}
        <div className="border-t border-border p-4">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}
'use client';

import { useEffect, useState } from 'react';
import { useChatStore } from '@/lib/stores/chat-store';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { ChatMessages } from '@/components/chat/chat-messages';
import { ChatInput } from '@/components/chat/chat-input';
import { ChatSettings } from '@/components/chat/chat-settings';
import { ArtifactsPanel } from '@/components/artifacts/artifacts-panel';
import { Button } from '@/components/ui/button';
import { Settings, MessageSquare, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

type ViewMode = 'chat' | 'artifacts';

export default function ChatPage() {
  const { currentSessionId, createSession } = useChatStore();
  const [viewMode, setViewMode] = useState<ViewMode>('chat');

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

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            {viewMode === 'chat' ? (
              <MessageSquare className="h-5 w-5" />
            ) : (
              <FileText className="h-5 w-5" />
            )}
            <h1 className="text-lg font-semibold">
              {viewMode === 'chat' ? 'Vertice Chat' : 'Artifacts'}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex rounded-md border">
              <Button
                variant={viewMode === 'chat' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('chat')}
                className="rounded-r-none"
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Chat
              </Button>
              <Button
                variant={viewMode === 'artifacts' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('artifacts')}
                className="rounded-l-none border-l"
              >
                <FileText className="h-4 w-4 mr-2" />
                Artifacts
              </Button>
            </div>

            {viewMode === 'chat' && <ChatSettings />}
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {viewMode === 'chat' ? (
            <>
              {/* Chat Messages */}
              <div className="flex-1 overflow-hidden">
                <ChatMessages />
              </div>

              {/* Chat Input */}
              <div className="border-t border-border p-4">
                <ChatInput />
              </div>
            </>
          ) : (
            /* Artifacts Panel */
            <div className="h-full p-4">
              <ArtifactsPanel />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
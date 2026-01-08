/**
 * Chat Page with Partial Prerendering
 *
 * PPR allows mixing static and dynamic content in the same page:
 * - Static: Layout, navigation, sidebar (prerendered at build time)
 * - Dynamic: Chat messages, user state (streamed at runtime)
 *
 * Reference: https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
 */
'use client';

import { Suspense, useEffect, useState } from 'react';
import { useChatStore } from '@/lib/stores/chat-store';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { ChatMessages } from '@/components/chat/chat-messages';
import { ChatInput } from '@/components/chat/chat-input';
import { ChatSettings } from '@/components/chat/chat-settings';
import { ArtifactsPanel } from '@/components/artifacts/artifacts-panel';
import { RepoBrowser } from '@/components/github/repo-browser';
import { Button } from '@/components/ui/button';
import { Settings, MessageSquare, FileText, Github, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';

// Enable Partial Prerendering for optimal performance
// Static parts (sidebar, header) render at build time
// Dynamic parts (messages, input) stream at runtime
// export const experimental_ppr = true; // Disabled due to cacheComponents conflict

type ViewMode = 'chat' | 'artifacts' | 'github' | 'voice';

/**
 * Chat Skeleton Loading State
 *
 * Shows while dynamic chat content loads with PPR
 * Provides smooth loading experience
 */
function ChatSkeleton() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Messages Skeleton */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full p-4 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
              <div className="bg-muted rounded-lg h-16 w-3/4 animate-pulse" />
            </div>
          ))}
        </div>
      </div>

      {/* Input Skeleton */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <div className="flex-1 bg-muted rounded-lg h-12 animate-pulse" />
          <div className="w-12 bg-muted rounded-lg animate-pulse" />
        </div>
      </div>
    </div>
  );
}

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
      {/* Sidebar - Static, prerendered */}
      <ChatSidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header - Static, prerendered */}
        <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center gap-2">
              {viewMode === 'chat' ? (
                <MessageSquare className="h-5 w-5" />
              ) : viewMode === 'artifacts' ? (
                <FileText className="h-5 w-5" />
              ) : viewMode === 'github' ? (
                <Github className="h-5 w-5" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
              <h1 className="text-lg font-semibold">
                {viewMode === 'chat' ? 'Vertice Chat' :
                 viewMode === 'artifacts' ? 'Artifacts' :
                 viewMode === 'github' ? 'GitHub Explorer' : 'Voice Chat'}
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
                className="rounded-none border-l border-r"
              >
                <FileText className="h-4 w-4 mr-2" />
                Artifacts
              </Button>
              <Button
                variant={viewMode === 'github' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('github')}
                className="rounded-l-none"
              >
                <Github className="h-4 w-4 mr-2" />
                GitHub
              </Button>
            </div>

            {viewMode === 'chat' && <ChatSettings />}
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Content Area - Dynamic, streamed */}
        <div className="flex-1 overflow-hidden">
          {viewMode === 'chat' ? (
            <Suspense fallback={<ChatSkeleton />}>
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
            </Suspense>
          ) : viewMode === 'artifacts' ? (
            /* Artifacts Panel - Also benefits from PPR */
            <div className="h-full p-4">
              <ArtifactsPanel />
            </div>
          ) : (
            /* GitHub Browser - Dynamic content */
            <Suspense fallback={<div className="h-full flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
              <div className="h-full">
                <RepoBrowser />
              </div>
            </Suspense>
          )}
        </div>
      </div>
    </div>
  );
}
"use client";

import React from "react";
import { User, Sparkles, FileCode, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";

export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatMessageProps {
  message: Message;
  isLast?: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "group w-full py-6 px-4 md:px-8 border-b border-transparent hover:bg-white/[0.02] transition-colors animate-fade-in",
        isLast && "pb-12" // Extra padding for the last message
      )}
    >
      <div className="max-w-3xl mx-auto flex gap-4 md:gap-6">
        {/* Avatar Column */}
        <div className="shrink-0 flex flex-col items-center gap-2">
          <div
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center shadow-sm",
              isUser
                ? "bg-muted text-foreground"
                : "bg-accent/10 text-accent shadow-[0_0_10px_-3px_var(--accent)]"
            )}
          >
            {isUser ? (
              <User className="w-5 h-5" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
          </div>

          {/* Connecting Line (Optional aesthetics) */}
          {/* <div className="w-px h-full bg-border/50 my-2 group-last:hidden" /> */}
        </div>

        {/* Content Column */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header (Name & Time) */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-foreground">
              {isUser ? "You" : "Vertice AI"}
            </span>
            <span className="text-xs text-muted-foreground/50">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          {/* The Message Body */}
          <div className="text-sm md:text-base leading-relaxed">
            <MarkdownRenderer content={message.content} />

            {/* Streaming Cursor */}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 align-middle bg-accent animate-pulse" />
            )}
          </div>

          {/* Action Bar (Visible on Hover for Assistant) */}
          {!isUser && !message.isStreaming && (
            <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
               <button className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded transition-colors" title="Regenerate">
                 <RefreshCw className="w-3.5 h-3.5" />
               </button>
               {/* Add more actions like Copy, Fork, etc. here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Sub-component: Artifact Chip (Usage example within chat)
export function ArtifactChip({ title, language }: { title: string; language: string }) {
  return (
    <div className="inline-flex items-center gap-3 px-3 py-2 bg-card border border-border rounded-lg cursor-pointer hover:border-accent/50 hover:bg-accent/5 transition-all group my-2">
      <div className="p-1.5 bg-muted rounded">
        <FileCode className="w-4 h-4 text-muted-foreground group-hover:text-accent" />
      </div>
      <div className="flex flex-col">
        <span className="text-xs font-medium text-foreground group-hover:text-accent transition-colors">{title}</span>
        <span className="text-[10px] text-muted-foreground uppercase">{language}</span>
      </div>
    </div>
  );
}

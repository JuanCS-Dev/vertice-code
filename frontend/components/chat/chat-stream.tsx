"use client";

import React, { useRef, useEffect } from "react";
import { ChatMessage } from "./chat-message";
import { useChatStore } from "@/lib/stores/chat-store";
import { AlertCircle } from "lucide-react";

export function ChatStream() {
  const { messages, error } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, messages[messages.length - 1]?.content]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
        <div className="w-16 h-16 rounded-2xl bg-accent/5 border border-accent/10 flex items-center justify-center mb-6">
          <span className="text-3xl">✨</span>
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">Vertice AI Active</h3>
        <p className="max-w-md text-sm leading-relaxed">
          I am ready to help you architect, code, and deploy. <br/>
          Ask me to create a component or explain a concept.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-0 w-full pb-4">
      <div className="flex-1 w-full">
        {messages.map((msg, index) => (
          <ChatMessage 
            key={msg.id} 
            message={msg} 
            isLast={index === messages.length - 1} 
          />
        ))}
        
        {error && (
          <div className="mx-auto max-w-2xl mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-center gap-3 text-destructive">
             <AlertCircle className="w-5 h-5" />
             <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {/* Anchor for auto-scroll */}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
}

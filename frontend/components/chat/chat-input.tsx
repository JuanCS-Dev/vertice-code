"use client";

import React, { useRef, useState } from "react";
import { SendHorizontal, Paperclip, Mic } from "lucide-react";
import { useChatStore } from "@/lib/stores/chat-store";
import { cn } from "@/lib/utils";

export function ChatInput() {
  const { sendMessage, isLoading } = useChatStore();
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const content = input;
    setInput("");

    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    await sendMessage(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Auto-resize
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2">
      <div className="relative flex items-end gap-2 bg-muted/50 border border-input rounded-xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring focus-within:border-accent/50 transition-all">

        {/* Attachment Button */}
        <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-lg transition-colors pb-3">
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask Vertice to generate code..."
          className="flex-1 bg-transparent border-none focus:ring-0 resize-none max-h-[200px] min-h-[44px] py-3 px-2 text-sm md:text-base scrollbar-thin placeholder:text-muted-foreground/50"
          rows={1}
        />

        {/* Action Buttons */}
        <div className="flex items-center gap-1 pb-1">
           {input.trim().length === 0 ? (
             <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-lg transition-colors">
               <Mic className="w-5 h-5" />
             </button>
           ) : (
             <button
               onClick={handleSend}
               disabled={isLoading}
               className={cn(
                 "p-2 rounded-lg transition-all duration-200",
                 isLoading
                   ? "bg-muted text-muted-foreground cursor-not-allowed"
                   : "bg-accent text-accent-foreground hover:bg-accent/90 shadow-sm"
               )}
             >
               <SendHorizontal className="w-5 h-5" />
             </button>
           )}
        </div>
      </div>

      {/* Footer / Hint */}
      <div className="text-center mt-2">
        <p className="text-[10px] text-muted-foreground/50">
          Vertice AI can make mistakes. Review generated code.
        </p>
      </div>
    </div>
  );
}

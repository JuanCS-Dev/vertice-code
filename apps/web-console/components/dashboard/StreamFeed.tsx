"use client";

import { useEffect, useRef } from "react";
import { StreamState, ToolCall } from "../../lib/hooks/useAguiStream";
import { AgentMessageCard } from "../cards/AgentMessageCard";
import { ToolCallCard } from "../cards/ToolCallCard";

interface StreamFeedProps {
    state: StreamState;
    onToolSelect: (tool: ToolCall) => void;
}

export function StreamFeed({ state, onToolSelect }: StreamFeedProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    const msgsLen = state.messages.length;
    const toolsLen = state.tools.length;
    const lastMsgLen = state.messages[msgsLen - 1]?.text?.length || 0;

    // Auto-scroll
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [msgsLen, toolsLen, state.status, lastMsgLen]);

    // Combine items by timestamp/order is tricky if separate arrays.
    // For M2, we will render "tools relevant to the current moment" or just interleaved?
    // Since `useAguiStream` puts them in separate arrays, we need a strategy.
    // The backend usually streams: Thought (delta) -> Tool Call -> Tool Result -> Text (delta).

    // Strategy: Interleave isn't supported by separate arrays easily.
    // Revised approach: `useAguiStream` should probably have returned a single `FeedItem[]` list.
    // But to stick to the plan: I will verify how `handlePayload` updates.
    // It updates `messages` and `tools`. Ideally, we iterate "events" or we assume simple alternation.
    // For now: Render Messages, and if a tool is running/completed "after" the last message, show it?

    // Actually, let's render them in a unified list by approximating order, or just render TOOLS then MESSAGES? No.
    // Let's render: List of Tools (active/recent) ?
    // Wait, Agentic flow is usually:
    // 1. User: prompt
    // 2. Agent: Thought...
    // 3. Agent: Call Tool
    // 4. System: Tool Result
    // 5. Agent: Final Answer

    // Since I separated them in `useAguiStream`, I made Interleaving hard.
    // FIX: I will render them in two separate blocks? No, that looks bad.
    // I will just map them all and sort by something? `ToolCall` doesn't have a timestamp.

    // Let's just render them: Messages first, then Tools? No.
    // Let's check `AgentMessage`. It has timestamp.
    // I'll add `timestamp` to `ToolCall` in a quick fix to `useAguiStream`?
    // Or simpler: Just render `messages` and `tools` in a "latest active" style?

    // Real Solution: Render all messages.
    // AND below the *last* message, render any Tools that are running or recently finished?
    // This is a "ChatBubble + ToolWidgets" style.

    return (
        <div className="flex flex-col gap-4 p-4 pb-20">
            {state.messages.map((msg) => (
                <AgentMessageCard key={msg.id} message={msg} />
            ))}

            {/* Tools that are not "attached" to a message yet.
          Actually, let's just show all tools at the bottom for now as a "Workspace" or "Activity Log"?
          Or maybe inside the feed?
      */}
            {state.tools.length > 0 && (
                <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-border-dim/30">
                    <h4 className="text-xs uppercase text-gray-500 font-bold tracking-wider mb-2">Technical Execution</h4>
                    {state.tools.map(tool => (
                        <ToolCallCard key={tool.id} tool={tool} onSelect={onToolSelect} />
                    ))}
                </div>
            )}

            {state.status === "streaming" && state.messages.length === 0 && state.tools.length === 0 && (
                <div className="p-4 text-center text-gray-500 animate-pulse">
                    Initializing neural link...
                </div>
            )}

            {state.error && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono">
                    SYSTEM_FAULT: {state.error}
                </div>
            )}

            <div ref={bottomRef} />
        </div>
    );
}

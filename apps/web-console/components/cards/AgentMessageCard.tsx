"use client";

import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import { AgentMessage } from "../../lib/hooks/useAguiStream";

export function AgentMessageCard({ message }: { message: AgentMessage }) {
    const isAgent = message.role === "agent";

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-4 p-4 rounded-xl border ${isAgent
                    ? "bg-panel border-border-dim"
                    : "bg-panel-light/30 border-transparent"
                }`}
        >
            <div className={`size-8 rounded-full flex items-center justify-center shrink-0 ${isAgent ? "bg-primary/10 text-primary" : "bg-gray-700 text-gray-400"}`}>
                {isAgent ? <Bot size={18} /> : <User size={18} />}
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-white capitalize">{message.role}</span>
                    <span className="text-xs text-gray-500 font-mono">
                        {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                </div>
                <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-mono">
                    {message.text}
                    {!message.isFinal && <span className="inline-block w-2 h-4 bg-primary/50 ml-1 animate-pulse align-middle" />}
                </div>
            </div>
        </motion.div>
    );
}

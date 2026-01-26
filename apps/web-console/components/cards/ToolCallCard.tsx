"use client";

import { motion } from "framer-motion";
import { Terminal, CheckCircle2, Loader2, AlertCircle, FileCode } from "lucide-react";
import { ToolCall } from "../../lib/hooks/useAguiStream";

export function ToolCallCard({ tool, onSelect }: { tool: ToolCall; onSelect?: (tool: ToolCall) => void }) {
    const isRunning = tool.status === "running";
    const isError = tool.status === "error";


    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className={`group relative overflow-hidden rounded-xl border p-3 cursor-pointer transition-all hover:bg-white/5 ${isRunning
                ? "bg-primary/5 border-primary/30"
                : isError
                    ? "bg-red-500/5 border-red-500/30"
                    : "bg-panel border-border-dim"
                }`}
            onClick={() => onSelect?.(tool)}
        >
            <div className="flex items-start gap-3">
                <div className={`mt-0.5 size-6 rounded flex items-center justify-center shrink-0 ${isRunning ? "text-primary" : isError ? "text-red-400" : "text-gray-400"
                    }`}>
                    {isRunning ? <Loader2 size={16} className="animate-spin" /> :
                        isError ? <AlertCircle size={16} /> :
                            <Terminal size={16} />}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-white font-mono flex items-center gap-2">
                            {tool.name}
                            {tool.code && <FileCode size={12} className="text-gray-500" />}
                        </h4>
                        <span className={`text-[10px] uppercase tracking-wider font-bold ${isRunning ? "text-primary animate-pulse" : isError ? "text-red-400" : "text-gray-500"
                            }`}>
                            {tool.status}
                        </span>
                    </div>

                    {Object.keys(tool.args).length > 0 && (
                        <div className="mt-2 text-xs font-mono text-gray-400 bg-black/20 rounded p-2 overflow-x-auto">
                            <span className="text-gray-500 select-none mr-2">$</span>
                            {JSON.stringify(tool.args)}
                        </div>
                    )}

                    {tool.result !== undefined && tool.result !== null && (
                        <div className="mt-2 pt-2 border-t border-white/5 flex items-center gap-2 text-xs text-green-400/80 font-mono">
                            <CheckCircle2 size={12} />
                            <span className="truncate max-w-[300px]">
                                {typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result)}
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Active Indicator */}
            {isRunning && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary/20 overflow-hidden">
                    <div className="h-full bg-primary/50 w-1/3 animate-[shimmer_1s_infinite_linear]" />
                </div>
            )}
        </motion.div>
    );
}

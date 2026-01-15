'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
    children: ReactNode;
    name?: string;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`[ErrorBoundary:${this.props.name || 'Unknown'}] caught error:`, error, errorInfo);
        this.props.onError?.(error, errorInfo);
    }

    private handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex flex-col items-center justify-center h-full min-h-[200px] p-6 bg-red-500/5 border border-red-500/20 rounded-xl m-2">
                    <div className="bg-red-500/10 p-3 rounded-full mb-4">
                        <AlertTriangle className="h-6 w-6 text-red-500" />
                    </div>
                    <h3 className="text-lg font-bold text-red-500 mb-2">Component Malfunction</h3>
                    <p className="text-xs text-zinc-400 mb-4 font-mono text-center max-w-sm">
                        Error in module: <span className="text-white font-bold">{this.props.name}</span>
                    </p>
                    <div className="bg-black/50 p-3 rounded text-[10px] w-full max-h-32 overflow-auto font-mono text-left mb-4 border border-white/5">
                        {this.state.error?.message || "Unknown error"}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={this.handleRetry}
                        className="gap-2 border-red-500/20 hover:bg-red-500/10 hover:text-red-500"
                    >
                        <RefreshCw className="h-3 w-3" />
                        Attempt Recovery
                    </Button>
                </div>
            );
        }

        return this.props.children;
    }
}

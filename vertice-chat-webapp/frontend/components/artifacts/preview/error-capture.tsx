'use client';

/**
 * Error Capture & Telemetry
 *
 * PROJECT VIVID - Phase 2.2: Error Telemetry
 *
 * Features:
 * - Capture runtime errors from Sandpack
 * - Feed errors back to Chat Context for AI auto-fix
 * - Visual error overlays with stack traces
 * - Error telemetry and analytics
 *
 * Integration: Connects to Chat API for auto-fix suggestions
 */

import { useState, useEffect, useCallback } from 'react';
import { AlertCircle, X, Bug, Copy, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface RuntimeError {
  id: string;
  message: string;
  stack?: string;
  line?: number;
  column?: number;
  file?: string;
  timestamp: Date;
  type: 'runtime' | 'syntax' | 'type' | 'network';
  severity: 'error' | 'warning';
}

export interface ErrorCaptureProps {
  errors: RuntimeError[];
  onDismiss: (errorId: string) => void;
  onDismissAll: () => void;
  onRequestFix: (error: RuntimeError) => void;
  showCompact?: boolean;
}

export function ErrorCapture({
  errors,
  onDismiss,
  onDismissAll,
  onRequestFix,
  showCompact = false
}: ErrorCaptureProps) {
  if (errors.length === 0) return null;

  if (showCompact) {
    return <CompactErrorBadge errors={errors} onDismissAll={onDismissAll} />;
  }

  return (
    <div className="absolute bottom-0 left-0 right-0 z-40 max-h-64 overflow-y-auto">
      <AnimatePresence>
        {errors.map((error) => (
          <ErrorCard
            key={error.id}
            error={error}
            onDismiss={() => onDismiss(error.id)}
            onRequestFix={() => onRequestFix(error)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

/**
 * Individual Error Card
 */
function ErrorCard({
  error,
  onDismiss,
  onRequestFix
}: {
  error: RuntimeError;
  onDismiss: () => void;
  onRequestFix: () => void;
}) {
  const [showStack, setShowStack] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const errorText = `${error.message}\n\n${error.stack || ''}`;
    await navigator.clipboard.writeText(errorText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 20, opacity: 0 }}
      className={cn(
        "m-2 rounded-lg border p-4",
        error.severity === 'error' && "border-red-500/50 bg-gradient-to-br from-red-950/80 to-black backdrop-blur-sm",
        error.severity === 'warning' && "border-amber-500/50 bg-gradient-to-br from-amber-950/80 to-black backdrop-blur-sm"
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-2">
        <AlertCircle className={cn(
          "h-5 w-5 mt-0.5 flex-shrink-0",
          error.severity === 'error' && "text-red-500",
          error.severity === 'warning' && "text-amber-500"
        )} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              "text-xs font-medium uppercase px-2 py-0.5 rounded",
              error.severity === 'error' && "bg-red-900/50 text-red-300",
              error.severity === 'warning' && "bg-amber-900/50 text-amber-300"
            )}>
              {error.type}
            </span>
            {error.file && (
              <span className="text-xs text-gray-400">
                {error.file}
                {error.line && `:${error.line}`}
                {error.column && `:${error.column}`}
              </span>
            )}
          </div>

          <p className={cn(
            "text-sm font-medium",
            error.severity === 'error' && "text-red-200",
            error.severity === 'warning' && "text-amber-200"
          )}>
            {error.message}
          </p>
        </div>

        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-300 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Stack Trace */}
      {error.stack && (
        <div className="mb-3">
          <button
            onClick={() => setShowStack(!showStack)}
            className="text-xs text-gray-400 hover:text-gray-300 transition-colors"
          >
            {showStack ? '▼' : '▶'} Stack Trace
          </button>

          {showStack && (
            <pre className="mt-2 text-xs text-gray-300 bg-black/50 p-2 rounded overflow-x-auto">
              {error.stack}
            </pre>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={onRequestFix}
          className={cn(
            "flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors",
            error.severity === 'error' && "bg-red-600 hover:bg-red-700 text-white",
            error.severity === 'warning' && "bg-amber-600 hover:bg-amber-700 text-white"
          )}
        >
          <Sparkles className="h-3 w-3" />
          AI Auto-Fix
        </button>

        <button
          onClick={handleCopy}
          className="px-3 py-1.5 border border-gray-700 hover:bg-gray-800 rounded text-xs font-medium transition-colors text-gray-300"
        >
          <Copy className="h-3 w-3" />
          {copied ? '✓' : ''}
        </button>
      </div>
    </motion.div>
  );
}

/**
 * Compact Error Badge - Shows error count in corner
 */
function CompactErrorBadge({
  errors,
  onDismissAll
}: {
  errors: RuntimeError[];
  onDismissAll: () => void;
}) {
  const errorCount = errors.filter(e => e.severity === 'error').length;
  const warningCount = errors.filter(e => e.severity === 'warning').length;

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="absolute bottom-2 right-2 flex items-center gap-2"
    >
      {errorCount > 0 && (
        <button
          onClick={onDismissAll}
          className="flex items-center gap-1.5 px-2 py-1 bg-red-900/80 hover:bg-red-900 text-red-300 rounded-md text-xs font-medium transition-colors"
        >
          <AlertCircle className="h-3 w-3" />
          {errorCount} {errorCount === 1 ? 'Error' : 'Errors'}
        </button>
      )}

      {warningCount > 0 && (
        <button
          onClick={onDismissAll}
          className="flex items-center gap-1.5 px-2 py-1 bg-amber-900/80 hover:bg-amber-900 text-amber-300 rounded-md text-xs font-medium transition-colors"
        >
          <Bug className="h-3 w-3" />
          {warningCount} {warningCount === 1 ? 'Warning' : 'Warnings'}
        </button>
      )}
    </motion.div>
  );
}

/**
 * Hook to capture Sandpack errors
 */
export function useSandpackErrors() {
  const [errors, setErrors] = useState<RuntimeError[]>([]);

  const addError = useCallback((error: Omit<RuntimeError, 'id' | 'timestamp'>) => {
    const newError: RuntimeError = {
      ...error,
      id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };

    setErrors(prev => [...prev, newError]);
  }, []);

  const dismissError = useCallback((errorId: string) => {
    setErrors(prev => prev.filter(e => e.id !== errorId));
  }, []);

  const dismissAll = useCallback(() => {
    setErrors([]);
  }, []);

  const clearOldErrors = useCallback((maxAge: number = 30000) => {
    const now = Date.now();
    setErrors(prev => prev.filter(e => now - e.timestamp.getTime() < maxAge));
  }, []);

  // Auto-clear old errors every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => clearOldErrors(), 30000);
    return () => clearInterval(interval);
  }, [clearOldErrors]);

  return {
    errors,
    addError,
    dismissError,
    dismissAll,
    clearOldErrors
  };
}

/**
 * Parse Sandpack error messages
 */
export function parseSandpackError(errorMessage: string, errorStack?: string): Omit<RuntimeError, 'id' | 'timestamp'> {
  // Extract file, line, column from stack trace
  const fileMatch = errorStack?.match(/at\s+(.+?):(\d+):(\d+)/);
  const file = fileMatch?.[1];
  const line = fileMatch?.[2] ? parseInt(fileMatch[2]) : undefined;
  const column = fileMatch?.[3] ? parseInt(fileMatch[3]) : undefined;

  // Determine error type
  let type: RuntimeError['type'] = 'runtime';
  if (errorMessage.includes('SyntaxError')) type = 'syntax';
  if (errorMessage.includes('TypeError')) type = 'type';
  if (errorMessage.includes('NetworkError') || errorMessage.includes('fetch')) type = 'network';

  // Determine severity
  const severity: RuntimeError['severity'] = errorMessage.includes('Warning') ? 'warning' : 'error';

  return {
    message: errorMessage,
    stack: errorStack,
    file,
    line,
    column,
    type,
    severity
  };
}

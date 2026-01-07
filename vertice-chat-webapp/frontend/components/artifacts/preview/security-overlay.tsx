'use client';

/**
 * Security Overlay Components
 *
 * PROJECT VIVID - Phase 2.1: Constitutional Feedback
 *
 * Features:
 * - Security scanning overlay during code generation
 * - Red shield overlay when Guardian Agent blocks code
 * - Visual feedback for security violations
 *
 * Constitutional Compliance: CODE_CONSTITUTION.md
 * - Truth Obligation: Explicit security status
 * - Sovereignty of Intent: Clear blocking reasons
 */

import { Shield, ShieldAlert, ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export type SecurityStatus = 'scanning' | 'safe' | 'blocked' | 'warning' | null;

export interface SecurityViolation {
  type: 'xss' | 'sql-injection' | 'command-injection' | 'unsafe-eval' | 'dangerous-pattern';
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  line?: number;
  column?: number;
  suggestion?: string;
}

export interface SecurityOverlayProps {
  status: SecurityStatus;
  violations?: SecurityViolation[];
  scanProgress?: number; // 0-100
  onDismiss?: () => void;
  onAcceptRisk?: () => void;
}

export function SecurityOverlay({
  status,
  violations = [],
  scanProgress = 0,
  onDismiss,
  onAcceptRisk
}: SecurityOverlayProps) {
  if (!status) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          className={cn(
            "max-w-md w-full mx-4 rounded-lg border p-6",
            status === 'scanning' && "border-cyan-500/50 bg-gradient-to-br from-cyan-950/50 to-black",
            status === 'safe' && "border-green-500/50 bg-gradient-to-br from-green-950/50 to-black",
            status === 'blocked' && "border-red-500/50 bg-gradient-to-br from-red-950/50 to-black",
            status === 'warning' && "border-amber-500/50 bg-gradient-to-br from-amber-950/50 to-black"
          )}
        >
          {status === 'scanning' && (
            <ScanningOverlay progress={scanProgress} />
          )}

          {status === 'safe' && (
            <SafeOverlay onDismiss={onDismiss} />
          )}

          {status === 'blocked' && (
            <BlockedOverlay
              violations={violations}
              onDismiss={onDismiss}
              onAcceptRisk={onAcceptRisk}
            />
          )}

          {status === 'warning' && (
            <WarningOverlay
              violations={violations}
              onDismiss={onDismiss}
              onAcceptRisk={onAcceptRisk}
            />
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * Scanning Overlay - Shows while code is being analyzed
 */
function ScanningOverlay({ progress }: { progress: number }) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Shield className="h-16 w-16 text-cyan-500" />
        </motion.div>
      </div>

      <h3 className="text-xl font-semibold text-cyan-100 mb-2">
        Security Scanning...
      </h3>

      <p className="text-sm text-cyan-300/70 mb-4">
        Analyzing code for security vulnerabilities
      </p>

      {/* Progress Bar */}
      <div className="w-full bg-cyan-950/50 rounded-full h-2 mb-2">
        <motion.div
          className="bg-cyan-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <p className="text-xs text-cyan-400/50">
        {Math.round(progress)}% complete
      </p>
    </div>
  );
}

/**
 * Safe Overlay - Code passed security checks
 */
function SafeOverlay({ onDismiss }: { onDismiss?: () => void }) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 10 }}
        >
          <ShieldCheck className="h-16 w-16 text-green-500" />
        </motion.div>
      </div>

      <h3 className="text-xl font-semibold text-green-100 mb-2">
        Code is Safe
      </h3>

      <p className="text-sm text-green-300/70 mb-4">
        No security vulnerabilities detected
      </p>

      <button
        onClick={onDismiss}
        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
      >
        Continue
      </button>
    </div>
  );
}

/**
 * Blocked Overlay - Guardian Agent blocked dangerous code
 */
function BlockedOverlay({
  violations,
  onDismiss,
  onAcceptRisk
}: {
  violations: SecurityViolation[];
  onDismiss?: () => void;
  onAcceptRisk?: () => void;
}) {
  const criticalViolations = violations.filter(v => v.severity === 'critical');

  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 0.5, repeat: Infinity }}
        >
          <ShieldAlert className="h-16 w-16 text-red-500" />
        </motion.div>
      </div>

      <h3 className="text-xl font-semibold text-red-100 mb-2">
        🛡️ Code Blocked by Guardian
      </h3>

      <p className="text-sm text-red-300/70 mb-4">
        {criticalViolations.length} critical security {criticalViolations.length === 1 ? 'issue' : 'issues'} detected
      </p>

      {/* Violations List */}
      <div className="text-left bg-red-950/30 rounded-lg p-4 mb-4 max-h-48 overflow-y-auto">
        {violations.map((violation, idx) => (
          <div key={idx} className="mb-3 last:mb-0">
            <div className="flex items-start gap-2">
              <AlertTriangle className={cn(
                "h-4 w-4 mt-0.5 flex-shrink-0",
                violation.severity === 'critical' && "text-red-500",
                violation.severity === 'high' && "text-orange-500",
                violation.severity === 'medium' && "text-amber-500",
                violation.severity === 'low' && "text-yellow-500"
              )} />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-200">
                  {violation.type.replace(/-/g, ' ').toUpperCase()}
                </p>
                <p className="text-xs text-red-300/70 mt-1">
                  {violation.message}
                </p>
                {violation.line && (
                  <p className="text-xs text-red-400/50 mt-1">
                    Line {violation.line}{violation.column && `:${violation.column}`}
                  </p>
                )}
                {violation.suggestion && (
                  <p className="text-xs text-green-400 mt-2 italic">
                    💡 {violation.suggestion}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={onDismiss}
          className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Fix Issues
        </button>
        {onAcceptRisk && (
          <button
            onClick={onAcceptRisk}
            className="flex-1 px-4 py-2 border border-red-500/50 hover:bg-red-900/30 text-red-300 rounded-lg transition-colors"
          >
            Accept Risk
          </button>
        )}
      </div>

      <p className="text-xs text-red-400/50 mt-3">
        ⚠️ Running unsafe code may compromise your system
      </p>
    </div>
  );
}

/**
 * Warning Overlay - Non-critical security issues
 */
function WarningOverlay({
  violations,
  onDismiss,
  onAcceptRisk
}: {
  violations: SecurityViolation[];
  onDismiss?: () => void;
  onAcceptRisk?: () => void;
}) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <AlertTriangle className="h-16 w-16 text-amber-500" />
      </div>

      <h3 className="text-xl font-semibold text-amber-100 mb-2">
        Security Warnings
      </h3>

      <p className="text-sm text-amber-300/70 mb-4">
        {violations.length} potential {violations.length === 1 ? 'issue' : 'issues'} found
      </p>

      {/* Violations List */}
      <div className="text-left bg-amber-950/30 rounded-lg p-4 mb-4 max-h-48 overflow-y-auto">
        {violations.map((violation, idx) => (
          <div key={idx} className="mb-3 last:mb-0">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-500 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-200">
                  {violation.type.replace(/-/g, ' ').toUpperCase()}
                </p>
                <p className="text-xs text-amber-300/70 mt-1">
                  {violation.message}
                </p>
                {violation.suggestion && (
                  <p className="text-xs text-green-400 mt-2 italic">
                    💡 {violation.suggestion}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={onDismiss}
          className="flex-1 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
        >
          Review
        </button>
        {onAcceptRisk && (
          <button
            onClick={onAcceptRisk}
            className="flex-1 px-4 py-2 border border-amber-500/50 hover:bg-amber-900/30 text-amber-300 rounded-lg transition-colors"
          >
            Continue Anyway
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Compact Security Badge - Shows in preview corner
 */
export function SecurityBadge({
  status,
  violationCount = 0,
  onClick
}: {
  status: SecurityStatus;
  violationCount?: number;
  onClick?: () => void;
}) {
  if (!status || status === 'scanning') return null;

  return (
    <motion.button
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      onClick={onClick}
      className={cn(
        "absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors",
        status === 'safe' && "bg-green-900/80 text-green-300 hover:bg-green-900",
        status === 'blocked' && "bg-red-900/80 text-red-300 hover:bg-red-900",
        status === 'warning' && "bg-amber-900/80 text-amber-300 hover:bg-amber-900"
      )}
    >
      {status === 'safe' && <ShieldCheck className="h-3 w-3" />}
      {status === 'blocked' && <ShieldAlert className="h-3 w-3" />}
      {status === 'warning' && <AlertTriangle className="h-3 w-3" />}

      <span>
        {status === 'safe' && 'Secure'}
        {status === 'blocked' && `Blocked (${violationCount})`}
        {status === 'warning' && `Warning (${violationCount})`}
      </span>
    </motion.button>
  );
}

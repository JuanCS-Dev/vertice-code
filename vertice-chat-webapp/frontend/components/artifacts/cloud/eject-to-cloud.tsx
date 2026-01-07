'use client';

/**
 * Eject to Cloud Component
 *
 * PROJECT VIVID - Phase 3.2: File Sync
 *
 * Features:
 * - Deploy current Sandpack state to cloud MCP
 * - Sync files between browser and cloud
 * - Persistent file storage
 * - Real backend execution
 *
 * This is the "Bolt-Killer" - true cloud execution vs Bolt's browser-only
 */

import { useState, useCallback } from 'react';
import { Cloud, CloudOff, Upload, Download, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export type CloudStatus = 'idle' | 'uploading' | 'synced' | 'error' | 'downloading';

export interface EjectToCloudProps {
  files: Record<string, string>;
  projectName?: string;
  onEject?: (success: boolean) => void;
  onSync?: (direction: 'upload' | 'download') => void;
}

export function EjectToCloud({
  files,
  projectName = 'my-project',
  onEject,
  onSync
}: EjectToCloudProps) {
  const [status, setStatus] = useState<CloudStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  // Eject files to cloud
  const handleEject = useCallback(async () => {
    setStatus('uploading');
    setError(null);
    setProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // Send files to cloud MCP
      const response = await fetch('/api/v1/mcp/eject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectName,
          files,
          timestamp: new Date().toISOString()
        }),
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        throw new Error(`Eject failed: ${response.statusText}`);
      }

      const data = await response.json();

      setStatus('synced');
      setLastSyncTime(new Date());
      onEject?.(true);

      // Auto-return to idle after 3 seconds
      setTimeout(() => {
        setStatus('idle');
        setProgress(0);
      }, 3000);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
      onEject?.(false);

      // Auto-return to idle after 5 seconds
      setTimeout(() => {
        setStatus('idle');
        setError(null);
        setProgress(0);
      }, 5000);
    }
  }, [files, projectName, onEject]);

  // Download from cloud
  const handleDownload = useCallback(async () => {
    setStatus('downloading');
    setError(null);

    try {
      const response = await fetch(`/api/v1/mcp/download?project=${projectName}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      const data = await response.json();

      setStatus('synced');
      setLastSyncTime(new Date());
      onSync?.('download');

      setTimeout(() => {
        setStatus('idle');
      }, 3000);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');

      setTimeout(() => {
        setStatus('idle');
        setError(null);
      }, 5000);
    }
  }, [projectName, onSync]);

  const fileCount = Object.keys(files).length;

  return (
    <div className="flex items-center gap-2">
      {/* Main Eject Button */}
      <button
        onClick={handleEject}
        disabled={status === 'uploading' || status === 'downloading'}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
          status === 'idle' && "bg-cyan-600 hover:bg-cyan-700 text-white",
          status === 'uploading' && "bg-cyan-700 text-white cursor-not-allowed",
          status === 'synced' && "bg-green-600 text-white",
          status === 'error' && "bg-red-600 text-white",
          status === 'downloading' && "bg-blue-600 text-white cursor-not-allowed"
        )}
        title={`Eject ${fileCount} files to cloud`}
      >
        {status === 'idle' && (
          <>
            <Cloud className="h-4 w-4" />
            Eject to Cloud
          </>
        )}

        {status === 'uploading' && (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Uploading {progress}%
          </>
        )}

        {status === 'synced' && (
          <>
            <CheckCircle2 className="h-4 w-4" />
            Synced!
          </>
        )}

        {status === 'error' && (
          <>
            <AlertCircle className="h-4 w-4" />
            Failed
          </>
        )}

        {status === 'downloading' && (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Downloading...
          </>
        )}
      </button>

      {/* Download Button */}
      <button
        onClick={handleDownload}
        disabled={status === 'uploading' || status === 'downloading'}
        className="p-1.5 hover:bg-gray-800 rounded transition-colors text-gray-400 hover:text-gray-300"
        title="Download from cloud"
      >
        <Download className="h-4 w-4" />
      </button>

      {/* Status Info */}
      {lastSyncTime && status === 'idle' && (
        <span className="text-xs text-gray-500">
          Last sync: {formatRelativeTime(lastSyncTime)}
        </span>
      )}

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="absolute top-full left-0 mt-2 p-2 bg-red-900/90 border border-red-500/50 rounded text-xs text-red-200 whitespace-nowrap"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Cloud Sync Badge - Shows sync status in corner
 */
export function CloudSyncBadge({
  status,
  onClick
}: {
  status: CloudStatus;
  onClick?: () => void;
}) {
  return (
    <motion.button
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      onClick={onClick}
      className={cn(
        "absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors",
        status === 'idle' && "bg-gray-800 text-gray-400",
        status === 'uploading' && "bg-cyan-900/80 text-cyan-300",
        status === 'synced' && "bg-green-900/80 text-green-300",
        status === 'error' && "bg-red-900/80 text-red-300",
        status === 'downloading' && "bg-blue-900/80 text-blue-300"
      )}
    >
      {status === 'idle' && <CloudOff className="h-3 w-3" />}
      {status === 'uploading' && <Upload className="h-3 w-3 animate-pulse" />}
      {status === 'synced' && <CheckCircle2 className="h-3 w-3" />}
      {status === 'error' && <AlertCircle className="h-3 w-3" />}
      {status === 'downloading' && <Download className="h-3 w-3 animate-pulse" />}

      <span>
        {status === 'idle' && 'Cloud'}
        {status === 'uploading' && 'Uploading...'}
        {status === 'synced' && 'Synced'}
        {status === 'error' && 'Error'}
        {status === 'downloading' && 'Downloading...'}
      </span>
    </motion.button>
  );
}

/**
 * Format relative time
 */
function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

/**
 * File Sync API Functions
 */
export async function uploadToCloud(
  projectName: string,
  files: Record<string, string>
): Promise<boolean> {
  try {
    const response = await fetch('/api/v1/mcp/eject', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        projectName,
        files,
        timestamp: new Date().toISOString()
      }),
    });

    return response.ok;
  } catch (error) {
    console.error('Upload failed:', error);
    return false;
  }
}

export async function downloadFromCloud(
  projectName: string
): Promise<Record<string, string> | null> {
  try {
    const response = await fetch(`/api/v1/mcp/download?project=${projectName}`, {
      method: 'GET',
    });

    if (!response.ok) return null;

    const data = await response.json();
    return data.files;
  } catch (error) {
    console.error('Download failed:', error);
    return null;
  }
}

export async function syncFiles(
  projectName: string,
  localFiles: Record<string, string>
): Promise<{ success: boolean; conflicts?: string[] }> {
  try {
    const response = await fetch('/api/v1/mcp/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        projectName,
        localFiles,
        timestamp: new Date().toISOString()
      }),
    });

    if (!response.ok) return { success: false };

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Sync failed:', error);
    return { success: false };
  }
}

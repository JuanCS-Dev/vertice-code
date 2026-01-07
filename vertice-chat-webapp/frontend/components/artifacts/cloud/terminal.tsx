'use client';

/**
 * Cloud Terminal Component
 *
 * PROJECT VIVID - Phase 3.1: The Terminal
 *
 * Features:
 * - xterm.js terminal in bottom panel
 * - WebSocket connection to backend MCP
 * - Real command execution in cloud sandbox
 * - File system operations
 * - Python/Node.js execution
 *
 * Reference: https://xtermjs.org/
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { Terminal as TerminalIcon, X, Maximize2, Minimize2, Power, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import '@xterm/xterm/css/xterm.css';

export interface TerminalProps {
  className?: string;
  onCommand?: (command: string) => void;
  onOutput?: (output: string) => void;
  autoConnect?: boolean;
}

export function Terminal({
  className,
  onCommand,
  onOutput,
  autoConnect = true
}: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [isConnected, setIsConnected] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [currentCommand, setCurrentCommand] = useState('');

  // Initialize xterm.js
  useEffect(() => {
    if (!terminalRef.current || xtermRef.current) return;

    // Create terminal instance
    const term = new XTerm({
      cursorBlink: true,
      cursorStyle: 'block',
      fontSize: 14,
      fontFamily: '"Fira Code", "JetBrains Mono", Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#050505',
        foreground: '#e5e5e5',
        cursor: '#22D3EE',
        cursorAccent: '#050505',
        selection: 'rgba(34, 211, 238, 0.3)',
        black: '#1e1e1e',
        red: '#ef4444',
        green: '#22c55e',
        yellow: '#f59e0b',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#22D3EE',
        white: '#e5e5e5',
        brightBlack: '#6b7280',
        brightRed: '#f87171',
        brightGreen: '#4ade80',
        brightYellow: '#fbbf24',
        brightBlue: '#60a5fa',
        brightMagenta: '#c084fc',
        brightCyan: '#67e8f9',
        brightWhite: '#ffffff'
      },
      allowProposedApi: true
    });

    // Add addons
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);

    // Open terminal
    term.open(terminalRef.current);
    fitAddon.fit();

    // Store refs
    xtermRef.current = term;
    fitAddonRef.current = fitAddon;

    // Welcome message
    term.writeln('\x1b[1;36m╔══════════════════════════════════════════════╗\x1b[0m');
    term.writeln('\x1b[1;36m║   ⚡ VERTICE CLOUD TERMINAL - Phase 3 ⚡    ║\x1b[0m');
    term.writeln('\x1b[1;36m╚══════════════════════════════════════════════╝\x1b[0m');
    term.writeln('');
    term.writeln('\x1b[1;33mConnecting to cloud sandbox...\x1b[0m');
    term.writeln('');

    // Handle input
    let lineBuffer = '';
    term.onData((data) => {
      const code = data.charCodeAt(0);

      // Handle special keys
      if (code === 13) { // Enter
        term.write('\r\n');
        if (lineBuffer.trim()) {
          handleCommand(lineBuffer.trim());
          setCurrentCommand(lineBuffer.trim());
          onCommand?.(lineBuffer.trim());
        }
        lineBuffer = '';
        term.write('$ ');
      } else if (code === 127) { // Backspace
        if (lineBuffer.length > 0) {
          lineBuffer = lineBuffer.slice(0, -1);
          term.write('\b \b');
        }
      } else if (code === 3) { // Ctrl+C
        term.write('^C\r\n$ ');
        lineBuffer = '';
      } else if (code >= 32) { // Printable characters
        lineBuffer += data;
        term.write(data);
      }
    });

    // Auto-resize on window resize
    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener('resize', handleResize);

    // Auto-connect if enabled
    if (autoConnect) {
      setTimeout(() => connectToBackend(), 1000);
    }

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
      wsRef.current?.close();
    };
  }, []);

  // Handle commands
  const handleCommand = useCallback((command: string) => {
    const term = xtermRef.current;
    if (!term) return;

    // Send to WebSocket if connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        data: command
      }));
    } else {
      // Simulate local commands
      simulateCommand(command);
    }
  }, []);

  // Simulate commands (for demo when not connected)
  const simulateCommand = (command: string) => {
    const term = xtermRef.current;
    if (!term) return;

    const cmd = command.trim().toLowerCase();

    if (cmd === 'help') {
      term.writeln('Available commands:');
      term.writeln('  ls           - List files');
      term.writeln('  pwd          - Print working directory');
      term.writeln('  clear        - Clear terminal');
      term.writeln('  connect      - Connect to cloud backend');
      term.writeln('  disconnect   - Disconnect from cloud');
      term.writeln('  help         - Show this help');
    } else if (cmd === 'ls') {
      term.writeln('App.tsx    Button.tsx    styles.css    package.json');
    } else if (cmd === 'pwd') {
      term.writeln('/workspace/vertice-project');
    } else if (cmd === 'clear') {
      term.clear();
    } else if (cmd === 'connect') {
      connectToBackend();
    } else if (cmd === 'disconnect') {
      disconnectFromBackend();
    } else if (cmd.startsWith('echo ')) {
      term.writeln(cmd.substring(5));
    } else if (cmd === '') {
      // Empty command, do nothing
    } else {
      term.writeln(`\x1b[31mCommand not found: ${command}\x1b[0m`);
      term.writeln('Type "help" for available commands');
    }

    onOutput?.(command);
  };

  // Connect to backend WebSocket
  const connectToBackend = useCallback(() => {
    const term = xtermRef.current;
    if (!term) return;

    term.writeln('');
    term.writeln('\x1b[1;33m⚡ Establishing WebSocket connection...\x1b[0m');

    try {
      // WebSocket URL (to be implemented in backend)
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/terminal`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        term.writeln('\x1b[1;32m✓ Connected to Vertice Cloud\x1b[0m');
        term.writeln('');
        term.write('$ ');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'output') {
            term.write(message.data);
          } else if (message.type === 'error') {
            term.writeln(`\x1b[31m${message.data}\x1b[0m`);
          }
        } catch (err) {
          term.write(event.data);
        }
      };

      ws.onerror = (error) => {
        term.writeln('\x1b[31m✗ Connection failed\x1b[0m');
        term.writeln('\x1b[33mFalling back to local simulation mode\x1b[0m');
        term.writeln('');
        term.write('$ ');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        term.writeln('');
        term.writeln('\x1b[33m⚠ Disconnected from cloud\x1b[0m');
        term.writeln('');
        term.write('$ ');
      };

      wsRef.current = ws;
    } catch (error) {
      term.writeln('\x1b[31m✗ Failed to establish connection\x1b[0m');
      term.writeln('');
      term.write('$ ');
    }
  }, []);

  // Disconnect from backend
  const disconnectFromBackend = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Clear terminal
  const handleClear = useCallback(() => {
    xtermRef.current?.clear();
  }, []);

  // Reconnect
  const handleReconnect = useCallback(() => {
    disconnectFromBackend();
    setTimeout(() => connectToBackend(), 500);
  }, [connectToBackend, disconnectFromBackend]);

  // Toggle maximize
  const toggleMaximize = useCallback(() => {
    setIsMaximized(!isMaximized);
    setTimeout(() => {
      fitAddonRef.current?.fit();
    }, 100);
  }, [isMaximized]);

  return (
    <div
      className={cn(
        "flex flex-col bg-[#050505] border border-gray-800 rounded-lg overflow-hidden transition-all duration-200",
        isMaximized ? "fixed inset-4 z-50" : "h-full",
        className
      )}
    >
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-900/50 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-4 w-4 text-cyan-500" />
          <span className="text-sm font-medium text-gray-300">Cloud Terminal</span>
          {isConnected && (
            <span className="flex items-center gap-1 text-xs text-green-500">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Connected
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleReconnect}
            className="p-1.5 hover:bg-gray-800 rounded transition-colors"
            title="Reconnect"
          >
            <RefreshCw className="h-3.5 w-3.5 text-gray-400" />
          </button>

          <button
            onClick={handleClear}
            className="p-1.5 hover:bg-gray-800 rounded transition-colors"
            title="Clear"
          >
            <X className="h-3.5 w-3.5 text-gray-400" />
          </button>

          <button
            onClick={toggleMaximize}
            className="p-1.5 hover:bg-gray-800 rounded transition-colors"
            title={isMaximized ? "Minimize" : "Maximize"}
          >
            {isMaximized ? (
              <Minimize2 className="h-3.5 w-3.5 text-gray-400" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div
        ref={terminalRef}
        className="flex-1 p-2 overflow-hidden"
        style={{ minHeight: isMaximized ? 'calc(100vh - 100px)' : '300px' }}
      />
    </div>
  );
}

/**
 * Compact Terminal Button - Shows terminal toggle in artifact toolbar
 */
export function TerminalToggle({
  isOpen,
  onClick
}: {
  isOpen: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors",
        isOpen
          ? "bg-cyan-600 text-white"
          : "bg-gray-800 text-gray-300 hover:bg-gray-700"
      )}
      title="Toggle Terminal (Ctrl+`)"
    >
      <TerminalIcon className="h-3.5 w-3.5" />
      Terminal
    </button>
  );
}

'use client';

/**
 * Sandpack Client - In-Browser Preview Component
 *
 * PROJECT VIVID - Phase 1.1: Core Integration
 *
 * Features:
 * - Sandpack v2.0 + Nodebox (Safari/iOS support)
 * - Instant React component rendering
 * - Tailwind CSS v4 support
 * - Vertice Void theme customization
 *
 * Reference: https://sandpack.codesandbox.io/docs/
 */

import {
  Sandpack,
  SandpackPreview,
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackTheme,
  useSandpack
} from '@codesandbox/sandpack-react';
import { useState, useEffect, useCallback } from 'react';
import { SecurityOverlay, SecurityBadge, SecurityStatus, SecurityViolation } from './security-overlay';
import { ErrorCapture, useSandpackErrors, parseSandpackError, RuntimeError } from './error-capture';

/**
 * Vertice Void Theme
 * Matches the dark theme (#050505) of the main application
 */
const VERTICE_VOID_THEME: SandpackTheme = {
  colors: {
    surface1: '#050505',    // Main background
    surface2: '#0a0a0a',    // Secondary background
    surface3: '#121212',    // Elevated surface
    disabled: '#2a2a2a',    // Disabled elements
    base: '#ffffff',        // Text color
    clickable: '#22D3EE',   // Cyan accent
    hover: '#0ea5e9',       // Sky blue hover
    accent: '#22D3EE',      // Primary accent
    error: '#ef4444',       // Red error
    errorSurface: '#7f1d1d', // Error background
    warning: '#f59e0b',     // Amber warning
    warningSurface: '#78350f' // Warning background
  },
  syntax: {
    plain: '#e5e5e5',        // Plain text
    comment: {
      color: '#6b7280',      // Gray comments
      fontStyle: 'italic'
    },
    keyword: '#a78bfa',      // Purple keywords
    tag: '#22D3EE',          // Cyan tags
    punctuation: '#e5e5e5',  // White punctuation
    definition: '#fbbf24',   // Amber definitions
    property: '#34d399',     // Green properties
    static: '#f472b6',       // Pink static
    string: '#86efac'        // Light green strings
  },
  font: {
    body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"Fira Code", "JetBrains Mono", Menlo, Monaco, "Courier New", monospace',
    size: '14px',
    lineHeight: '1.6'
  }
};

/**
 * Tailwind CSS v4 Setup for Sandpack
 * Ensures Tailwind works in preview
 */
const TAILWIND_SETUP = {
  '/styles.css': {
    code: `@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom Vertice styles */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #050505;
  color: #ffffff;
}

* {
  box-sizing: border-box;
}`,
    active: true
  },
  '/tailwind.config.js': {
    code: `module.exports = {
  content: ['./**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'void': {
          DEFAULT: '#050505',
          light: '#0a0a0a',
          dark: '#000000'
        },
        'cyan': {
          DEFAULT: '#22D3EE',
          light: '#67e8f9',
          dark: '#0ea5e9'
        }
      }
    }
  }
}`
  }
};

export interface SandpackClientProps {
  files: Record<string, string>;
  template?: 'react' | 'react-ts' | 'vanilla' | 'vanilla-ts';
  showEditor?: boolean;
  showPreview?: boolean;
  editable?: boolean;
  autorun?: boolean;
  onFilesChange?: (files: Record<string, string>) => void;
  onError?: (error: RuntimeError) => void; // PROJECT VIVID Phase 2
  onSecurityViolation?: (violations: SecurityViolation[]) => void; // PROJECT VIVID Phase 2
}

/**
 * Internal component that captures Sandpack errors
 * Must be inside SandpackProvider to access useSandpack hook
 */
function SandpackErrorListener({
  onError
}: {
  onError?: (error: RuntimeError) => void;
}) {
  const { listen } = useSandpack();

  useEffect(() => {
    const unsubscribe = listen((message) => {
      if (message.type === 'error') {
        const parsedError = parseSandpackError(
          message.message || 'Unknown error',
          message.stack
        );

        onError?.({
          ...parsedError,
          id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date()
        });
      }
    });

    return () => unsubscribe();
  }, [listen, onError]);

  return null;
}

export function SandpackClient({
  files,
  template = 'react-ts',
  showEditor = false, // Hide by default (we use Monaco)
  showPreview = true,
  editable = false,
  autorun = true,
  onFilesChange,
  onError,
  onSecurityViolation
}: SandpackClientProps) {
  const [localFiles, setLocalFiles] = useState(files);
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus>(null);
  const [securityViolations, setSecurityViolations] = useState<SecurityViolation[]>([]);
  const { errors, addError, dismissError, dismissAll } = useSandpackErrors();

  // Sync external file changes
  useEffect(() => {
    setLocalFiles(files);
  }, [files]);

  // Security scanning simulation (Phase 2.1)
  useEffect(() => {
    if (!autorun) return;

    // Start scanning
    setSecurityStatus('scanning');

    // Simulate security scan
    const scanTimer = setTimeout(() => {
      const violations = scanCodeForViolations(Object.values(localFiles).join('\n'));

      if (violations.length > 0) {
        const hasCritical = violations.some(v => v.severity === 'critical');
        setSecurityStatus(hasCritical ? 'blocked' : 'warning');
        setSecurityViolations(violations);
        onSecurityViolation?.(violations);
      } else {
        setSecurityStatus('safe');
        // Auto-dismiss after 2 seconds
        setTimeout(() => setSecurityStatus(null), 2000);
      }
    }, 1500);

    return () => clearTimeout(scanTimer);
  }, [localFiles, autorun, onSecurityViolation]);

  // Merge user files with Tailwind setup
  const mergedFiles = {
    ...TAILWIND_SETUP,
    ...localFiles
  };

  // Configure Sandpack dependencies
  const customSetup = {
    dependencies: {
      'tailwindcss': '^4.0.0',
      'postcss': '^8.0.0',
      'autoprefixer': '^10.0.0',
      'react': '^18.2.0',
      'react-dom': '^18.2.0'
    }
  };

  const handleCodeChange = (newCode: string, filePath: string) => {
    const updatedFiles = {
      ...localFiles,
      [filePath]: newCode
    };
    setLocalFiles(updatedFiles);
    onFilesChange?.(updatedFiles);
  };

  // Handle error from Sandpack
  const handleSandpackError = useCallback((error: RuntimeError) => {
    addError(error);
    onError?.(error);
  }, [addError, onError]);

  // Handle security overlay dismissal
  const handleSecurityDismiss = useCallback(() => {
    setSecurityStatus(null);
  }, []);

  // Handle accept risk (for warnings)
  const handleAcceptRisk = useCallback(() => {
    setSecurityStatus(null);
  }, []);

  // Handle error fix request
  const handleRequestFix = useCallback((error: RuntimeError) => {
    // This will be integrated with chat in Phase 2.2
    console.log('Requesting AI fix for error:', error);
    // TODO: Send to chat API for auto-fix
  }, []);

  return (
    <div className="sandpack-container w-full h-full relative">
      <SandpackProvider
        template={template}
        files={mergedFiles}
        customSetup={customSetup}
        theme={VERTICE_VOID_THEME}
        options={{
          autorun,
          autoReload: true,
          showTabs: showEditor,
          showLineNumbers: true,
          showInlineErrors: true,
          wrapContent: true,
          editorHeight: showEditor ? 400 : 0,
          editorWidthPercentage: 50
        }}
      >
        {/* Error Listener (PROJECT VIVID Phase 2.2) */}
        <SandpackErrorListener onError={handleSandpackError} />

        <SandpackLayout>
          {showEditor && (
            <SandpackCodeEditor
              showTabs={true}
              showLineNumbers={true}
              showInlineErrors={true}
              wrapContent={true}
              closableTabs={false}
              readOnly={!editable}
            />
          )}

          {showPreview && (
            <div className="relative h-full">
              <SandpackPreview
                showOpenInCodeSandbox={false}
                showRefreshButton={true}
                showNavigator={false}
                actionsChildren={
                  <div className="flex items-center gap-2 px-2">
                    <span className="text-xs text-gray-400">
                      Live Preview
                    </span>
                  </div>
                }
              />

              {/* Security Badge (PROJECT VIVID Phase 2.1) */}
              <SecurityBadge
                status={securityStatus}
                violationCount={securityViolations.length}
                onClick={() => securityStatus && setSecurityStatus(securityStatus)}
              />

              {/* Error Capture (PROJECT VIVID Phase 2.2) */}
              <ErrorCapture
                errors={errors}
                onDismiss={dismissError}
                onDismissAll={dismissAll}
                onRequestFix={handleRequestFix}
                showCompact={false}
              />
            </div>
          )}
        </SandpackLayout>

        {/* Security Overlay (PROJECT VIVID Phase 2.1) */}
        <SecurityOverlay
          status={securityStatus}
          violations={securityViolations}
          scanProgress={75}
          onDismiss={handleSecurityDismiss}
          onAcceptRisk={handleAcceptRisk}
        />
      </SandpackProvider>
    </div>
  );
}

/**
 * Scan code for security violations
 * PROJECT VIVID Phase 2.1
 */
function scanCodeForViolations(code: string): SecurityViolation[] {
  const violations: SecurityViolation[] = [];

  // XSS Detection
  if (code.includes('dangerouslySetInnerHTML')) {
    violations.push({
      type: 'xss',
      severity: 'high',
      message: 'Potential XSS vulnerability: dangerouslySetInnerHTML detected',
      suggestion: 'Use React components or sanitize HTML with DOMPurify'
    });
  }

  // Unsafe eval
  if (code.match(/\beval\s*\(/)) {
    violations.push({
      type: 'unsafe-eval',
      severity: 'critical',
      message: 'Critical: eval() usage detected',
      suggestion: 'Refactor to avoid eval() - use JSON.parse() or Function() constructor with caution'
    });
  }

  // SQL Injection (template literals in SQL-like strings)
  if (code.match(/`SELECT.*\$\{.*\}`/i) || code.match(/`INSERT.*\$\{.*\}`/i)) {
    violations.push({
      type: 'sql-injection',
      severity: 'critical',
      message: 'Potential SQL injection: Template literals in SQL query',
      suggestion: 'Use parameterized queries or ORM'
    });
  }

  // Command Injection
  if (code.includes('child_process') || code.includes('exec(')) {
    violations.push({
      type: 'command-injection',
      severity: 'high',
      message: 'Potential command injection: Process execution detected',
      suggestion: 'Validate all inputs and use safe alternatives'
    });
  }

  // Dangerous patterns
  if (code.includes('__proto__') || code.includes('constructor.prototype')) {
    violations.push({
      type: 'dangerous-pattern',
      severity: 'high',
      message: 'Prototype pollution risk detected',
      suggestion: 'Avoid modifying __proto__ or prototype chain'
    });
  }

  return violations;
}

/**
 * Quick Preview - Renders a single file without editor
 */
export function SandpackQuickPreview({
  code,
  language = 'jsx',
  autorun = true
}: {
  code: string;
  language?: 'jsx' | 'tsx' | 'html';
  autorun?: boolean;
}) {
  const template = language === 'tsx' ? 'react-ts' : 'react';
  const fileName = language === 'html'
    ? '/index.html'
    : `/App.${language}`;

  const files = {
    [fileName]: code
  };

  return (
    <SandpackClient
      files={files}
      template={template}
      showEditor={false}
      showPreview={true}
      autorun={autorun}
    />
  );
}

/**
 * Debounced Monaco → Sandpack sync
 * Prevents re-render flashing during typing
 */
export function useDebouncedSync(
  monacoContent: string,
  delay: number = 500
) {
  const [debouncedContent, setDebouncedContent] = useState(monacoContent);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedContent(monacoContent);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [monacoContent, delay]);

  return debouncedContent;
}

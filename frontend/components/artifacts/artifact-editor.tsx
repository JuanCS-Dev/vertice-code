"use client";

import React, { useEffect, useState } from "react";
import Editor, { useMonaco, OnMount } from "@monaco-editor/react";
import { useArtifactStore } from "@/lib/stores/artifact-store";
import { Loader2 } from "lucide-react";

export function ArtifactEditor() {
  const { files, activeFileId, createOrUpdateFile } = useArtifactStore();
  const [mounted, setMounted] = useState(false);

  const activeFile = activeFileId ? files[activeFileId] : null;
  const monaco = useMonaco();

  // Custom Theme Definition
  useEffect(() => {
    if (monaco) {
      // We define the theme to match our 'Void' design token (#050505)
      // This ensures the editor feels native to the app
      monaco.editor.defineTheme('vertice-void', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token: 'comment', foreground: '6272a4' },
          { token: 'keyword', foreground: 'ff79c6' },
          { token: 'identifier', foreground: '8be9fd' },
          { token: 'string', foreground: 'f1fa8c' },
          { token: 'type', foreground: '8be9fd' },
        ],
        colors: {
          'editor.background': '#050505', // Matches var(--background)
          'editor.foreground': '#f8f8f2',
          'editor.lineHighlightBackground': '#101010',
          'editorLineNumber.foreground': '#6272a4',
          'editor.selectionBackground': '#44475a',
          'editor.inactiveSelectionBackground': '#44475a50',
        }
      });
      monaco.editor.setTheme('vertice-void');
    }
  }, [monaco]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    setMounted(true);
  };

  const handleChange = (value: string | undefined) => {
    if (activeFile && value !== undefined) {
      createOrUpdateFile(activeFile.name, value, activeFile.language);
    }
  };

  if (!activeFile) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground bg-background">
        <div className="text-center">
          <p>No file selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-background relative animate-fade-in">
      {!mounted && (
        <div className="absolute inset-0 flex items-center justify-center bg-background z-10">
          <Loader2 className="w-6 h-6 animate-spin text-accent" />
        </div>
      )}
      <Editor
        height="100%"
        path={activeFile.name}
        defaultLanguage={activeFile.language}
        language={activeFile.language}
        value={activeFile.content}
        onChange={handleChange}
        theme="vertice-void"
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', monospace",
          lineHeight: 1.6,
          padding: { top: 16, bottom: 16 },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: "smooth",
          cursorSmoothCaretAnimation: "on",
          fontLigatures: true,
          renderLineHighlight: "all",
          folding: true,
          wordWrap: "on",
        }}
      />
    </div>
  );
}

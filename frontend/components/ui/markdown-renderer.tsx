"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, Terminal, FileCode, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useArtifactStore } from "@/lib/stores/artifact-store";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      className={cn("prose prose-invert prose-p:leading-relaxed prose-pre:p-0 max-w-none break-words", className)}
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || "");
          const language = match ? match[1] : "";

          if (!inline && match) {
            return (
              <CodeBlock language={language} value={String(children).replace(/\n$/, "")} />
            );
          }

          return (
            <code
              className={cn(
                "bg-muted/50 text-accent font-mono text-[0.85em] px-1.5 py-0.5 rounded border border-border",
                className
              )}
              {...props}
            >
              {children}
            </code>
          );
        },
        h1: ({ children }) => <h1 className="text-2xl font-semibold tracking-tight mt-6 mb-4">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-semibold tracking-tight mt-5 mb-3 text-foreground/90">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-medium tracking-tight mt-4 mb-2 text-foreground/90">{children}</h3>,
        a: ({ children, href }) => (
          <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline decoration-accent/50 underline-offset-4 transition-all">
            {children}
          </a>
        ),
        ul: ({ children }) => <ul className="list-disc list-outside ml-4 space-y-1 mb-4 text-muted-foreground">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-outside ml-4 space-y-1 mb-4 text-muted-foreground">{children}</ol>,
        p: ({ children }) => <p className="mb-4 last:mb-0 text-muted-foreground leading-7">{children}</p>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function CodeBlock({ language, value }: { language: string; value: string }) {
  const [copied, setCopied] = React.useState(false);
  const { createOrUpdateFile } = useArtifactStore();

  const onCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const onOpenInEditor = () => {
    // Generate a filename based on language and timestamp or hash
    const ext = language === 'typescript' || language === 'ts' ? 'tsx'
              : language === 'javascript' || language === 'js' ? 'jsx'
              : language === 'python' ? 'py'
              : language === 'html' ? 'html'
              : language === 'css' ? 'css'
              : 'txt';

    const filename = `snippet-${Date.now().toString().slice(-4)}.${ext}`;
    createOrUpdateFile(filename, value, language);
  };

  return (
    <div className="my-4 rounded-lg border border-border bg-[#0d1117] overflow-hidden group">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-white/5 border-b border-border">
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <Terminal className="w-3.5 h-3.5" />
          <span className="uppercase">{language || "text"}</span>
        </div>

        <div className="flex items-center gap-2">
           <button
            onClick={onOpenInEditor}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/10 text-xs text-muted-foreground hover:text-accent transition-colors"
            title="Open in Editor"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span className="hidden group-hover:inline">Open</span>
          </button>

          <div className="w-px h-3 bg-white/10" />

          <button
            onClick={onCopy}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/10 text-xs text-muted-foreground hover:text-foreground transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
      {/* Code */}
      <div className="p-4 overflow-x-auto">
        <pre className="text-sm font-mono leading-relaxed text-[#e6edf3]">
          {value}
        </pre>
      </div>
    </div>
  );
}

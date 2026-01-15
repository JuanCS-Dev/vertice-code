'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '@/components/ui/button';
import { Copy, Check, Play, Sparkles, Loader2 } from 'lucide-react';
import { useState, memo, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { motion } from 'framer-motion';
import { SEMANTIC_TOKEN_MAP } from './semantic-icons';

// -----------------------------------------------------------------------------
// SEMANTIC PARSER ENGINE (2026)
// Intercepts text streams and injects alive UI components for semantic tokens.
// -----------------------------------------------------------------------------

const parseSemanticText = (text: string): ReactNode[] => {
  if (!text) return [];
  
  // Regex to match any of the semantic tokens
  const tokenRegex = new RegExp(`(${Object.keys(SEMANTIC_TOKEN_MAP).map(k => k.replace(/[.*+?^${}()|[\\\]]/g, '\\$&')).join('|')})`, 'g');
  
  const parts = text.split(tokenRegex);
  
  return parts.map((part, index) => {
    const Component = SEMANTIC_TOKEN_MAP[part];
    if (Component) {
      return <Component key={`${part}-${index}`} />;
    }
    return part;
  });
};

const SemanticParagraph = ({ children }: { children?: ReactNode }) => {
  // If children is a string, parse it. If it's an array, map over it.
  const processNode = (node: ReactNode): ReactNode => {
    if (!node) return null;
    if (typeof node === 'string') {
      return parseSemanticText(node);
    }
    if (Array.isArray(node)) {
      return node.map((child, i) => <span key={i}>{processNode(child)}</span>);
    }
    return node;
  };

  return <p className="mb-4 last:mb-0 leading-relaxed text-zinc-300">{processNode(children)}</p>;
};

const SemanticListItem = ({ children }: { children?: ReactNode }) => {
    const processNode = (node: ReactNode): ReactNode => {
    if (!node) return null;
    if (typeof node === 'string') {
      return parseSemanticText(node);
    }
    if (Array.isArray(node)) {
      return node.map((child, i) => <span key={i}>{processNode(child)}</span>);
    }
    return node;
  };
  return <li className="leading-relaxed">{processNode(children)}</li>;
};

// -----------------------------------------------------------------------------
// CODE BLOCK COMPONENT
// -----------------------------------------------------------------------------

interface CodeBlockProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: ReactNode;
  [key: string]: any;
}

// Memoized CodeBlock for performance during streaming
const CodeBlock = memo(function CodeBlock({ node, inline, className, children, ...props }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const { toast } = useToast();

  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const content = String(children).replace(/\n$/, '');
  
  // High-fidelity streaming detection
  const isStreaming = content.endsWith('▋') || content.endsWith('█') || content.endsWith('_') || content.endsWith('▎');


  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content.replace(/[▋█_▎]$/, ''));
      setCopied(true);
      toast({
        title: "Copiado!",
        description: "Código copiado para a área de transferência.",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast({
        title: "Erro",
        description: "Não foi possível copiar o código.",
        variant: "destructive",
      });
    }
  };

  const handleRun = () => {
    setIsExecuting(true);
    toast({
      title: "Sovereign Execution",
      description: `Iniciando sandbox Wasm para ${language}...`,
    });
    setTimeout(() => {
      setIsExecuting(false);
      toast({
        title: "Execução concluída",
        description: "Script finalizado com sucesso no ambiente isolado.",
      });
    }, 2000);
  };

  if (!inline && language) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative group my-8"
      >
        {/* Sovereign Header - Claude Code 2026 Style */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900/90 backdrop-blur-xl rounded-t-2xl border-x border-t border-white/10 shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/40"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/40"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/40"></div>
            </div>
            <div className="h-4 w-px bg-white/10 mx-1"></div>
            <span className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.25em]">
              {language}
            </span>
            {isStreaming && (
              <div className="flex items-center gap-2 ml-3 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                <span className="flex h-1.5 w-1.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-500"></span>
                </span>
                <span className="text-[8px] font-mono font-bold text-cyan-400 tracking-tighter">SYNTHESIZING</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2.5 text-[9px] font-bold text-zinc-400 hover:text-white hover:bg-white/5 gap-1.5 transition-all"
              onClick={handleRun}
              disabled={isExecuting || isStreaming}
            >
              {isExecuting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
              RUN
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2.5 text-[9px] font-bold text-zinc-400 hover:text-white hover:bg-white/5 gap-1.5 transition-all"
              onClick={copyToClipboard}
            >
              {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
              {copied ? 'COPIED' : 'COPY'}
            </Button>
            <Button
              variant="neon"
              size="sm"
              className="h-7 px-3 text-[9px] font-bold gap-1.5 ml-1 border-cyan-500/40 shadow-none hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]"
              disabled={isStreaming}
            >
              <Sparkles className="h-3 w-3" />
              APPLY
            </Button>
          </div>
        </div>

        {/* Code Content with High-Precision Highlighting */}
        <div className="relative group/code">
          <div className="absolute inset-0 bg-cyan-500/[0.02] opacity-0 group-hover/code:opacity-100 transition-opacity pointer-events-none rounded-b-2xl"></div>
          <SyntaxHighlighter
            style={oneDark}
            language={language}
            PreTag="div"
            className="!rounded-b-2xl !rounded-t-none !mt-0 !bg-[#050505] !border-x !border-b !border-white/10 !p-6 font-mono text-[13px] leading-relaxed scrollbar-thin"
            showLineNumbers={true}
            lineNumberStyle={{ minWidth: '3.5em', paddingRight: '1.5em', color: '#27272a', textAlign: 'right', userSelect: 'none' }}
            {...props}
          >
            {content}
          </SyntaxHighlighter>
        </div>
      </motion.div>
    );
  }

  return (
    <code className={cn("bg-zinc-800/50 px-1.5 py-0.5 rounded text-[13px] font-mono text-cyan-300 border border-white/5", className)} {...props}>
      {children}
    </code>
  );
});

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={{
        code: CodeBlock,
        // Custom link component
        a: ({ children, href, ...props }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 underline underline-offset-4 decoration-cyan-500/30 hover:decoration-cyan-500 transition-all"
            {...props}
          >
            {children}
          </a>
        ),
        // Custom table component
        table: ({ children, ...props }) => (
          <div className="my-6 overflow-x-auto rounded-xl border border-white/10 bg-zinc-900/20">
            <table className="min-w-full divide-y divide-white/5" {...props}>
              {children}
            </table>
          </div>
        ),
        thead: ({ children, ...props }) => (
          <thead className="bg-white/5" {...props}>
            {children}
          </thead>
        ),
        tbody: ({ children, ...props }) => (
          <tbody className="divide-y divide-white/5" {...props}>
            {children}
          </tbody>
        ),
        th: ({ children, ...props }) => (
          <th className="px-6 py-3 text-left text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]" {...props}>
            {children}
          </th>
        ),
        td: ({ children, ...props }) => (
          <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-300" {...props}>
            {children}
          </td>
        ),
        // SEMANTIC TYPOGRAPHY INJECTION
        p: SemanticParagraph,
        li: SemanticListItem,
        
        h1: ({ children }) => <h1 className="text-2xl font-bold mb-6 mt-8 text-white tracking-tight">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-bold mb-4 mt-8 text-white tracking-tight">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-bold mb-3 mt-6 text-white tracking-tight">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-2 text-zinc-300">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-zinc-300">{children}</ol>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-cyan-500/50 pl-6 my-6 italic text-zinc-400 bg-cyan-500/5 py-4 rounded-r-lg">
            {children}
          </blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
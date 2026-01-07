'use client';

import { useState, useEffect, useRef } from 'react';
import { useActiveArtifact, useArtifactsStore } from '@/lib/stores/artifacts-store';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Copy, Save, Undo } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

export function ArtifactEditor() {
  const activeArtifact = useActiveArtifact();
  const { updateArtifact, saveArtifact } = useArtifactsStore();
  const { toast } = useToast();

  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update content when active artifact changes
  useEffect(() => {
    if (activeArtifact) {
      setContent(activeArtifact.content || '');
    }
  }, [activeArtifact]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [content]);

  if (!activeArtifact) {
    return null;
  }

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    updateArtifact(activeArtifact.id, { content: newContent });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saveArtifact(activeArtifact.id);
      toast({
        title: "Salvo!",
        description: `"${activeArtifact.name}" foi salvo com sucesso.`,
      });
    } catch (error) {
      toast({
        title: "Erro",
        description: "Falha ao salvar o arquivo.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast({
        title: "Copiado!",
        description: "Conteúdo copiado para a área de transferência.",
      });
    } catch (error) {
      toast({
        title: "Erro",
        description: "Falha ao copiar o conteúdo.",
        variant: "destructive",
      });
    }
  };

  const handleUndo = () => {
    if (activeArtifact.originalContent !== undefined) {
      setContent(activeArtifact.originalContent);
      updateArtifact(activeArtifact.id, { content: activeArtifact.originalContent });
    }
  };

  const isModified = activeArtifact.isModified;
  const canUndo = activeArtifact.originalContent !== undefined && isModified;

  return (
    <div className="h-full flex flex-col">
      {/* Editor Header */}
      <div className="flex items-center justify-between p-4 border-b bg-muted/10">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="font-medium">{activeArtifact.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              {activeArtifact.language && (
                <Badge variant="secondary" className="text-xs">
                  {activeArtifact.language}
                </Badge>
              )}
              {activeArtifact.path && (
                <span className="text-xs text-muted-foreground">
                  {activeArtifact.path}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {canUndo && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleUndo}
              className="text-orange-600 hover:text-orange-700"
            >
              <Undo className="h-4 w-4 mr-2" />
              Desfazer
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
          >
            <Copy className="h-4 w-4 mr-2" />
            Copiar
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
            disabled={!isModified || isSaving}
            className={cn(
              isModified && "bg-green-600 hover:bg-green-700"
            )}
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {isSaving ? 'Salvando...' : 'Salvar'}
          </Button>
        </div>
      </div>

      {/* Editor Content */}
      <div className="flex-1 p-4 overflow-auto">
        <Textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => handleContentChange(e.target.value)}
          placeholder="Digite o conteúdo do arquivo..."
          className={cn(
            "min-h-[400px] font-mono text-sm resize-none border-0 shadow-none focus-visible:ring-0",
            "bg-transparent",
            activeArtifact.language && "whitespace-pre"
          )}
          style={{
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Monaco, Inconsolata, "Roboto Mono", monospace',
            fontSize: '14px',
            lineHeight: '1.5',
          }}
        />
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/10 text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>
            {content.split('\n').length} linhas
          </span>
          <span>
            {content.length} caracteres
          </span>
          {isModified && (
            <Badge variant="outline" className="text-orange-600">
              Modificado
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {activeArtifact.updatedAt && (
            <span>
              Atualizado {new Date(activeArtifact.updatedAt).toLocaleString('pt-BR')}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
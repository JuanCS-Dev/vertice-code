'use client';

import { useActiveArtifact, useArtifactsStore } from '@/lib/stores/artifacts-store';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Save,
  Download,
  Copy,
  Search,
  Replace,
  Undo,
  Redo,
  Settings,
  Eye,
  Code2,
  Columns2,
  Terminal as TerminalIcon
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { EjectToCloud } from './cloud/eject-to-cloud'; // PROJECT VIVID Phase 3
import { useState } from 'react';

export type PreviewMode = 'editor' | 'preview' | 'split';

export interface ArtifactToolbarProps {
  showTerminal?: boolean;
  onToggleTerminal?: () => void;
}

export function ArtifactToolbar({
  showTerminal = false,
  onToggleTerminal
}: ArtifactToolbarProps = {}) {
  const activeArtifact = useActiveArtifact();
  const { saveArtifact, exportArtifact, setPreviewMode, previewMode, artifacts } = useArtifactsStore();
  const { toast } = useToast();

  if (!activeArtifact) return null;

  // Determine if preview is available for this file type
  const canPreview = activeArtifact.language && [
    'jsx', 'tsx', 'javascript', 'typescript', 'html', 'react'
  ].includes(activeArtifact.language);

  const handleSave = async () => {
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
    }
  };

  const handleExport = () => {
    exportArtifact(activeArtifact.id);
    toast({
      title: "Exportado!",
      description: `"${activeArtifact.name}" foi baixado.`,
    });
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(activeArtifact.content || '');
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

  const handleSearch = () => {
    // Search functionality will be implemented in Phase 9
    toast({
      title: "Em breve",
      description: "Funcionalidade de busca será implementada.",
    });
  };

  const handleReplace = () => {
    // Replace functionality will be implemented in Phase 9
    toast({
      title: "Em breve",
      description: "Funcionalidade de substituição será implementada.",
    });
  };

  return (
    <div className="flex items-center gap-1 p-2 border-b bg-background">
      {/* File Actions */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSave}
          disabled={!activeArtifact.isModified}
          className="h-8 px-2"
        >
          <Save className="h-4 w-4 mr-1" />
          Salvar
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          className="h-8 px-2"
        >
          <Download className="h-4 w-4 mr-1" />
          Exportar
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-8 px-2"
        >
          <Copy className="h-4 w-4 mr-1" />
          Copiar
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Edit Actions */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSearch}
          className="h-8 w-8 p-0"
          title="Buscar (Ctrl+F)"
        >
          <Search className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleReplace}
          className="h-8 w-8 p-0"
          title="Substituir (Ctrl+H)"
        >
          <Replace className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Desfazer (Ctrl+Z)"
          disabled={!activeArtifact.isModified}
        >
          <Undo className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Refazer (Ctrl+Y)"
        >
          <Redo className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Preview Mode Toggle - PROJECT VIVID */}
      {canPreview && (
        <>
          <div className="flex items-center gap-1">
            <Button
              variant={previewMode === 'editor' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setPreviewMode('editor')}
              className="h-8 px-2"
              title="Editor Only (Ctrl+1)"
            >
              <Code2 className="h-4 w-4 mr-1" />
              Editor
            </Button>

            <Button
              variant={previewMode === 'split' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setPreviewMode('split')}
              className="h-8 px-2"
              title="Split View (Ctrl+2)"
            >
              <Columns2 className="h-4 w-4 mr-1" />
              Split
            </Button>

            <Button
              variant={previewMode === 'preview' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setPreviewMode('preview')}
              className="h-8 px-2"
              title="Preview Only (Ctrl+3)"
            >
              <Eye className="h-4 w-4 mr-1" />
              Preview
            </Button>
          </div>

          <Separator orientation="vertical" className="h-6" />
        </>
      )}

      {/* Cloud Actions - PROJECT VIVID Phase 3 */}
      <div className="flex items-center gap-2 ml-auto">
        {/* Eject to Cloud */}
        <EjectToCloud
          files={Object.fromEntries(
            Object.values(artifacts)
              .filter(a => a.type === 'file')
              .map(a => [a.name, a.content || ''])
          )}
          projectName={activeArtifact.name.split('.')[0]}
          onEject={(success) => {
            toast({
              title: success ? 'Ejected!' : 'Failed',
              description: success
                ? 'Files synced to cloud successfully'
                : 'Failed to sync files to cloud',
              variant: success ? 'default' : 'destructive'
            });
          }}
        />

        <Separator orientation="vertical" className="h-6" />

        {/* Terminal Toggle */}
        {onToggleTerminal && (
          <Button
            variant={showTerminal ? 'default' : 'ghost'}
            size="sm"
            onClick={onToggleTerminal}
            className="h-8 px-2"
            title="Toggle Terminal (Ctrl+`)"
          >
            <TerminalIcon className="h-4 w-4 mr-1" />
            Terminal
          </Button>
        )}

        <Separator orientation="vertical" className="h-6" />

        {/* Settings */}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Configurações do editor"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
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
  Settings
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export function ArtifactToolbar() {
  const activeArtifact = useActiveArtifact();
  const { saveArtifact, exportArtifact } = useArtifactsStore();
  const { toast } = useToast();

  if (!activeArtifact) return null;

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
    // TODO: Implement search functionality
    toast({
      title: "Em breve",
      description: "Funcionalidade de busca será implementada.",
    });
  };

  const handleReplace = () => {
    // TODO: Implement replace functionality
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

      {/* Settings */}
      <div className="flex items-center gap-1 ml-auto">
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
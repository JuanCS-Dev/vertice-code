'use client';

import { useState, useEffect } from 'react';
import { useArtifactsStore, useActiveArtifact } from '@/lib/stores/artifacts-store';
import { ArtifactTree } from './artifact-tree';
import { ArtifactEditor } from './artifact-editor';
import { ArtifactToolbar } from './artifact-toolbar';
import { Button } from '@/components/ui/button';
import { Plus, File, Folder, Upload } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function ArtifactsPanel() {
  const {
    createArtifact,
    loadArtifactFromFile,
    artifacts,
    rootArtifactIds
  } = useArtifactsStore();

  const activeArtifact = useActiveArtifact();
  const [showTree, setShowTree] = useState(true);

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await loadArtifactFromFile(file);
      const artifactId = createArtifact(file.name, 'file');
      useArtifactsStore.getState().updateArtifact(artifactId, {
        content,
        language: file.name.split('.').pop(),
      });
    } catch (error) {
      console.error('Failed to load file:', error);
    }

    // Reset input
    event.target.value = '';
  };

  // Create new file/folder
  const handleCreateFile = () => {
    createArtifact('untitled.txt', 'file');
  };

  const handleCreateFolder = () => {
    createArtifact('new-folder', 'folder');
  };

  const hasArtifacts = Object.keys(artifacts).length > 0;

  return (
    <div className="flex h-full bg-background border rounded-lg overflow-hidden">
      {/* Left Sidebar - Artifact Tree */}
      <div className={cn(
        "border-r bg-muted/10 transition-all duration-200",
        showTree ? "w-80" : "w-0 overflow-hidden"
      )}>
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">Artifacts</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTree(!showTree)}
              className="text-muted-foreground"
            >
              {showTree ? '◁' : '▷'}
            </Button>
          </div>

          {showTree && (
            <div className="space-y-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Plus className="h-4 w-4 mr-2" />
                    New
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem onClick={handleCreateFile}>
                    <File className="h-4 w-4 mr-2" />
                    File
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleCreateFolder}>
                    <Folder className="h-4 w-4 mr-2" />
                    Folder
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <div className="relative">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  multiple={false}
                />
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload
                </Button>
              </div>
            </div>
          )}
        </div>

        {showTree && (
          <div className="flex-1 overflow-hidden">
            {hasArtifacts ? (
              <ArtifactTree />
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-8 text-center text-muted-foreground">
                <File className="h-12 w-12 mb-4 opacity-50" />
                <p className="text-sm mb-2">No artifacts yet</p>
                <p className="text-xs">Create a file or upload one to get started</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {activeArtifact ? (
          <>
            <ArtifactToolbar />
            <div className="flex-1 overflow-hidden">
              <ArtifactEditor />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <File className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <h3 className="text-lg font-medium mb-2">No file selected</h3>
              <p className="text-sm">
                Select an artifact from the sidebar or create a new one
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
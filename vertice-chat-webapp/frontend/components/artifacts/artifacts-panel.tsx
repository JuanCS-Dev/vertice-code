'use client';

import { useState, useEffect } from 'react';
import { useArtifactsStore, useActiveArtifact } from '@/lib/stores/artifacts-store';
import { ArtifactTree } from './artifact-tree';
import { ArtifactEditor } from './artifact-editor';
import { ArtifactToolbar } from './artifact-toolbar';
import { SandpackClient, useDebouncedSync } from './preview/sandpack-client';
import { Terminal } from './cloud/terminal';
import { Button } from '@/components/ui/button';
import { Plus, File, Folder, Upload, Columns, ChevronLeft, ChevronRight } from 'lucide-react';
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
    previewMode
  } = useArtifactsStore();

  const activeArtifact = useActiveArtifact();
  const [showTree, setShowTree] = useState(true);
  const [showTerminal, setShowTerminal] = useState(false);

  // Debounced content for Sandpack sync
  const debouncedContent = useDebouncedSync(activeArtifact?.content || '', 500);

  // Determine if current file can be previewed
  const canPreview = activeArtifact && activeArtifact.language && [
    'jsx', 'tsx', 'javascript', 'typescript', 'html', 'react'
  ].includes(activeArtifact.language);

  // Keyboard shortcut for terminal (Ctrl+`)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault();
        setShowTerminal(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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

  const handleCreateFile = () => createArtifact('untitled.txt', 'file');
  const handleCreateFolder = () => createArtifact('new-folder', 'folder');

  const hasArtifacts = Object.keys(artifacts).length > 0;

  return (
    <div className="flex h-full bg-[#050505] border border-white/5 rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
      {/* Left Sidebar - Artifact Tree */}
      <div className={cn(
        "border-r border-white/5 bg-[#080808]/50 backdrop-blur-md transition-all duration-300 relative",
        showTree ? "w-72" : "w-0 overflow-hidden"
      )}>
        <div className="p-5 border-b border-white/5 bg-[#0A0A0A]/50">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(212,255,0,0.5)]"></div>
              <h3 className="font-bold text-[10px] uppercase tracking-[0.3em] text-zinc-500">Project Nodes</h3>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowTree(!showTree)}
              className="h-6 w-6 p-0 hover:bg-white/5 text-zinc-600"
            >
              {showTree ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          </div>

          {showTree && (
            <div className="grid grid-cols-2 gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="w-full justify-start h-9 border-white/5 bg-white/[0.02] text-xs font-mono">
                    <Plus className="h-3.5 w-3.3 mr-2 text-primary" />
                    New
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="bg-[#0A0A0A] border-white/10 text-zinc-400">
                  <DropdownMenuItem onClick={handleCreateFile} className="hover:bg-primary hover:text-black">
                    <File className="h-4 w-4 mr-2" />
                    File
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleCreateFolder} className="hover:bg-primary hover:text-black">
                    <Folder className="h-4 w-4 mr-2" />
                    Folder
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <div className="relative">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  multiple={false}
                />
                <Button variant="outline" size="sm" className="w-full justify-start h-9 border-white/5 bg-white/[0.02] text-xs font-mono">
                  <Upload className="h-3.5 w-3.5 mr-2 text-primary" />
                  Import
                </Button>
              </div>
            </div>
          )}
        </div>

        {showTree && (
          <div className="flex-1 overflow-y-auto scrollbar-thin h-[calc(100%-8rem)]">
            {hasArtifacts ? (
              <ArtifactTree />
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                <File className="h-10 w-10 mb-4 text-zinc-800" />
                <p className="text-[10px] uppercase tracking-widest font-bold text-zinc-600">No artifacts found</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toggle Tab for Tree when closed */}
      {!showTree && (
        <button 
            onClick={() => setShowTree(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 w-4 h-12 bg-white/5 border border-white/5 border-l-0 rounded-r-md flex items-center justify-center hover:bg-white/10 transition-colors z-20"
        >
            <ChevronRight className="h-3 w-3 text-zinc-600" />
        </button>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative bg-[#050505]">
        {activeArtifact ? (
          <>
            <ArtifactToolbar
              showTerminal={showTerminal}
              onToggleTerminal={() => setShowTerminal(!showTerminal)}
            />

            <div className="flex-1 flex flex-col overflow-hidden">
              <div className={cn(
                "flex transition-all duration-300",
                showTerminal ? 'flex-1' : 'h-full'
              )}>
                {/* Editor */}
                {(previewMode === 'editor' || previewMode === 'split') && (
                  <div className={cn(
                    "overflow-hidden transition-all duration-300 border-r border-white/5",
                    previewMode === 'split' ? 'w-1/2' : 'w-full'
                  )}>
                    <ArtifactEditor />
                  </div>
                )}

                {/* Preview */}
                {canPreview && (previewMode === 'preview' || previewMode === 'split') && (
                  <div className={cn(
                    "overflow-hidden transition-all duration-300 bg-black",
                    previewMode === 'split' ? 'w-1/2' : 'w-full'
                  )}>
                    <div className="h-full p-6">
                      <div className="h-full border border-white/5 rounded-xl overflow-hidden shadow-2xl bg-[#080808]">
                        <SandpackClient
                          files={{
                            [`/App.${activeArtifact.language}`]: debouncedContent
                          }}
                          template={activeArtifact.language === 'tsx' ? 'react-ts' : 'react'}
                          showEditor={false}
                          showPreview={true}
                          autorun={true}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Terminal */}
              {showTerminal && (
                <div className="h-72 border-t border-white/5 bg-black">
                  <Terminal
                    onCommand={(cmd) => console.log('Command:', cmd)}
                    autoConnect={true}
                  />
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in duration-1000">
            <div className="relative mb-6">
                <div className="absolute inset-0 bg-primary/10 rounded-full blur-2xl animate-pulse"></div>
                <File className="h-16 w-16 text-zinc-800 relative z-10" />
            </div>
            <h3 className="text-sm font-bold uppercase tracking-[0.3em] text-zinc-600">Observation Deck</h3>
            <p className="text-xs text-zinc-700 mt-2 font-mono">Select a Project Node to begin manifestation.</p>
          </div>
        )}
      </div>
    </div>
  );
}

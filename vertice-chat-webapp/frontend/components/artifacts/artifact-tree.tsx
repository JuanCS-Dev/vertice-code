'use client';

import { useArtifactsStore, useArtifactTree } from '@/lib/stores/artifacts-store';
import { Artifact } from '@/lib/stores/artifacts-store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  File,
  Folder,
  FolderOpen,
  MoreHorizontal,
  Trash2,
  Download,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ArtifactTreeItemProps {
  artifact: Artifact;
  level: number;
}

function ArtifactTreeItem({ artifact, level }: ArtifactTreeItemProps) {
  const {
    activeArtifactId,
    expandedFolders,
    setActiveArtifact,
    toggleFolder,
    deleteArtifact,
    exportArtifact,
    getArtifactChildren,
  } = useArtifactsStore();

  const isActive = activeArtifactId === artifact.id;
  const isExpanded = expandedFolders.has(artifact.id);
  const children = getArtifactChildren(artifact.id);
  const hasChildren = artifact.type === 'folder' && children.length > 0;

  const handleClick = () => {
    if (artifact.type === 'folder') {
      toggleFolder(artifact.id);
    } else {
      setActiveArtifact(artifact.id);
    }
  };

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-3 cursor-pointer group transition-colors",
          isActive
            ? "bg-white/[0.05] text-white"
            : "hover:bg-white/[0.03] text-zinc-500 hover:text-zinc-300"
        )}
        style={{ paddingLeft: `${level * 12 + 12}px` }}
        onClick={handleClick}
      >
        {/* Toggle Arrow */}
        <div className="w-4 h-4 flex items-center justify-center">
            {artifact.type === 'folder' && (
                isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />
            )}
        </div>

        {/* Icon */}
        <div className="flex-shrink-0">
          {artifact.type === 'folder' ? (
            <Folder className={cn(
                "h-3.5 w-3.5",
                isExpanded ? "text-primary" : "text-zinc-600"
            )} />
          ) : (
            <File className={cn(
                "h-3.5 w-3.5",
                isActive ? "text-primary" : "text-zinc-700"
            )} />
          )}
        </div>

        {/* Name */}
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-xs font-mono truncate tracking-tight",
            isActive && "font-bold"
          )}>
            {artifact.name}
          </p>
        </div>

        {/* Actions */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-5 w-5 p-0 hover:bg-white/10">
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-[#0A0A0A] border-white/10 text-zinc-400">
              <DropdownMenuItem onClick={() => exportArtifact(artifact.id)} className="text-xs hover:bg-primary hover:text-black">
                <Download className="h-3.5 w-3.5 mr-2" /> Export
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => deleteArtifact(artifact.id)}
                className="text-xs text-red-500 hover:bg-red-500 hover:text-white"
              >
                <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Children */}
      {artifact.type === 'folder' && isExpanded && (
        <div className="animate-in fade-in slide-in-from-top-1 duration-200">
          {children.map((child) => (
            <ArtifactTreeItem
              key={child.id}
              artifact={child}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function ArtifactTree() {
  const artifactTree = useArtifactTree();

  return (
    <div className="py-2">
        {artifactTree.map((artifact) => (
            <ArtifactTreeItem
            key={artifact.id}
            artifact={artifact}
            level={0}
            />
        ))}
    </div>
  );
}

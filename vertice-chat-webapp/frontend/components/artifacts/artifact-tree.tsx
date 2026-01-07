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
  Edit,
  Trash2,
  Download
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
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
    selectedArtifactIds,
    setActiveArtifact,
    toggleFolder,
    deleteArtifact,
    exportArtifact,
    getArtifactChildren,
  } = useArtifactsStore();

  const isActive = activeArtifactId === artifact.id;
  const isSelected = selectedArtifactIds.has(artifact.id);
  const isExpanded = expandedFolders.has(artifact.id);
  const hasChildren = artifact.type === 'folder' && getArtifactChildren(artifact.id).length > 0;

  const handleClick = () => {
    if (artifact.type === 'folder') {
      toggleFolder(artifact.id);
    } else {
      setActiveArtifact(artifact.id);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Delete "${artifact.name}"?`)) {
      deleteArtifact(artifact.id);
    }
  };

  const handleExport = (e: React.MouseEvent) => {
    e.stopPropagation();
    exportArtifact(artifact.id);
  };

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2 hover:bg-accent cursor-pointer group",
          isActive && "bg-accent",
          isSelected && "ring-2 ring-primary ring-offset-1",
          "select-none"
        )}
        style={{ paddingLeft: `${level * 16 + 12}px` }}
        onClick={handleClick}
      >
        {/* Icon */}
        <div className="flex-shrink-0">
          {artifact.type === 'folder' ? (
            isExpanded ? (
              <FolderOpen className="h-4 w-4 text-blue-500" />
            ) : (
              <Folder className="h-4 w-4 text-blue-500" />
            )
          ) : (
            <File className="h-4 w-4 text-muted-foreground" />
          )}
        </div>

        {/* Name */}
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-sm truncate",
            isActive && "font-medium",
            artifact.isModified && "text-orange-600"
          )}>
            {artifact.name}
            {artifact.isModified && <span className="ml-1 text-xs">•</span>}
          </p>
        </div>

        {/* Modified indicator */}
        {artifact.isModified && (
          <div className="w-2 h-2 bg-orange-500 rounded-full flex-shrink-0" />
        )}

        {/* Actions */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {artifact.type === 'file' && (
                <DropdownMenuItem onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-red-600"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Children */}
      {artifact.type === 'folder' && isExpanded && (
        <div>
          {getArtifactChildren(artifact.id).map((child) => (
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
    <ScrollArea className="h-full">
      <div className="py-2">
        {artifactTree.map((artifact) => (
          <ArtifactTreeItem
            key={artifact.id}
            artifact={artifact}
            level={0}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
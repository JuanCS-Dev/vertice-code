"use client";

import React from "react";
import { useArtifactStore } from "@/lib/stores/artifact-store";
import { Download, X, FileCode, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

export function ArtifactHeader() {
  const { activeFileId, closeFile, files } = useArtifactStore();

  if (!activeFileId) return null;

  // Truth: Files are currently in-memory only until backend persistence is connected
  const isInMemory = true;

  return (
    <div className="h-10 border-b border-border flex items-center px-0 bg-background select-none">
       {/* Active Tab */}
       <div className="h-full px-4 border-r border-border bg-muted/5 flex items-center gap-2 min-w-[150px] relative group">
          <FileCode className="w-3.5 h-3.5 text-accent" />
          <span className="text-xs font-mono text-foreground font-medium truncate max-w-[120px]">
            {activeFileId}
          </span>

          {/* Close Button (Hover) */}
          <button
            onClick={(e) => { e.stopPropagation(); closeFile(activeFileId); }}
            className="absolute right-2 opacity-0 group-hover:opacity-100 p-0.5 hover:bg-white/10 rounded text-muted-foreground hover:text-foreground transition-all"
          >
            <X className="w-3 h-3" />
          </button>

          {/* Active Indicator Bar */}
          <div className="absolute top-0 left-0 w-full h-[2px] bg-accent" />
       </div>

       {/* Toolbar Spacer */}
       <div className="flex-1" />

       {/* Toolbar Actions */}
       <div className="flex items-center gap-1 px-2">
         <div className="flex items-center gap-1.5 px-3 py-1 text-[10px] text-muted-foreground mr-2 border border-dashed border-muted-foreground/30 rounded">
           {isInMemory && (
             <>
               <Cpu className="w-3 h-3 text-amber-500" />
               <span className="text-amber-500/80">Memory Only</span>
             </>
           )}
         </div>

         <button className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded transition-colors" title="Download Code">
           <Download className="w-3.5 h-3.5" />
         </button>
       </div>
    </div>
  );
}

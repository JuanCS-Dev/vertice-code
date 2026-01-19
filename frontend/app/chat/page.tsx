"use client";

import { Suspense } from "react";
import { WorkbenchShell } from "@/components/layout/workbench-shell";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup
} from "@/components/ui/resizable";
import { ChatSkeleton } from "@/components/chat/chat-skeleton";
import { ChatStream } from "@/components/chat/chat-stream";
import { ChatInput } from "@/components/chat/chat-input";
import { ArtifactEditor } from "@/components/artifacts/artifact-editor";
import { ArtifactHeader } from "@/components/artifacts/artifact-header";

export default function ChatPage() {
  return (
    <WorkbenchShell>
      <ResizablePanelGroup direction="horizontal" className="h-full items-stretch">

        {/* LEFT PANEL: Context / History */}
        <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="hidden md:block bg-muted/5 border-r border-border">
          <div className="h-full flex flex-col p-3">
            <h3 className="text-[10px] font-mono font-bold text-muted-foreground uppercase tracking-wider mb-3 px-2">
              Workspace
            </h3>
            <div className="space-y-1">
              <div className="px-3 py-2 rounded-md bg-accent/5 text-accent text-xs font-medium border border-accent/10 flex items-center gap-2 cursor-pointer">
                <span className="w-1 h-4 bg-accent rounded-full"></span>
                Active Session
              </div>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* CENTER PANEL: The Chat Stream + Input */}
        <ResizablePanel defaultSize={40} minSize={30} className="bg-background">
          <div className="h-full flex flex-col relative">
            <Suspense fallback={<ChatSkeleton />}>
               <div className="flex-1 overflow-y-auto scrollbar-thin pb-20">
                 <ChatStream />
               </div>
            </Suspense>

            {/* Input Area (Sticky Bottom) */}
            <div className="absolute bottom-0 w-full bg-gradient-to-t from-background via-background to-transparent pt-10 pb-4 z-20">
               <ChatInput />
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* RIGHT PANEL: Artifacts / Editor */}
        <ResizablePanel defaultSize={40} minSize={30} className="bg-background border-l border-border flex flex-col">
          <ArtifactHeader />
          <div className="flex-1 overflow-hidden relative">
             <ArtifactEditor />
          </div>
        </ResizablePanel>

      </ResizablePanelGroup>
    </WorkbenchShell>
  );
}

export const experimental_ppr = true;

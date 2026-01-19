"use client";

import * as React from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup
} from "@/components/ui/resizable"; // We need to scaffold these primitives too
import { AppSidebar } from "./app-sidebar";
import { cn } from "@/lib/utils";

interface WorkbenchProps {
  children: React.ReactNode;
  defaultLayout?: number[];
  navCollapsedSize?: number;
}

export function WorkbenchShell({
  children,
  defaultLayout = [20, 80],
}: WorkbenchProps) {
  // We can add state persistence here later to remember layout preferences

  return (
    <div className="h-screen w-full bg-background flex overflow-hidden">
      {/* Sidebar is fixed width for stability, but we could make it resizable too */}
      <AppSidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
         {/* Top Bar / Header would go here */}

         <div className="flex-1 h-full w-full">
            {children}
         </div>
      </main>
    </div>
  );
}

/**
 * Primitives for Resizable Panels (Wrapping react-resizable-panels)
 * Usually these live in components/ui/resizable.tsx but incl here for speed.
 */
import * as ResizablePrimitive from "react-resizable-panels";

const ResizablePanelGroup = ({
  className,
  ...props
}: React.ComponentProps<typeof ResizablePrimitive.PanelGroup>) => (
  <ResizablePrimitive.PanelGroup
    className={cn(
      "flex h-full w-full data-[panel-group-direction=vertical]:flex-col",
      className
    )}
    {...props}
  />
);

const ResizablePanel = ResizablePrimitive.Panel;

const ResizableHandle = ({
  withHandle,
  className,
  ...props
}: React.ComponentProps<typeof ResizablePrimitive.PanelResizeHandle> & {
  withHandle?: boolean;
}) => (
  <ResizablePrimitive.PanelResizeHandle
    className={cn(
      "relative flex w-px items-center justify-center bg-border transition-all hover:bg-primary/50 hover:w-1 group z-10",
      "data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:hover:h-1",
      className
    )}
    {...props}
  >
    {withHandle && (
      <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border transition-all group-hover:bg-primary group-hover:border-primary">
        <div className="h-2.5 w-0.5 bg-muted-foreground group-hover:bg-background" />
      </div>
    )}
  </ResizablePrimitive.PanelResizeHandle>
);

export { ResizablePanelGroup, ResizablePanel, ResizableHandle };

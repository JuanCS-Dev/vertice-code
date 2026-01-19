"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Layers,
  Github,
  Settings,
  Command,
  Activity,
  Box,
  TerminalSquare
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  match?: RegExp;
}

const mainNav: NavItem[] = [
  { icon: MessageSquare, label: "Chat", href: "/chat", match: /^\/chat/ },
  { icon: Layers, label: "Artifacts", href: "/artifacts" },
  { icon: Github, label: "Repositories", href: "/github" },
  { icon: TerminalSquare, label: "Console", href: "/console" },
];

const secondaryNav: NavItem[] = [
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="h-full w-[60px] md:w-[240px] flex flex-col bg-card border-r border-border transition-all duration-300 group">
      {/* Header / Logo Area */}
      <div className="h-14 flex items-center px-3 md:px-4 border-b border-border">
        <div className="flex items-center gap-3 text-accent">
          <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shadow-[0_0_15px_-3px_var(--accent)]">
            <Box className="w-5 h-5" />
          </div>
          <span className="font-bold tracking-tight hidden md:block text-foreground whitespace-nowrap opacity-0 md:opacity-100 transition-opacity duration-300">
            Vertice<span className="text-accent">.ai</span>
          </span>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 py-6 px-2 space-y-2 overflow-y-auto scrollbar-hide">
        <div className="mb-2 px-2 text-xs font-mono text-muted-foreground uppercase tracking-widest hidden md:block">
          Operations
        </div>
        {mainNav.map((item) => {
          const isActive = item.match
            ? item.match.test(pathname)
            : pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-200 relative overflow-hidden group/item",
                isActive
                  ? "bg-accent/10 text-accent shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              <item.icon className={cn("w-5 h-5 shrink-0", isActive && "animate-pulse-subtle")} />
              <span className="hidden md:block truncate">{item.label}</span>

              {/* Active Indicator Line */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent rounded-r-full shadow-[0_0_10px_var(--accent)]" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer / System Status */}
      <div className="p-2 border-t border-border mt-auto">
        <div className="mb-2 px-2 text-xs font-mono text-muted-foreground uppercase tracking-widest hidden md:block">
          System
        </div>

        {secondaryNav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <item.icon className="w-5 h-5 shrink-0" />
            <span className="hidden md:block">{item.label}</span>
          </Link>
        ))}

        {/* Status Badge */}
        <div className="mt-4 mx-1 p-2 rounded-lg bg-black/20 border border-white/5 flex items-center gap-3">
          <div className="relative flex h-2.5 w-2.5 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </div>
          <div className="hidden md:flex flex-col">
            <span className="text-[10px] font-mono font-bold text-emerald-500">OMNI-ROOT</span>
            <span className="text-[10px] text-muted-foreground leading-none">v2.5.0-beta</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

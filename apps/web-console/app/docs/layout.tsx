"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Code2,
  Cpu,
  FileText,
  Home,
  Layers,
  Menu,
  Rocket,
  Settings,
  Terminal,
  X,
  Zap,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  children?: NavItem[];
}

const navigation: NavItem[] = [
  {
    title: "Getting Started",
    href: "/docs",
    icon: <Rocket className="w-4 h-4" />,
    children: [
      { title: "Introduction", href: "/docs", icon: <Home className="w-4 h-4" /> },
      { title: "Installation", href: "/docs/installation", icon: <Terminal className="w-4 h-4" /> },
      { title: "Quick Start", href: "/docs/quickstart", icon: <Zap className="w-4 h-4" /> },
    ],
  },
  {
    title: "Core Concepts",
    href: "/docs/concepts",
    icon: <Layers className="w-4 h-4" />,
    children: [
      { title: "What is an Agent?", href: "/docs/concepts/agents", icon: <Cpu className="w-4 h-4" /> },
      { title: "Tools & MCP", href: "/docs/concepts/tools", icon: <Settings className="w-4 h-4" /> },
      { title: "Memory System", href: "/docs/concepts/memory", icon: <BookOpen className="w-4 h-4" /> },
    ],
  },
  {
    title: "SDK Reference",
    href: "/docs/sdk",
    icon: <Code2 className="w-4 h-4" />,
    children: [
      { title: "Python SDK", href: "/docs/sdk/python", icon: <FileText className="w-4 h-4" /> },
      { title: "API Reference", href: "/docs/sdk/api", icon: <FileText className="w-4 h-4" /> },
    ],
  },
  {
    title: "Tutorials",
    href: "/docs/tutorials",
    icon: <BookOpen className="w-4 h-4" />,
    children: [
      { title: "Build an Analyst Agent", href: "/docs/tutorials/analyst", icon: <FileText className="w-4 h-4" /> },
      { title: "Custom Tools", href: "/docs/tutorials/tools", icon: <FileText className="w-4 h-4" /> },
    ],
  },
];

function NavLink({ item, depth = 0 }: { item: NavItem; depth?: number }) {
  const pathname = usePathname();
  const isActive = pathname === item.href;
  const hasChildren = item.children && item.children.length > 0;
  const [isOpen, setIsOpen] = useState(
    hasChildren && item.children?.some((child) => pathname.startsWith(child.href))
  );

  return (
    <div>
      <Link
        href={item.href}
        className={`
          flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors
          ${depth > 0 ? "ml-4" : ""}
          ${isActive
            ? "bg-neon-cyan/10 text-neon-cyan font-medium"
            : "text-text-muted hover:text-text-main hover:bg-surface-card"
          }
        `}
        onClick={(e) => {
          if (hasChildren) {
            e.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
      >
        {item.icon}
        <span>{item.title}</span>
      </Link>
      {hasChildren && isOpen && (
        <div className="mt-1">
          {item.children?.map((child) => (
            <NavLink key={child.href} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-obsidian">
      {/* Mobile sidebar toggle */}
      <button
        className="fixed top-4 left-4 z-50 p-2 bg-surface-card rounded-lg border border-border-dim md:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? (
          <X className="w-5 h-5 text-text-main" />
        ) : (
          <Menu className="w-5 h-5 text-text-main" />
        )}
      </button>

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-40 w-64 h-full bg-surface-dark border-r border-border-dim
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0
        `}
      >
        {/* Logo */}
        <div className="p-4 border-b border-border-dim">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-neon-cyan to-neon-emerald rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-obsidian" />
            </div>
            <span className="text-lg font-display font-bold text-text-main">
              Vertice Docs
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2 overflow-y-auto h-[calc(100vh-80px)]">
          {navigation.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="md:ml-64 min-h-screen">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {children}
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

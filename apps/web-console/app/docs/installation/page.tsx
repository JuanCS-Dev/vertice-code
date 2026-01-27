import { CheckCircle2, Copy, Terminal } from "lucide-react";

export const metadata = {
  title: "Installation | Vertice Docs",
  description: "Install the Vertice SDK and get started building AI agents",
};

export default function InstallationPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-display font-bold text-text-main">
          Installation
        </h1>
        <p className="text-text-muted">
          Get started with Vertice by installing the Python SDK.
        </p>
      </div>

      {/* Requirements */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Requirements
        </h2>
        <ul className="space-y-2">
          {["Python 3.11+", "pip or poetry", "Google Cloud account (for Gemini 3)"].map((req) => (
            <li key={req} className="flex items-center gap-2 text-text-muted">
              <CheckCircle2 className="w-4 h-4 text-neon-emerald" />
              {req}
            </li>
          ))}
        </ul>
      </section>

      {/* Install via pip */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Install via pip
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-surface-card border-b border-border-dim">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-text-subtle" />
              <span className="text-xs text-text-subtle font-mono">terminal</span>
            </div>
            <button className="p-1 hover:bg-border-dim rounded transition-colors">
              <Copy className="w-4 h-4 text-text-subtle" />
            </button>
          </div>
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-neon-cyan font-mono">pip install vertice-mcp</code>
          </pre>
        </div>
      </section>

      {/* Environment Setup */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Environment Setup
        </h2>
        <p className="text-text-muted">
          Configure your API keys for Gemini 3 access:
        </p>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-surface-card border-b border-border-dim">
            <span className="text-xs text-text-subtle font-mono">.env</span>
          </div>
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`# Google Cloud / Gemini 3
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your-gemini-api-key

# Vertice MCP
VERTICE_MCP_ENDPOINT=https://mcp.vertice.ai
VERTICE_API_KEY=your-vertice-api-key`}
            </code>
          </pre>
        </div>
      </section>

      {/* Verify Installation */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Verify Installation
        </h2>
        <p className="text-text-muted">
          Test your installation by running:
        </p>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`python -c "from vertice_mcp import MCPClient; print('✓ Vertice installed')"`}
            </code>
          </pre>
        </div>
      </section>

      {/* Next Steps */}
      <div className="p-4 bg-surface-card border border-border-dim rounded-lg">
        <p className="text-text-muted">
          <span className="text-text-main font-medium">Next:</span>{" "}
          Follow the{" "}
          <a href="/docs/quickstart" className="text-neon-cyan hover:underline">
            Quick Start guide
          </a>{" "}
          to build your first agent.
        </p>
      </div>
    </div>
  );
}

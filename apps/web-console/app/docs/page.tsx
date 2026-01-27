import { BookOpen, Code2, Cpu, Rocket, Terminal, Zap } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "Documentation | Vertice",
  description: "Learn how to build AI agents with Vertice SDK and MCP",
};

const features = [
  {
    icon: <Cpu className="w-6 h-6" />,
    title: "Multi-Agent Architecture",
    description: "Build sophisticated AI systems with multiple specialized agents working together.",
  },
  {
    icon: <Code2 className="w-6 h-6" />,
    title: "Python SDK",
    description: "Simple, type-safe Python SDK for creating and deploying agents.",
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: "Gemini 3 Powered",
    description: "Native integration with Google's latest Gemini 3 Pro and Flash models.",
  },
  {
    icon: <BookOpen className="w-6 h-6" />,
    title: "1M Token Context",
    description: "Leverage massive context windows for complex reasoning tasks.",
  },
];

const quickLinks = [
  {
    title: "Installation",
    href: "/docs/installation",
    description: "Get started with pip install vertice-mcp",
    icon: <Terminal className="w-5 h-5" />,
  },
  {
    title: "Quick Start",
    href: "/docs/quickstart",
    description: "Build your first agent in 5 minutes",
    icon: <Rocket className="w-5 h-5" />,
  },
  {
    title: "API Reference",
    href: "/docs/sdk/api",
    description: "Complete API documentation",
    icon: <Code2 className="w-5 h-5" />,
  },
];

export default function DocsPage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <div className="space-y-4">
        <h1 className="text-4xl font-display font-bold text-text-main">
          Vertice Documentation
        </h1>
        <p className="text-lg text-text-muted max-w-2xl">
          Build production-ready AI agents with the Vertice platform.
          Powered by Gemini 3 and the Multi-Agent Collective Protocol (MCP).
        </p>
      </div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-3 gap-4">
        {quickLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group p-4 bg-surface-card border border-border-dim rounded-lg hover:border-neon-cyan/50 transition-all"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-neon-cyan/10 rounded-lg text-neon-cyan group-hover:bg-neon-cyan/20 transition-colors">
                {link.icon}
              </div>
              <h3 className="font-medium text-text-main group-hover:text-neon-cyan transition-colors">
                {link.title}
              </h3>
            </div>
            <p className="text-sm text-text-muted">{link.description}</p>
          </Link>
        ))}
      </div>

      {/* Features */}
      <div className="space-y-6">
        <h2 className="text-2xl font-display font-bold text-text-main">
          Why Vertice?
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature) => (
            <div key={feature.title} className="flex gap-4">
              <div className="flex-shrink-0 p-3 bg-surface-card border border-border-dim rounded-lg text-neon-cyan">
                {feature.icon}
              </div>
              <div>
                <h3 className="font-medium text-text-main mb-1">{feature.title}</h3>
                <p className="text-sm text-text-muted">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Code Example */}
      <div className="space-y-4">
        <h2 className="text-2xl font-display font-bold text-text-main">
          Quick Example
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-surface-card border-b border-border-dim">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
            <span className="ml-2 text-xs text-text-subtle font-mono">example.py</span>
          </div>
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`from vertice_mcp import MCPClient

# Initialize the MCP client
client = MCPClient(api_key="your-api-key")

# Create a simple task
response = client.submit_task(
    prompt="Analyze the Q4 sales data and identify trends",
    agent="analyst",
    tools=["data_query", "chart_generator"]
)

print(response.result)`}
            </code>
          </pre>
        </div>
      </div>

      {/* Next Steps */}
      <div className="p-6 bg-gradient-to-r from-neon-cyan/10 to-neon-emerald/10 border border-neon-cyan/20 rounded-lg">
        <h2 className="text-xl font-display font-bold text-text-main mb-2">
          Ready to get started?
        </h2>
        <p className="text-text-muted mb-4">
          Follow our installation guide to set up Vertice in your project.
        </p>
        <Link
          href="/docs/installation"
          className="inline-flex items-center gap-2 px-4 py-2 bg-neon-cyan text-obsidian font-medium rounded-lg hover:bg-neon-cyan-dim transition-colors"
        >
          <Terminal className="w-4 h-4" />
          Start Installation
        </Link>
      </div>
    </div>
  );
}

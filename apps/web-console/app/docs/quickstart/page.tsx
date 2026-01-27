import { ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "Quick Start | Vertice Docs",
  description: "Build your first AI agent with Vertice in 5 minutes",
};

export default function QuickStartPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-display font-bold text-text-main">
          Quick Start
        </h1>
        <p className="text-text-muted">
          Build and deploy your first AI agent in under 5 minutes.
        </p>
      </div>

      {/* Step 1 */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-neon-cyan/20 text-neon-cyan flex items-center justify-center font-bold">
            1
          </div>
          <h2 className="text-xl font-display font-semibold text-text-main">
            Initialize Client
          </h2>
        </div>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`from vertice_mcp import MCPClient

# Initialize with your API key

client = MCPClient(

    api_key="your-api-key",  # pragma: allowlist secret

    project_id="your-project-id",

)

`}
            </code>
          </pre>
        </div>
      </section>

      {/* Step 2 */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-neon-cyan/20 text-neon-cyan flex items-center justify-center font-bold">
            2
          </div>
          <h2 className="text-xl font-display font-semibold text-text-main">
            Submit a Task
          </h2>
        </div>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`# Submit a task to the Coder agent
response = client.submit_task(
    prompt="Create a Python function to calculate fibonacci numbers",
    agent="coder",
)

print(response.result)`}
            </code>
          </pre>
        </div>
      </section>

      {/* Step 3 */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-neon-cyan/20 text-neon-cyan flex items-center justify-center font-bold">
            3
          </div>
          <h2 className="text-xl font-display font-semibold text-text-main">
            Use Tools
          </h2>
        </div>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`# Use specific tools for the task
response = client.submit_task(
    prompt="Search for recent news about AI",
    agent="researcher",
    tools=["web_search", "summarize"],
)

for result in response.tool_results:
    print(f"Tool: {result.tool_name}")
    print(f"Output: {result.output}")`}
            </code>
          </pre>
        </div>
      </section>

      {/* Step 4 */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-neon-cyan/20 text-neon-cyan flex items-center justify-center font-bold">
            4
          </div>
          <h2 className="text-xl font-display font-semibold text-text-main">
            Stream Responses
          </h2>
        </div>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`# Stream responses for real-time output
async for chunk in client.stream_task(
    prompt="Write a detailed analysis of market trends",
    agent="analyst",
):
    print(chunk.text, end="", flush=True)`}
            </code>
          </pre>
        </div>
      </section>

      {/* Complete Example */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Complete Example
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-surface-card border-b border-border-dim">
            <span className="text-xs text-text-subtle font-mono">my_agent.py</span>
          </div>
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`import asyncio
from vertice_mcp import AsyncMCPClient

async def main():
    # Initialize async client
    client = AsyncMCPClient(api_key="your-api-key")

    # Get available skills from the collective
    skills = await client.get_skills()
    print(f"Available skills: {[s.name for s in skills]}")

    # Submit a complex task
    response = await client.submit_task(
        prompt="""
        Analyze the following code and suggest improvements:

        def fib(n):
            if n <= 1: return n
            return fib(n-1) + fib(n-2)
        """,
        agent="coder",
        context={"focus": "performance"},
    )

    print(response.result)

if __name__ == "__main__":
    asyncio.run(main())`}
            </code>
          </pre>
        </div>
      </section>

      {/* What's Next */}
      <div className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          What&apos;s Next?
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            {
              title: "Core Concepts",
              description: "Learn about agents, tools, and MCP",
              href: "/docs/concepts/agents",
            },
            {
              title: "Python SDK Reference",
              description: "Complete API documentation",
              href: "/docs/sdk/python",
            },
            {
              title: "Build an Analyst Agent",
              description: "Step-by-step tutorial",
              href: "/docs/tutorials/analyst",
            },
            {
              title: "Custom Tools",
              description: "Create your own tools",
              href: "/docs/tutorials/tools",
            },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group flex items-center justify-between p-4 bg-surface-card border border-border-dim rounded-lg hover:border-neon-cyan/50 transition-all"
            >
              <div>
                <h3 className="font-medium text-text-main group-hover:text-neon-cyan transition-colors">
                  {item.title}
                </h3>
                <p className="text-sm text-text-muted">{item.description}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-text-subtle group-hover:text-neon-cyan transition-colors" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

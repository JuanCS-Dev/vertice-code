import { Brain, Cpu, MessageSquare, Wrench } from "lucide-react";

export const metadata = {
  title: "What is an Agent? | Vertice Docs",
  description: "Understanding AI agents in the Vertice ecosystem",
};

export default function AgentsConceptPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-display font-bold text-text-main">
          What is an Agent?
        </h1>
        <p className="text-text-muted">
          An Agent is an autonomous AI system that can perceive, reason, and act to accomplish tasks.
        </p>
      </div>

      {/* Core Components */}
      <section className="space-y-6">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Core Components
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            {
              icon: <Brain className="w-6 h-6" />,
              title: "LLM Brain",
              description: "Gemini 3 Pro/Flash provides reasoning, planning, and natural language understanding.",
            },
            {
              icon: <Wrench className="w-6 h-6" />,
              title: "Tools",
              description: "Specialized capabilities like code execution, web search, and data analysis.",
            },
            {
              icon: <MessageSquare className="w-6 h-6" />,
              title: "Memory",
              description: "Hierarchical memory system (L1-L4) for context persistence across sessions.",
            },
            {
              icon: <Cpu className="w-6 h-6" />,
              title: "Metacognition",
              description: "Self-monitoring and improvement through reflection and learning.",
            },
          ].map((component) => (
            <div key={component.title} className="p-4 bg-surface-card border border-border-dim rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-neon-cyan/10 rounded-lg text-neon-cyan">
                  {component.icon}
                </div>
                <h3 className="font-medium text-text-main">{component.title}</h3>
              </div>
              <p className="text-sm text-text-muted">{component.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Available Agents */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Available Agents
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-dim">
                <th className="text-left py-3 px-4 text-text-main font-medium">Agent</th>
                <th className="text-left py-3 px-4 text-text-main font-medium">Specialty</th>
                <th className="text-left py-3 px-4 text-text-main font-medium">Model</th>
              </tr>
            </thead>
            <tbody className="text-text-muted">
              <tr className="border-b border-border-dim/50">
                <td className="py-3 px-4 font-mono text-neon-cyan">coder</td>
                <td className="py-3 px-4">Code generation, debugging, refactoring</td>
                <td className="py-3 px-4">Gemini 3 Pro</td>
              </tr>
              <tr className="border-b border-border-dim/50">
                <td className="py-3 px-4 font-mono text-neon-cyan">analyst</td>
                <td className="py-3 px-4">Data analysis, visualization, insights</td>
                <td className="py-3 px-4">Gemini 3 Pro</td>
              </tr>
              <tr className="border-b border-border-dim/50">
                <td className="py-3 px-4 font-mono text-neon-cyan">researcher</td>
                <td className="py-3 px-4">Web search, summarization, synthesis</td>
                <td className="py-3 px-4">Gemini 3 Flash</td>
              </tr>
              <tr className="border-b border-border-dim/50">
                <td className="py-3 px-4 font-mono text-neon-cyan">planner</td>
                <td className="py-3 px-4">Task decomposition, orchestration</td>
                <td className="py-3 px-4">Gemini 3 Pro</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-mono text-neon-emerald">nexus</td>
                <td className="py-3 px-4">Meta-agent: self-healing, evolution</td>
                <td className="py-3 px-4">Gemini 3 Pro</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Agent Lifecycle */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Agent Lifecycle
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg p-4">
          <pre className="text-sm text-text-muted font-mono">
{`┌─────────────────────────────────────────────────────────────┐
│                      AGENT LIFECYCLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. RECEIVE    ──▶  2. PLAN    ──▶  3. EXECUTE              │
│     Task            Decompose       Use Tools                │
│                     Strategy                                 │
│                                                              │
│  6. LEARN     ◀──  5. REFLECT  ◀──  4. RESPOND              │
│     Update          Analyze         Synthesize               │
│     Memory          Outcome         Result                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘`}
          </pre>
        </div>
      </section>
    </div>
  );
}

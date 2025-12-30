# VERTICE

```
██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
 ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
  ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝

       THE ULTIMATE AI CODE AGENCY
```

> **Enterprise-Grade Multi-Agent Code Intelligence**
>
> Combining the best patterns from Anthropic, Google, and OpenAI

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VERTICE AGENCY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌───────────────────────────────────────────────────────┐   │
│    │              ORCHESTRATOR (Claude)                     │   │
│    │         Strategic Planning - Task Decomposition        │   │
│    │              Context Preservation - QA                 │   │
│    └───────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│         ┌──────────────┼──────────────┐                        │
│         │              │              │                         │
│         v              v              v                         │
│    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐       │
│    │  CODER  │   │REVIEWER │   │ARCHITECT│   │RESEARCHER│      │
│    │  (Groq) │   │(Vertex) │   │(Claude) │   │ (Vertex) │      │
│    │   Fast  │   │   Sec   │   │   Des   │   │   Doc   │       │
│    └─────────┘   └─────────┘   └─────────┘   └─────────┘       │
│                                                                 │
│    ═══════════════════════════════════════════════════════     │
│                                                                 │
│    SKILLS          TOOLS           MEMORY          PROVIDERS   │
│    - code_gen      - git           - cortex        - groq      │
│    - code_review   - shell         - episodic      - vertex    │
│    - testing       - web           - procedural    - claude    │
│    - git_ops       - mcp           - working       - mistral   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Agent Orchestration
- **Hierarchical Pattern**: Lead agent delegates to specialists
- **Parallel Execution**: Independent tasks run simultaneously
- **Smart Handoffs**: Context preserved across agent transitions
- **Quality Gates**: Automatic review before completion

### Agent Roster

| Agent | Model | Specialty | Speed |
|-------|-------|-----------|-------|
| **Orchestrator** | Claude Opus | Strategic planning, coordination | - |
| **Coder** | Groq Llama 70B | Code generation, refactoring | 2,600 tok/s |
| **Reviewer** | Vertex Gemini | Security audit, code review | Fast |
| **Architect** | Claude Sonnet | System design, decisions | Deep |
| **Researcher** | Vertex Gemini | Documentation, web search | Fast |
| **DevOps** | Groq Llama | CI/CD, deployment | Fast |

### Free Tier Priority
Intelligent routing optimizes for cost:
1. **Groq** - 14,400 req/day FREE (primary)
2. **Cerebras** - 1M tokens/day FREE
3. **Vertex AI** - Enterprise quota
4. **Mistral** - 1B tokens/month FREE

### Skills System (Anthropic Pattern)
```
skills/
├── code_generation/
│   ├── SKILL.md          # Instructions
│   ├── scripts/          # Executable tools
│   ├── references/       # Context docs
│   └── assets/           # Templates
```

### Memory Architecture (MIRIX-inspired)
- **Working**: Active task context
- **Episodic**: Session history
- **Semantic**: Knowledge graph (LanceDB)
- **Procedural**: Learned patterns
- **Meta**: Self-reflection logs

## Quick Start

```bash
# Install
pip install -e .

# Run CLI
vertice chat

# Run TUI
vertice-tui

# Test providers
python test_vertice_providers.py
```

## Directory Structure

```
Vertice-Code/
├── .vertice/                # Agency configuration
│   ├── agents/              # Subagent definitions (Anthropic pattern)
│   ├── skills/              # Agency-level skills
│   ├── hooks/               # Event hooks
│   └── config.yaml          # Main configuration
│
├── agents/                  # Agent implementations
│   ├── orchestrator/        # Lead coordinator
│   ├── coder/               # Code generation
│   ├── reviewer/            # Code review
│   ├── architect/           # System design
│   ├── researcher/          # Documentation
│   └── devops/              # CI/CD
│
├── skills/                  # Shared skills library
│   ├── code_generation/     # SKILL.md + scripts/
│   ├── code_review/
│   ├── testing/
│   └── git_ops/
│
├── tools/                   # Tool implementations
│   ├── git/
│   ├── shell/
│   ├── web/
│   └── mcp/
│
├── memory/                  # Memory systems
│   ├── cortex/              # Semantic (LanceDB)
│   ├── episodic/            # Session logs
│   └── procedural/          # Learned patterns
│
├── providers/               # LLM providers
│   ├── groq.py              # FREE: 14,400 req/day
│   ├── vertex_ai.py         # Enterprise Gemini
│   ├── azure_openai.py      # Enterprise GPT-4
│   └── vertice_router.py    # Intelligent routing
│
├── cli/                     # CLI implementation
├── tui/                     # TUI implementation
└── tests/                   # Test suite
```

## Configuration

### .vertice/config.yaml

```yaml
agency:
  name: "Vertice"
  version: "2.0.0"

sovereignty:
  L0_AUTONOMOUS: [formatting, linting, tests]
  L1_CONSENSUS: [architecture, api_changes]
  L2_HUMAN_VETO: [deployment, security]
  L3_HUMAN_REQUIRED: [production, financial]

providers:
  priority_order: [groq, cerebras, vertex-ai, mistral]
```

## Research Foundation

Built on cutting-edge research from December 2025:

- [Anthropic Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) - Skills, subagents, hooks
- [Google ADK](https://google.github.io/adk-docs/) - Multi-agent patterns, tools ecosystem
- [OpenAI Agents SDK](https://openai.com/index/new-tools-for-building-agents/) - Handoffs, guardrails
- [Microsoft Azure AI Agents](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) - Orchestration patterns

## License

MIT - Built with intelligence by Vertice Agency

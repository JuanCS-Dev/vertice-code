# VERTICE

```
██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
 ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
  ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝

    Multi-LLM Agentic Framework with Constitutional AI
```

> **Enterprise-Grade AI Code Agency** | 20 Agents | 47 Tools | 7 LLM Providers | Constitutional Governance
>
> *December 2025 - Built with patterns from Anthropic, Google, OpenAI & Microsoft*

---

## Highlights

- **20 Specialized Agents** with semantic routing and confidence scoring
- **47 Tools** with MCP integration and safety sandboxing
- **7 LLM Providers** with FREE FIRST priority and automatic failover
- **Constitutional AI** governance (JUSTIÇA + SOFIA)
- **200K Token Context** with auto-compaction and thought signatures
- **PROMETHEUS** self-evolving meta-agent with 6-type memory
- **Premium TUI** at 60fps with real-time streaming
- **732+ Tests** covering unit, integration, and E2E scenarios

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VERTICE FRAMEWORK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    CONSTITUTIONAL GOVERNANCE                            │ │
│  │         JUSTIÇA (5 Principles)  +  SOFIA (7 Dimensions)                │ │
│  │                    TRIBUNAL Mode for High-Risk                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     VERTICE CLIENT (Multi-LLM Router)                   │ │
│  │  Groq → Cerebras → Mistral → OpenRouter → Gemini → Vertex AI → Azure   │ │
│  │              Circuit Breaker + Rate Limiting + Auto-Failover            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │              │
│         v                          v                          v              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐          │
│  │     CLI     │          │     TUI     │          │  PROMETHEUS │          │
│  │  14 Agents  │          │   60fps UI  │          │ Meta-Agent  │          │
│  │  vtc/vertice│          │  Streaming  │          │ Self-Evolve │          │
│  └─────────────┘          └─────────────┘          └─────────────┘          │
│         │                          │                          │              │
│         └──────────────────────────┼──────────────────────────┘             │
│                                    v                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         CORE FRAMEWORK                                  │ │
│  │   6 Core Agents  │  47 Tools  │  A2A Mesh  │  Context Manager          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Install in development mode
pip install -e .

# Run CLI interface
vtc                    # or: vertice-cli

# Run TUI interface
vertice                # Premium 60fps interface

# Check status
vtc status             # Show providers, agents, tools

# Run tests
pytest tests/ -v       # 732+ tests
```

---

## LLM Providers (FREE FIRST Priority)

VERTICE intelligently routes requests to minimize costs while maximizing availability:

| Priority | Provider | Tier | Daily Limit | Speed |
|----------|----------|------|-------------|-------|
| 1 | **Groq** | FREE | 14,400 requests | 2,600 tok/s |
| 2 | **Cerebras** | FREE | 1M tokens | Ultra-fast |
| 3 | **Mistral** | FREE | 1B tokens/month | Fast |
| 4 | **OpenRouter** | FREE | 200 requests | Variable |
| 5 | **Gemini** | API Key | Quota-based | Fast |
| 6 | **Vertex AI** | Enterprise | GCP Billing | Reliable |
| 7 | **Azure OpenAI** | Enterprise | Azure Billing | GPT-4 |

### Features
- **Circuit Breaker**: Automatic failover on provider failures
- **Rate Limiting**: Per-provider request tracking
- **Health Monitoring**: Real-time provider status
- **Dynamic Switching**: `/model groq` to switch providers

---

## 20 Specialized Agents

### CLI Agents (14)

| Agent | Specialty | Use Case |
|-------|-----------|----------|
| **Coder** | Code generation | Write new features |
| **Reviewer** | Code review | Security & quality audit |
| **Architect** | System design | Architecture decisions |
| **Researcher** | Documentation | Web search, docs |
| **Planner** | Task planning | Break down complex tasks |
| **Debugger** | Bug fixing | Trace and fix issues |
| **Refactor** | Code improvement | Clean and optimize |
| **Test** | Test generation | Unit, integration tests |
| **Docs** | Documentation | README, docstrings |
| **Git** | Version control | Commits, branches, PRs |
| **Security** | Security audit | Vulnerability detection |
| **DevOps** | CI/CD | Deployment, pipelines |
| **Explain** | Code explanation | Teaching, onboarding |
| **Mentor** | Best practices | Code review feedback |

### Core Agents (6)

| Agent | Model | Role |
|-------|-------|------|
| **Orchestrator** | Claude Opus | Strategic coordination |
| **Coder** | Groq Llama 70B | Fast code generation |
| **Reviewer** | Vertex Gemini | Security analysis |
| **Architect** | Claude Sonnet | System design |
| **Researcher** | Vertex Gemini | Documentation search |
| **DevOps** | Groq Llama | CI/CD operations |

### Semantic Routing
```
User Input → Embedding → Cosine Similarity → Top Agent (confidence > 0.7)
                                          → Fallback to Coder if uncertain
```

---

## 47 Tools System

### Categories

| Category | Tools | Examples |
|----------|-------|----------|
| **File Operations** | 12 | read, write, glob, grep, edit |
| **Bash Execution** | 8 | run, background, timeout, sandbox |
| **Git Integration** | 10 | status, commit, push, pr, diff |
| **Web Operations** | 6 | fetch, search, scrape |
| **MCP Integration** | 5 | connect, call, list, disconnect |
| **Code Analysis** | 6 | lint, format, complexity, deps |

### Safety Features
- **Sandboxing**: Dangerous commands require approval
- **Timeout Protection**: Max 10 minutes per command
- **Path Validation**: Prevent directory traversal
- **Secret Detection**: Block credential commits

---

## Constitutional AI Governance

### JUSTIÇA (5 Constitutional Principles)

1. **Beneficence** - Actions must benefit the user
2. **Non-maleficence** - Prevent harm
3. **Autonomy** - Respect user decisions
4. **Justice** - Fair and unbiased behavior
5. **Transparency** - Explain reasoning

### SOFIA (7 Ethical Dimensions)

1. **Safety** - Prevent dangerous actions
2. **Oversight** - Human-in-the-loop for critical ops
3. **Fairness** - Unbiased recommendations
4. **Interpretability** - Explainable decisions
5. **Accountability** - Audit trail
6. **Privacy** - Data protection
7. **Alignment** - User intent alignment

### Sovereignty Levels

| Level | Name | Examples | Approval |
|-------|------|----------|----------|
| L0 | AUTONOMOUS | Formatting, linting | None |
| L1 | CONSENSUS | Architecture changes | Agent consensus |
| L2 | HUMAN_VETO | Deployment, security | Human can veto |
| L3 | HUMAN_REQUIRED | Production, financial | Human must approve |

### TRIBUNAL Mode
For high-risk decisions, multiple agents deliberate:
```
TRIBUNAL activated → 3+ agents vote → Majority required → Human confirmation
```

---

## Context Management (200K Tokens)

### Features
- **Max Context**: 200,000 tokens (Claude 3 level)
- **Auto-Compaction**: Triggers at 80% usage
- **ObservationMasker**: Compresses tool outputs
- **SlidingWindowCompressor**: Smart context windowing
- **ThoughtSignatures**: Reasoning continuity across sessions

### Commands
| Command | Description |
|---------|-------------|
| `/compact` | Force context compression |
| `/context` | Show context breakdown |
| `/tokens` | Quick token count |
| `/add <file>` | Add file to context |
| `/context-clear` | Clear conversation history |

---

## PROMETHEUS Meta-Agent

Self-evolving system for continuous improvement:

### Agent0 Genome
```python
genome = {
    "reasoning_depth": 0.8,
    "creativity": 0.6,
    "precision": 0.9,
    "exploration": 0.4
}
```

### MIRIX 6-Type Memory

| Type | Purpose | Storage |
|------|---------|---------|
| **Working** | Active task context | In-memory |
| **Episodic** | Session history | SQLite |
| **Semantic** | Knowledge graph | LanceDB |
| **Procedural** | Learned patterns | JSON |
| **Strategic** | Long-term goals | YAML |
| **Meta** | Self-reflection logs | Markdown |

### Evolution Commands
```bash
/prometheus status    # Show system status
/prometheus evolve 5  # Run 5 evolution iterations
/prometheus memory    # Show memory status
/prometheus enable    # Enable self-evolution
```

---

## Premium TUI Interface

### Features
- **60fps Rendering** with Textual framework
- **Real-time Streaming** token-by-token display
- **Token Meter** with visual usage bar
- **Status Bar** with provider/agent/cost info
- **Premium Themes** (dark, light, cyberpunk)
- **Command Palette** with fuzzy search

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+L` | Clear screen |
| `Ctrl+P` | Command palette |
| `Tab` | Autocomplete |
| `Up/Down` | Command history |
| `Esc` | Close modal/cancel |

---

## A2A Protocol (Agent-to-Agent)

### Mesh Networking
- **Agent Discovery**: Automatic peer detection
- **Message Routing**: Efficient inter-agent communication
- **State Sync**: Distributed context sharing

### Three-Loop Learning
1. **Inner Loop**: Real-time response adaptation
2. **Middle Loop**: Session pattern learning
3. **Outer Loop**: Cross-session evolution

### Metacognition
- **Self-Monitoring**: Performance tracking
- **Strategy Selection**: Dynamic approach changes
- **Confidence Calibration**: Know when uncertain

---

## Directory Structure

```
Vertice-Code/
├── vertice_cli/          # CLI interface (primary)
│   ├── commands/         # Command implementations
│   ├── core/             # CLI core logic
│   └── __main__.py       # Entry point
│
├── vertice_tui/          # TUI interface (primary)
│   ├── app.py            # Main Textual app
│   ├── widgets/          # Custom widgets
│   │   ├── token_meter.py
│   │   ├── response_view.py
│   │   └── status_bar.py
│   ├── core/             # TUI core bridge
│   │   ├── bridge.py     # LLM/Agent/Tool integration
│   │   └── formatting/   # Rich output formatting
│   └── handlers/         # Command handlers
│
├── vertice_core/         # Domain kernel
│   ├── types.py          # Core type definitions
│   ├── protocols.py      # Abstract interfaces
│   └── config.py         # Configuration
│
├── core/                 # Framework foundation
│   ├── mesh/             # A2A mesh networking
│   ├── a2a/              # Agent-to-agent protocol
│   ├── metacognition/    # Self-monitoring
│   └── context/          # Context management
│
├── agents/               # Agent implementations
│   ├── orchestrator/     # Lead coordinator
│   ├── coder/            # Code generation
│   ├── reviewer/         # Code review
│   ├── architect/        # System design
│   ├── researcher/       # Documentation
│   └── devops/           # CI/CD
│
├── prometheus/           # Meta-agent framework
│   ├── agent0.py         # Genome-based agent
│   ├── evolution.py      # Self-evolution logic
│   └── mirix_memory.py   # 6-type memory system
│
├── vertice_governance/   # Constitutional AI
│   ├── justica.py        # 5 principles
│   ├── sofia.py          # 7 dimensions
│   └── tribunal.py       # Multi-agent deliberation
│
├── clients/              # LLM provider clients
│   └── vertice_client.py # Unified multi-provider router
│
├── tools/                # Tool implementations
│   ├── file_ops/         # File operations
│   ├── bash/             # Shell execution
│   ├── git/              # Git integration
│   └── mcp/              # MCP integration
│
├── tests/                # Test suite (732+ tests)
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
│
└── docs/                 # Documentation
    ├── architecture/     # Design docs
    └── api/              # API reference
```

---

## Configuration

### Environment Variables

```bash
# Free providers (priority order)
export GROQ_API_KEY="gsk_..."
export CEREBRAS_API_KEY="..."
export MISTRAL_API_KEY="..."
export OPENROUTER_API_KEY="..."

# API Key providers
export GEMINI_API_KEY="..."

# Enterprise providers
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://..."
```

### .vertice/config.yaml

```yaml
agency:
  name: "Vertice"
  version: "2.0.0"

providers:
  priority_order: [groq, cerebras, mistral, openrouter, gemini, vertex-ai, azure]
  free_first: true
  circuit_breaker:
    failure_threshold: 3
    recovery_timeout: 60

governance:
  sovereignty:
    L0_AUTONOMOUS: [formatting, linting, tests]
    L1_CONSENSUS: [architecture, api_changes]
    L2_HUMAN_VETO: [deployment, security]
    L3_HUMAN_REQUIRED: [production, financial]

context:
  max_tokens: 200000
  compaction_threshold: 0.80
  sliding_window: true
```

---

## Development

### Running Tests

```bash
# All tests (732+)
pytest tests/ -v

# Specific categories
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/e2e/ -v            # E2E tests

# With coverage
pytest tests/ --cov=vertice_cli --cov=vertice_tui --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check vertice_cli/ vertice_tui/ vertice_core/

# Formatting
black vertice_cli/ vertice_tui/ vertice_core/

# Type checking
mypy vertice_cli/ vertice_tui/ vertice_core/
```

---

## Research Foundation

Built on cutting-edge research from December 2025:

| Source | Contribution |
|--------|--------------|
| [Anthropic Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) | Skills, subagents, hooks patterns |
| [Google ADK](https://google.github.io/adk-docs/) | Multi-agent orchestration, tools ecosystem |
| [OpenAI Agents SDK](https://openai.com/index/new-tools-for-building-agents/) | Handoffs, guardrails, structured outputs |
| [Microsoft Azure AI Agents](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) | Enterprise orchestration patterns |
| [MIRIX Memory](https://arxiv.org/abs/2312.00000) | 6-type memory architecture |
| [Constitutional AI](https://www.anthropic.com/research/constitutional-ai) | Governance principles |

---

## License

MIT License - Built with intelligence by VERTICE Framework

---

*Soli Deo Gloria* | December 2025

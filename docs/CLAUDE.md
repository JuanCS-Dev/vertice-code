# CLAUDE.md - VERTICE Project Configuration

## Project Overview

VERTICE is a multi-LLM agentic framework with unified context management and Constitutional AI governance.

**Entry Points:**
- `vtc` / `vertice-cli` - CLI interface
- `vertice` - TUI interface

## Core Architecture

```
vertice_cli/         # CLI interface (primary)
vertice_tui/         # TUI interface (primary)
vertice_core/        # Domain kernel (types, protocols)
core/                # Framework foundation (mesh, A2A, metacognition)
agents/              # Multi-agent system (6 specialized agents)
prometheus/          # Meta-agent framework
vertice_governance/  # Constitutional AI governance
```

## Supported LLM Providers

- **Claude** (Anthropic) - Primary
- **Gemini** (Google) - Secondary
- **Qwen** (Alibaba) - Via Azure/Groq
- **Groq** - Fast inference
- **Mistral** - European alternative
- **OpenAI** (GPT-4) - Via Azure

## Development Setup

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v

# Check code quality
ruff check vertice_cli/ vertice_tui/ vertice_core/
black --check vertice_cli/ vertice_tui/ vertice_core/
```

## Context Management

- **Max tokens:** 200,000 (Claude 3)
- **Auto-compact threshold:** 64%
- **ObservationMasker:** Tool output compression
- **SlidingWindowCompressor:** Context window management
- **ThoughtSignatures:** Reasoning continuity

## Commands

| Command | Description |
|---------|-------------|
| `/compact` | Compress context |
| `/context` | Show context breakdown |
| `/tokens` | Quick token count |
| `/add <file>` | Add file to context |

## Test Suite

- **732 tests** across unit, integration, and E2E
- Run with: `pytest tests/ -v`

## Important Directories

| Directory | Purpose | Tracked |
|-----------|---------|---------|
| `vertice_cli/` | CLI package | Yes |
| `vertice_tui/` | TUI package | Yes |
| `vertice_core/` | Domain kernel | Yes |
| `core/` | Framework | Yes |
| `.archive/` | Legacy code | No |
| `.claude/` | Claude Code config | Partial |

## Coding Standards

- Python 3.11+
- Type hints required
- Docstrings for public APIs
- Max line length: 100 chars
- Async/await for I/O operations

## Git Workflow

- **main** - Production
- **develop** - Integration
- **feat/** - Features
- **fix/** - Bug fixes

---

*VERTICE Framework - December 2025*
*Soli Deo Gloria*

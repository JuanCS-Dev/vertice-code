# AGENTS.md - Jules Configuration for Vertice-Code

## Project Overview

**Vertice-Code** is a multi-LLM agentic framework with unified context management and Constitutional AI governance.

- **Language**: Python 3.11+
- **Framework**: Textual (TUI), Click (CLI)
- **LLM Providers**: Claude, Gemini, Groq, Mistral, OpenAI

## Entry Points

```bash
vtc          # CLI interface
vertice      # TUI interface (primary)
```

## Directory Structure

```
vertice_cli/         # CLI package
vertice_tui/         # TUI package (Textual-based)
vertice_core/        # Domain kernel (types, protocols)
prometheus/          # PROMETHEUS meta-agent framework
tests/               # Test suites
  e2e/               # End-to-end tests
  prometheus/        # PROMETHEUS validation tests
  edge_cases/        # Edge case tests
```

## Running Tests

### Quick Validation (5-10 min)
```bash
pytest tests/e2e/test_e2e_shell_integration.py -v --timeout=120
```

### Prometheus Validation (10-15 min)
```bash
python tests/prometheus/test_scientific_validation.py
```

### Full Suite (2+ hours)
```bash
pytest tests/e2e/ -v --timeout=900
```

## Environment Variables

Required for LLM tests:
- `GOOGLE_API_KEY` - For Gemini/Prometheus
- `GROQ_API_KEY` - For Groq provider
- `ANTHROPIC_API_KEY` - For Claude

## Code Quality

```bash
ruff check vertice_cli/ vertice_tui/ vertice_core/
black --check vertice_cli/ vertice_tui/ vertice_core/
```

## Key Files for Testing

| File | Purpose |
|------|---------|
| `tests/e2e/RUN_E2E_TESTS.md` | Test guide with commands |
| `tests/e2e/test_e2e_shell_integration.py` | Shell/NLU tests |
| `tests/prometheus/test_scientific_validation.py` | Prometheus validation |
| `vertice_tui/core/prometheus_client.py` | Prometheus TUI client |

## Conventions

- Type hints required for all public APIs
- Async/await for I/O operations
- Tests use pytest with pytest-asyncio
- Max line length: 100 chars

## Recent Changes (2026-01-04)

- Fixed `import asyncio` in prometheus/core/orchestrator.py
- Hardened PrometheusClient with error handling
- Updated TUI keybindings (Ctrl+P=Prometheus, Ctrl+H=Help)
- Version bumped to v0.9.0

---
*Last updated: 2026-01-04*

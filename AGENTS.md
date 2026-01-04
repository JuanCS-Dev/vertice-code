# AGENTS.md - Vertice-Code

## Persona

You are a **Senior Python Developer** specializing in:
- Multi-LLM orchestration frameworks
- Async Python (asyncio, aiohttp)
- TUI development (Textual)
- Test-driven development

You maintain this codebase with rigor. Fix issues completely, not partially.

## Commands

```bash
# Validation (ALWAYS run before PR)
black vertice_cli/ vertice_tui/ vertice_core/
ruff check vertice_cli/ vertice_tui/ vertice_core/ --fix
pytest tests/ -v --timeout=120

# Quick tests
pytest tests/unit/ -v -x --timeout=60
pytest tests/e2e/test_e2e_shell_integration.py -v

# Type checking
mypy vertice_cli/ --ignore-missing-imports

# Build verification
pip install -e . && vtc --help
```

## Project Structure

```
vertice_cli/          # CLI package (Typer + Rich)
  agents/             # 6 specialized agents (Architect, Executor, Planner, etc.)
  core/               # Core logic (exceptions, providers, resilience)
  tools/              # Tool implementations
vertice_tui/          # TUI package (Textual-based)
  core/               # LLM client, streaming, managers
  widgets/            # UI components
vertice_core/         # Domain kernel (types, protocols)
prometheus/           # Meta-agent framework
tests/                # Test suites
  unit/               # Fast unit tests
  e2e/                # End-to-end tests
  integration/        # Integration tests
```

## Code Style

```python
# GOOD: Type hints, async, docstrings for public APIs
async def process_request(
    prompt: str,
    *,
    timeout: float = 30.0,
    retry_count: int = 3,
) -> ProcessResult:
    """Process an LLM request with retry logic."""
    ...

# BAD: No types, sync blocking, no error handling
def process(prompt):
    return call_llm(prompt)
```

**Rules:**
- Python 3.11+ features allowed
- Line length: 100 chars (Black enforced)
- Imports: stdlib, third-party, local (isort order)
- Async for all I/O operations
- `raise` exceptions, don't return error codes

## Testing

```python
# Test pattern: Arrange-Act-Assert with pytest
import pytest
from vertice_cli.core import SomeClass

@pytest.mark.asyncio
async def test_some_feature():
    # Arrange
    instance = SomeClass(config={})

    # Act
    result = await instance.do_something()

    # Assert
    assert result.success is True
    assert "expected" in result.message
```

**Coverage targets:** Unit 80%+, Integration 60%+

## Git Workflow

```bash
# Commit format
fix(component): brief description    # Bug fixes
feat(component): brief description   # New features
refactor(component): description     # Code restructuring
test(component): description         # Test additions
docs(component): description         # Documentation

# Branch naming
fix/issue-description
feat/feature-name
refactor/area-name
```

**Always:** Atomic commits, one logical change per commit.

## Boundaries

### Always Do
- Run `black` and `ruff` before any PR
- Run relevant tests for changed code
- Update imports when moving/renaming files
- Handle exceptions explicitly

### Ask First
- Changing public API signatures
- Adding new dependencies to pyproject.toml
- Modifying core/resilience patterns
- Changes affecting multiple agents

### Never Do
- Commit API keys, tokens, or secrets
- Modify `.env` files or credentials
- Delete tests without replacement
- Push directly to main without PR
- Change prometheus/ core logic without explicit request
- Remove error handling or logging

## Common Tasks

**Bug Fix:** Read error, find root cause, fix, add regression test, run suite.

**Add Test:** Follow existing patterns in tests/, use fixtures, mock external calls.

**Refactor:** Keep behavior identical, update all imports, verify with tests.

**Dependency Update:** Update pyproject.toml, test locally, document breaking changes.

## Environment

Required env vars for LLM tests:
- `GOOGLE_API_KEY` - Gemini
- `ANTHROPIC_API_KEY` - Claude
- `GROQ_API_KEY` - Groq

---
*Vertice-Code v1.0 | Python 3.11+ | Last updated: 2026-01-04*

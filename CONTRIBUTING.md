# Contributing to VERTICE

Thank you for your interest in contributing to VERTICE! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before submitting a bug report:

1. Check the [existing issues](https://github.com/JuanCS-Dev/vertice-code/issues) to avoid duplicates
2. Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include as much detail as possible:
   - VERTICE version (`vtc --version`)
   - Python version (`python --version`)
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or error messages

### Suggesting Features

We welcome feature suggestions! Please:

1. Check [existing feature requests](https://github.com/JuanCS-Dev/vertice-code/issues?q=is%3Aissue+label%3Aenhancement)
2. Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
3. Describe the problem your feature would solve
4. Explain your proposed solution

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
3. **Make your changes** following our coding standards
4. **Write/update tests** as needed
5. **Run the test suite**:
   ```bash
   pytest tests/ -v
   ```
6. **Ensure code quality**:
   ```bash
   ruff check vertice_cli/ vertice_tui/ vertice_core/
   black --check vertice_cli/ vertice_tui/ vertice_core/
   ```
7. **Commit** with a descriptive message:
   ```bash
   git commit -m "feat: add new agent routing capability"
   ```
8. **Push** to your fork and submit a PR

## Development Setup

### Prerequisites

- Python 3.11+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/JuanCS-Dev/vertice-code.git
cd vertice-code

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=vertice_cli --cov=vertice_tui --cov-report=html

# Specific test file
pytest tests/unit/test_agents.py -v
```

## Coding Standards

### Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for all function signatures
- Write docstrings for public APIs

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add Groq provider support
fix: resolve context overflow in long sessions
docs: update README with new commands
```

### Branch Naming

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

## Project Structure

```
vertice_cli/         # CLI interface
vertice_tui/         # TUI interface
vertice_core/        # Domain kernel
core/                # Framework foundation
agents/              # Agent implementations
prometheus/          # Meta-agent framework
vertice_governance/  # Constitutional AI
tests/               # Test suite
```

## Areas for Contribution

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/JuanCS-Dev/vertice-code/labels/good%20first%20issue).

### High-Impact Areas

- **New LLM Providers**: Add support for additional providers
- **Agent Improvements**: Enhance agent capabilities
- **Documentation**: Improve guides and API docs
- **Testing**: Increase test coverage
- **Performance**: Optimize context management

## Review Process

1. All PRs require at least one review
2. CI checks must pass (tests, linting)
3. Documentation must be updated if needed
4. Breaking changes require discussion

## Getting Help

- Open an issue for questions
- Join discussions in existing issues
- Check the [documentation](docs/)

## Recognition

Contributors are recognized in:
- The project's release notes
- The contributors list

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make VERTICE better!

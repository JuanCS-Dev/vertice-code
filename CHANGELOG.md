# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - 2026-01-06
- **Documentation**: Major update to README.md reflecting January 2026 status.
  - Updated agent count to 20 (6 Core + 14 specialized stubs).
  - Updated tool count to 78 (including MCP and Prometheus integrations).
  - Documented massive test suite expansion to 9,024+ tests.
  - Added dedicated section for **Prometheus Meta-Agent (L4)**.
  - Refined LLM Provider routing strategy and Constitutional Governance (SOFIA/JUSTICA).
- **System**: Verified 100% parity across all core agents and provider registries.

### Changed - 2025-11-18
- **Major Project Reorganization**: Complete semantic directory restructuring
  - Moved all planning documents to `docs/planning/`
  - Moved all reports and summaries to `docs/reports/`
  - Moved all research documents to `docs/research/`
  - Moved all test files to `tests/`
  - Moved examples to `examples/`
  - Moved benchmarks to `benchmarks/`
  - Cleaned up root directory for better project navigation
- **Documentation**: Updated README.md with detailed project structure
- **Build**: Updated .gitignore to exclude temporary files and backups

### Project Structure
```
Root Directory (Clean)
├── qwen_dev_cli/      # Core application
├── tests/             # All test files
├── docs/              # All documentation
│   ├── planning/      # Planning documents
│   ├── reports/       # Status reports
│   └── research/      # Research docs
├── examples/          # Code examples
├── benchmarks/        # Performance tests
├── scripts/           # Utility scripts
└── Configuration files (pyproject.toml, requirements.txt, etc.)
```

## [0.1.0] - Previous Version

### Added
- Initial MCP integration with filesystem server
- LLM client with HuggingFace and Ollama support
- CLI interface with Typer
- Web interface with Gradio
- Shell command parser
- Terminal tools integration
- Workflow orchestration system
- Context management
- Comprehensive test suite
- Resilience and recovery mechanisms

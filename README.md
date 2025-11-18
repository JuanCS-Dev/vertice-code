# 🚀 QWEN-DEV-CLI

**AI-Powered Code Assistant with MCP Integration**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![Gradio](https://img.shields.io/badge/Gradio-6.0-orange.svg)](https://gradio.app/)

> A hybrid CLI + Web code assistant that leverages Model Context Protocol (MCP) for context-aware code explanations and generation. Privacy-first, mobile-friendly, and lightning fast.

📁 **[View Complete Project Structure](PROJECT_STRUCTURE.md)**

---

## ✨ Features

- 🚀 **Instant Responses** - HuggingFace Inference API for sub-2s latency
- 🔒 **Privacy-First** - Optional local Ollama mode for complete data privacy
- 📱 **Mobile Responsive** - Works seamlessly on any device (320px+)
- 🔧 **MCP Integration** - Filesystem server for context-aware assistance
- ⚡ **Real-time Streaming** - Progressive token display for better UX
- 🎯 **Dual Interface** - CLI for power users, Web UI for accessibility

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         QWEN-DEV-CLI                        │
├─────────────────────────────────────────────┤
│                                             │
│  CLI (Typer)         Web UI (Gradio 6)      │
│  ├─ explain          ├─ Chat interface     │
│  ├─ generate         ├─ Streaming          │
│  └─ serve            └─ Mobile responsive  │
│                                             │
├─────────────────────────────────────────────┤
│         Core Business Logic                 │
│  ├─ LLM Client (HF API + Ollama)           │
│  ├─ MCP Manager (Filesystem)               │
│  └─ Context Builder                        │
├─────────────────────────────────────────────┤
│         External Services                   │
│  ├─ HuggingFace Inference API              │
│  ├─ Ollama (Optional)                      │
│  └─ MCP Filesystem Server                  │
└─────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/JuanCS-Dev/qwen-dev-cli.git
cd qwen-dev-cli

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### CLI Mode

```bash
# Explain code
qwen-dev explain main.py

# Generate code
qwen-dev generate "Create a FastAPI endpoint for user authentication"

# Start web server
qwen-dev serve
```

#### Web UI Mode

```bash
# Start Gradio interface
python -m qwen_dev_cli

# Open browser at http://localhost:7860
```

---

## 🛠️ Technology Stack

- **Frontend**: Gradio 6.0+ (Blocks API)
- **Backend**: Python 3.11+
- **LLM Primary**: HuggingFace Inference API
- **LLM Optional**: Ollama + Qwen 2.5 Coder 7B
- **MCP**: Model Context Protocol 1.0
- **CLI**: Typer + Rich

---

## 📦 Project Structure

```
qwen-dev-cli/
├── qwen_dev_cli/           # Core application
│   ├── core/               # Business logic layer
│   │   ├── llm.py          # LLM client abstraction
│   │   ├── mcp.py          # MCP server integration
│   │   ├── context.py      # Context management
│   │   └── config.py       # Configuration handling
│   ├── integration/        # External integrations
│   │   ├── parser.py       # Shell command parsing
│   │   └── workflow.py     # Workflow orchestration
│   ├── tools/              # MCP tools implementation
│   │   ├── shell.py        # Shell execution tools
│   │   └── terminal.py     # Terminal utilities
│   ├── prompts/            # System prompts
│   ├── cli.py              # CLI interface (Typer)
│   ├── shell.py            # Interactive shell
│   └── ui.py               # Web interface (Gradio)
│
├── tests/                  # Comprehensive test suite
│   ├── test_*.py           # Unit & integration tests
│   ├── validate_*.py       # Validation scripts
│   └── __init__.py         # Test package
│
├── docs/                   # Documentation hub
│   ├── planning/           # Project planning docs
│   │   ├── MASTER_PLAN.md  # Master roadmap
│   │   └── DAILY_LOG.md    # Development journal
│   ├── reports/            # Status & audit reports
│   │   ├── VALIDATION_REPORT.md
│   │   ├── AUDIT_REPORT.md
│   │   └── *_SUMMARY.md    # Various summaries
│   └── research/           # Technical research
│       └── PHASE_*.md      # Phase-specific research
│
├── examples/               # Usage examples
│   └── example_parser_usage.py
│
├── benchmarks/             # Performance benchmarks
│   └── benchmark_llm.py
│
├── scripts/                # Utility scripts
│
├── pyproject.toml          # Project metadata (Poetry)
├── requirements.txt        # Python dependencies
└── pytest.ini              # Test configuration
```

---

## 🎯 MCP Integration

This project showcases Model Context Protocol integration through:

1. **Filesystem Server** - Direct file access for context injection
2. **Context Building** - Smart file selection and prompt construction
3. **Hybrid Approach** - CLI tools + Web interface working together
4. **Shell Tools** - Command execution and terminal integration
5. **Workflow Orchestration** - Multi-step task automation

### Key Features
- ✅ **Parser Integration** - Intelligent shell command parsing
- ✅ **Terminal Tools** - Safe command execution with validation
- ✅ **Context Management** - Advanced context window handling
- ✅ **LLM Resilience** - Automatic retry and fallback strategies
- ✅ **Workflow System** - Complex task orchestration

---

## 🚀 Deployment

### HuggingFace Spaces

This project is deployed on HuggingFace Spaces for instant access:

🔗 **[Live Demo](https://huggingface.co/spaces/JuanCS-Dev/qwen-dev-cli)** *(coming soon)*

---

## 📊 Performance

- **TTFT**: < 2s (Time to First Token)
- **Throughput**: 12-18 tokens/sec
- **Cold Start**: ~5s (HF API) / ~45s (Ollama)
- **Mobile Support**: 320px+ width
- **Test Coverage**: 90%+ across all modules
- **Resilience**: Automatic retry with exponential backoff

---

## 🤝 Contributing

This is a hackathon project for the **MCP 1st Birthday Hackathon** (Anthropic + Gradio).

Contributions welcome after the hackathon concludes!

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run specific test suite
pytest tests/test_parser.py -v

# Run benchmarks
python benchmarks/benchmark_llm.py
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Anthropic** - For the amazing Claude and MCP
- **Gradio Team** - For the excellent UI framework
- **HuggingFace** - For Inference API and Spaces hosting
- **Ollama** - For local LLM capabilities

---

## 📞 Contact

**Author**: Juan Carlos  
**GitHub**: [@JuanCS-Dev](https://github.com/JuanCS-Dev)  
**Project**: [qwen-dev-cli](https://github.com/JuanCS-Dev/qwen-dev-cli)

---

**Built for MCP 1st Birthday Hackathon 🎉**

*Soli Deo Gloria* 🙏

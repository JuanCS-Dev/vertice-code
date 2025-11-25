# JUANCS.md - Project Memory for juancs-code

This file is automatically loaded by juancs-code to understand project context.
Similar to CLAUDE.md, it provides project-specific guidance and memory.

## Project Overview

**qwen-dev-cli** is a Claude Code-style AI coding assistant CLI.
- Built with Python 3.11+
- Uses Gemini API as primary LLM provider
- Implements multi-agent architecture with specialized agents
- Provides 40+ development tools

## Architecture

```
qwen_cli/           # Main TUI application (Textual-based)
├── app.py          # Main application entry
├── core/
│   ├── bridge.py   # Integration layer (5000+ lines)
│   └── agentic_prompt.py  # Claude Code-style prompt system
└── ...

qwen_dev_cli/       # Agent system (93K+ lines)
├── agents/         # Specialized agents (Architect, Planner, etc.)
├── tools/          # Claude-parity tools
├── prompts/        # System prompts
└── ...
```

## Development Commands

```bash
# Run the CLI
python -m qwen_cli

# Run tests
pytest tests/

# Type checking
mypy qwen_cli qwen_dev_cli

# Format code
black qwen_cli qwen_dev_cli
```

## Coding Conventions

- **Python Style**: PEP 8, type hints everywhere
- **Async First**: All I/O operations should be async
- **Error Handling**: Always return structured results with success/error
- **Security**: Validate all user inputs, sanitize file paths

## Important Patterns

### Tool Result Format
```python
return {
    "success": True,
    "data": result,
    "metadata": {...}
}
```

### Error Handling
```python
try:
    # operation
except Exception as e:
    return {"success": False, "error": str(e)}
```

## Known Issues / TODOs

- [ ] Improve streaming response handling
- [ ] Add more secret patterns to scanner
- [ ] Implement semantic intent detection

## Preferences

- Prefer concise responses over verbose explanations
- Execute actions immediately, don't describe what you'll do
- Always read files before modifying them
- Run tests after making changes to core logic

## Security Notes

- Never expose API keys in logs or output
- Validate all file paths to prevent traversal
- Block backup/read of system files (/etc, /root, etc.)

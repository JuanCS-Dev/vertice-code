# 📖 QWEN-DEV-CLI USER GUIDE

**Version:** 1.0.0  
**Last Updated:** 2025-11-21

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/qwen-dev-cli
cd qwen-dev-cli

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### First Run

```bash
# Start the CLI
python -m qwen_dev_cli.shell

# You'll see the welcome screen:
┌────────────────────────────────────────────┐
│     🚀 AI-Powered Code Shell               │
│     Type /help for commands                │
└────────────────────────────────────────────┘

qwen-dev-cli ❯ 
```

---

## 💬 Basic Usage

### Natural Language Commands

Just type what you want to do:

```bash
# Read files
qwen-dev-cli ❯ read main.py

# Search code
qwen-dev-cli ❯ search for "def calculate" in python files

# Git operations
qwen-dev-cli ❯ show git status

# Create files
qwen-dev-cli ❯ create a new file hello.py with hello world
```

### System Commands

All commands start with `/`:

```bash
/help          # Show all commands
/exit          # Exit the CLI
/clear         # Clear screen
/history       # Show command history
/tokens        # Show token usage & cost
```

---

## 🔧 Core Features

### 1. File Operations

#### Reading Files
```bash
# Read single file
qwen-dev-cli ❯ /read path/to/file.py

# Read multiple files
qwen-dev-cli ❯ read all Python files in src/
```

#### Writing Files
```bash
# Create new file
qwen-dev-cli ❯ /write path/to/new.py
Content of the file...
[Ctrl+D to finish]

# Edit existing file
qwen-dev-cli ❯ /edit path/to/file.py
# Opens diff preview before applying
```

#### Searching
```bash
# Search in files
qwen-dev-cli ❯ /search "function_name" --type py

# Search with context
qwen-dev-cli ❯ search for authentication logic
```

---

### 2. LSP Code Intelligence

**Multi-language support:** Python, TypeScript, JavaScript, Go

#### Start LSP Server
```bash
qwen-dev-cli ❯ /lsp
✓ LSP server started successfully
Language: python
```

#### Hover Documentation
```bash
# Get documentation at cursor position
qwen-dev-cli ❯ /lsp hover myfile.py:10:5
```

#### Go to Definition
```bash
qwen-dev-cli ❯ /lsp goto myfile.py:15:10

Found 1 definition(s):
  utils.py:42:0
```

#### Find References
```bash
qwen-dev-cli ❯ /lsp refs myfile.py:20:8

Found 5 reference(s):
  main.py:15:4
  tests.py:30:12
  ...
```

#### Code Completion
```bash
qwen-dev-cli ❯ /lsp complete myfile.py:25:10

Code Completions (8 items):
  🔧 calculate_sum - (a: int, b: int) -> int
     Calculates the sum of two numbers
  📦 MAX_VALUE - int
     Maximum allowed value
```

#### Signature Help
```bash
qwen-dev-cli ❯ /lsp signature myfile.py:30:15

Function Signature:
  process_data(data: List[str], format: str = "json") -> Dict

Parameters:
  → data: List[str]
    Input data to process
    format: str = "json"
    Output format
```

---

### 3. Refactoring Tools

#### Rename Symbol
```bash
qwen-dev-cli ❯ /refactor rename myfile.py old_name new_name
✓ Renamed 5 occurrences in myfile.py
```

#### Organize Imports
```bash
qwen-dev-cli ❯ /refactor imports myfile.py
✓ Organized 12 imports (stdlib, third-party, local)
```

---

### 4. Context-Aware Suggestions

#### Related Files
```bash
qwen-dev-cli ❯ /suggest src/main.py

Related files (3 suggestions):
  - src/utils.py: 0.95
  - src/config.py: 0.88
  - tests/test_main.py: 0.82

Reason: Imports, similar symbols, shared dependencies
```

#### Context Optimization
```bash
qwen-dev-cli ❯ /context optimize
✓ Optimized context: 15 items → 8 items
✓ Saved 12,450 tokens
```

---

### 5. Git Integration

```bash
# Status
qwen-dev-cli ❯ /git status

# Commit
qwen-dev-cli ❯ /git commit "feat: add new feature"

# Branch operations
qwen-dev-cli ❯ /git branch feature/new-stuff
qwen-dev-cli ❯ /git checkout main
```

---

### 6. Token Tracking

```bash
qwen-dev-cli ❯ /tokens

Token Usage:
┌─────────────────────────────────────────┐
│ Session: 45,230 tokens                  │
│ Cost: $0.12 (estimated)                 │
│ Model: qwen-2.5-235b-instruct          │
│                                         │
│ History:                                │
│  - Query 1: 3,450 tokens                │
│  - Query 2: 8,920 tokens                │
│  - Query 3: 2,100 tokens                │
└─────────────────────────────────────────┘
```

---

## 🎨 Advanced Features

### Command Palette (Ctrl+K)

Press `Ctrl+K` to open fuzzy command search:

```
╭─────────────────────────────────────╮
│ Search commands...                  │
│                                     │
│ ❯ /read - Read file                │
│   /write - Write file               │
│   /search - Search in files         │
│   /git - Git operations             │
│   /lsp - Code intelligence          │
╰─────────────────────────────────────╯
```

### Inline Preview

For destructive operations, preview changes first:

```bash
qwen-dev-cli ❯ /edit main.py

╭─────────────── Diff Preview ───────────────╮
│ - old_function()                           │
│ + new_function()                           │
│                                            │
│ Apply changes? [Y/n]                       │
╰────────────────────────────────────────────╯
```

### Workflow Visualization

Track complex operations:

```bash
qwen-dev-cli ❯ create new feature module

Workflow Progress:
┌─────────────────────────────────────┐
│ ✓ Analyze requirements              │
│ ✓ Generate code structure           │
│ ⏳ Create files (2/4)                │
│ ⏸  Run tests                         │
│ ⏸  Update documentation             │
└─────────────────────────────────────┘
```

---

## 🔐 Safety & Security

### Constitutional AI Protection

The CLI includes built-in safety checks:

```bash
# Dangerous operation detected
qwen-dev-cli ❯ delete all files

⚠️  WARNING: Potentially dangerous operation
This action will delete files permanently.

Constitutional Review:
  - HRI Score: 0.45 (caution)
  - Safety Check: BLOCKED
  
Type "I UNDERSTAND" to proceed anyway: _
```

### Rate Limiting

Automatic rate limiting prevents abuse:

```bash
⚠️  Rate limit: 10 requests/minute
Wait 15 seconds before next request...
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# API Keys
NEBIUS_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Model Configuration
DEFAULT_MODEL=qwen-2.5-235b-instruct
TEMPERATURE=0.7
MAX_TOKENS=4096

# Performance
TTFT_TARGET=2.0
MAX_RETRIES=3
```

### Settings

```bash
# View current settings
qwen-dev-cli ❯ /settings

# Change model
qwen-dev-cli ❯ /model qwen-3-235b-instruct

# Adjust temperature
qwen-dev-cli ❯ /temperature 0.3
```

---

## 🐛 Troubleshooting

### Common Issues

#### "LSP server failed to start"
```bash
# Install Python LSP server
pip install python-lsp-server[all]

# For TypeScript
npm install -g typescript-language-server

# For Go
go install golang.org/x/tools/gopls@latest
```

#### "API key not found"
```bash
# Check .env file exists
ls -la .env

# Verify key is set
cat .env | grep NEBIUS_API_KEY
```

#### "Out of memory"
```bash
# Reduce context window
qwen-dev-cli ❯ /context clear

# Use smaller model
qwen-dev-cli ❯ /model qwen-2-72b-instruct
```

### Debug Mode

```bash
# Enable verbose logging
export DEBUG=1
python -m qwen_dev_cli.shell

# Check logs
tail -f ~/.qwen-dev-cli/logs/debug.log
```

---

## 💡 Tips & Best Practices

### 1. **Start with /help**
Always check available commands first.

### 2. **Use Context Wisely**
Clear context when switching tasks:
```bash
qwen-dev-cli ❯ /context clear
```

### 3. **Preview Before Applying**
Always review diffs for file edits.

### 4. **Track Token Usage**
Monitor costs with `/tokens`.

### 5. **Use Natural Language**
The CLI understands context:
```bash
# Instead of complex commands:
qwen-dev-cli ❯ find all TODO comments in Python files and list them

# Works better than:
qwen-dev-cli ❯ /search "TODO" --type py --format list
```

### 6. **Leverage LSP Features**
Use code intelligence before refactoring:
```bash
# 1. Find all references
qwen-dev-cli ❯ /lsp refs myfile.py:10:5

# 2. Check usage
qwen-dev-cli ❯ /lsp hover myfile.py:10:5

# 3. Refactor safely
qwen-dev-cli ❯ /refactor rename myfile.py old_name new_name
```

---

## 📚 Learn More

- **Master Plan:** [MASTER_PLAN.md](../MASTER_PLAN.md)
- **API Reference:** [API.md](API.md)
- **Examples:** [EXAMPLES.md](EXAMPLES.md)
- **Contributing:** [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 🆘 Getting Help

- **In-CLI Help:** `/help`
- **GitHub Issues:** [Report a bug](https://github.com/yourusername/qwen-dev-cli/issues)
- **Discord:** Join our community (link)

---

**Happy Coding! 🚀**

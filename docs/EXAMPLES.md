# 📚 QWEN-DEV-CLI EXAMPLES

**Practical real-world scenarios.**

---

## 🚀 Getting Started

### Example 1: First Steps

```bash
# Start CLI
python -m qwen_dev_cli.shell

# Read project README
qwen-dev-cli ❯ read README.md

# Search for main entry point
qwen-dev-cli ❯ search for "if __name__" in python files

# Get project structure
qwen-dev-cli ❯ list all directories
```

---

## 📝 File Operations

### Example 2: Creating a New Module

```bash
qwen-dev-cli ❯ Create a new Python module called utils.py with helper functions for file operations

# AI generates:
# - utils.py with common file operations
# - Docstrings
# - Type hints
# - Error handling

qwen-dev-cli ❯ read utils.py
# Review generated code

qwen-dev-cli ❯ /refactor imports utils.py
# Organize imports

qwen-dev-cli ❯ run tests for utils.py
# Validate functionality
```

### Example 3: Refactoring Legacy Code

```bash
# Find all TODOs
qwen-dev-cli ❯ search for "TODO" in python files

# Get context on a file
qwen-dev-cli ❯ /suggest legacy_code.py

Related files (3):
  - config.py: 0.92
  - models.py: 0.85
  - tests/test_legacy.py: 0.78

# Rename outdated function
qwen-dev-cli ❯ /refactor rename legacy_code.py oldFunction newFunction
✓ Renamed 8 occurrences

# Organize messy imports
qwen-dev-cli ❯ /refactor imports legacy_code.py
✓ Organized 15 imports
```

---

## 🔍 Code Intelligence

### Example 4: Exploring Unknown Codebase

```bash
# Start LSP for Python
qwen-dev-cli ❯ /lsp
✓ LSP server started (python)

# Find main entry point
qwen-dev-cli ❯ search for "def main" in python files

Found: src/main.py:42

# Get hover documentation
qwen-dev-cli ❯ /lsp hover src/main.py:42:4

def main() -> int:
    '''Main entry point for the application.
    
    Returns:
        int: Exit code (0 = success)
    '''

# Find all references to main()
qwen-dev-cli ❯ /lsp refs src/main.py:42:4

Found 3 reference(s):
  - src/__init__.py:10:8
  - tests/test_main.py:15:12
  - setup.py:25:20

# Go to definition of imported function
qwen-dev-cli ❯ /lsp goto src/main.py:5:10
→ src/utils.py:120:0
```

### Example 5: Understanding Function Signatures

```bash
# Working with complex API
qwen-dev-cli ❯ read src/api.py

# Get signature help while editing
qwen-dev-cli ❯ /lsp signature src/api.py:50:25

Function Signature:
  make_request(
      url: str,
      method: str = "GET",
      headers: Dict[str, str] = {},
      timeout: int = 30
  ) -> Response

Parameters:
  → url: str
    API endpoint URL
  → method: str = "GET"
    HTTP method (GET, POST, PUT, DELETE)
    headers: Dict[str, str] = {}
    Optional HTTP headers
    timeout: int = 30
    Request timeout in seconds
```

---

## 🔨 Development Workflow

### Example 6: Feature Development

```bash
# 1. Create feature branch
qwen-dev-cli ❯ /git branch feature/user-auth

# 2. Generate boilerplate
qwen-dev-cli ❯ Create user authentication module with login/logout functions

# 3. Get completions while coding
qwen-dev-cli ❯ /lsp complete src/auth.py:30:10

Code Completions:
  🔧 hash_password - (password: str) -> str
  🔧 verify_password - (password: str, hash: str) -> bool
  📦 PASSWORD_MIN_LENGTH - int

# 4. Run tests
qwen-dev-cli ❯ run pytest tests/test_auth.py

# 5. Check coverage
qwen-dev-cli ❯ show test coverage for src/auth.py

# 6. Commit changes
qwen-dev-cli ❯ /git commit "feat: add user authentication"
```

### Example 7: Bug Fixing

```bash
# Bug reported: "NameError in calculate_total"
qwen-dev-cli ❯ search for "calculate_total" in python files

Found in: src/billing.py:85

# Get context
qwen-dev-cli ❯ /suggest src/billing.py

# Read the problematic function
qwen-dev-cli ❯ read src/billing.py --lines 80-100

# Find all references
qwen-dev-cli ❯ /lsp refs src/billing.py:85:4

Found 5 references:
  - src/main.py:120:8
  - src/reports.py:45:12
  - tests/test_billing.py:30:20
  ...

# Check where variable is defined
qwen-dev-cli ❯ /lsp goto src/billing.py:87:10
→ src/config.py:15:0

# Fix the import
qwen-dev-cli ❯ edit src/billing.py
# Add: from config import TAX_RATE

# Test the fix
qwen-dev-cli ❯ run python src/billing.py
```

---

## 📊 Code Analysis

### Example 8: Technical Debt Assessment

```bash
# Find all TODOs
qwen-dev-cli ❯ search for "TODO|FIXME|XXX" in all files

Found 23 matches:
  - src/legacy.py: 8 TODOs
  - src/utils.py: 5 FIXMEs
  - tests/old_tests.py: 10 XXXs

# Check code complexity
qwen-dev-cli ❯ analyze complexity in src/legacy.py

Functions with high complexity:
  - process_data (complexity: 15)
  - validate_input (complexity: 12)
  - parse_config (complexity: 10)

# Get refactoring suggestions
qwen-dev-cli ❯ /suggest src/legacy.py

Suggestions:
  1. Extract process_data into smaller functions
  2. Move validation to separate module
  3. Use dataclasses for config parsing
```

### Example 9: Dependency Analysis

```bash
# Check what imports a module
qwen-dev-cli ❯ search for "from utils import" in python files

# Get dependency tree
qwen-dev-cli ❯ show dependencies for src/main.py

Dependencies:
  - config.py (direct)
  - utils.py (direct)
    └─ helpers.py (indirect)
  - models.py (direct)
    └─ database.py (indirect)
    └─ validators.py (indirect)

# Find circular dependencies
qwen-dev-cli ❯ check for circular imports
```

---

## 🎨 Multi-Language Projects

### Example 10: TypeScript + Python

```bash
# Switch to TypeScript
qwen-dev-cli ❯ /lsp
✓ LSP server started (python)

# Work on TS file
qwen-dev-cli ❯ read frontend/src/App.tsx

# Auto-detect TypeScript
qwen-dev-cli ❯ /lsp complete frontend/src/App.tsx:25:10

Code Completions (TypeScript):
  🔧 useState - <T>(initialState: T) => [T, Dispatch<SetStateAction<T>>]
  🔧 useEffect - (effect: EffectCallback, deps?: DependencyList) => void
  ⚙️ render - () => ReactElement

# Get signature help
qwen-dev-cli ❯ /lsp signature frontend/src/App.tsx:30:15

Function Signature (TypeScript):
  fetch(
      input: RequestInfo | URL,
      init?: RequestInit
  ): Promise<Response>

# Switch back to Python
qwen-dev-cli ❯ read backend/api.py
# LSP auto-switches to Python
```

---

## 🚀 Advanced Workflows

### Example 11: Automated Code Review

```bash
# Before committing
qwen-dev-cli ❯ /git status

Changes:
  - src/new_feature.py (modified)
  - tests/test_feature.py (new)

# Check diagnostics
qwen-dev-cli ❯ /lsp diag src/new_feature.py

Diagnostics:
  ✓ No errors found

# Organize imports
qwen-dev-cli ❯ /refactor imports src/new_feature.py

# Run formatter (via hook)
qwen-dev-cli ❯ format src/new_feature.py
✓ Hook: black executed successfully

# Run linter
qwen-dev-cli ❯ lint src/new_feature.py
✓ All checks passed

# Commit
qwen-dev-cli ❯ /git commit "feat: add new feature"
```

### Example 12: Documentation Generation

```bash
# Generate docstrings
qwen-dev-cli ❯ add docstrings to src/utils.py

# Review
qwen-dev-cli ❯ read src/utils.py --lines 1-50

# Generate API docs
qwen-dev-cli ❯ create API documentation for all Python modules

# Update README
qwen-dev-cli ❯ update README.md with new features section
```

---

## 🔧 Productivity Hacks

### Example 13: Quick Context Switching

```bash
# Working on feature A
qwen-dev-cli ❯ read src/feature_a.py

# Bug reported in feature B
qwen-dev-cli ❯ /context save feature_a

# Switch to bug
qwen-dev-cli ❯ /context clear
qwen-dev-cli ❯ read src/feature_b.py
# Fix bug...

# Switch back to feature A
qwen-dev-cli ❯ /context load feature_a
# Context restored!
```

### Example 14: Batch Operations

```bash
# Format all Python files
qwen-dev-cli ❯ format all python files in src/

# Run tests for all modules
qwen-dev-cli ❯ run tests for all modules

# Update imports in all files
qwen-dev-cli ❯ /refactor imports src/*.py
```

---

## 💡 Tips & Tricks

### Smart Context Usage

```bash
# Clear context when switching tasks
qwen-dev-cli ❯ /context clear

# Only add relevant files
qwen-dev-cli ❯ /suggest current_file.py
# Shows related files to add
```

### Keyboard Shortcuts

```bash
Ctrl+K    # Command palette
Ctrl+C    # Cancel operation
Ctrl+D    # Finish multi-line input
↑/↓       # Command history
Tab       # Auto-complete
```

### Natural Language Power

```bash
# Instead of remembering exact commands:
qwen-dev-cli ❯ find all functions that use deprecated API

# Works better than:
qwen-dev-cli ❯ /search "deprecated_api" --type function
```

---

## 📚 More Examples

Check out:
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
- **API Reference:** [API.md](API.md)
- **Tutorial Videos:** (coming soon)

---

**Have a cool example?** Contribute via [Pull Request](../CONTRIBUTING.md)!

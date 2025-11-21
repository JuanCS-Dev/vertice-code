# 🔧 API REFERENCE

**Version:** 1.0.0  
**For Developers & Contributors**

---

## 📦 Core Modules

### `qwen_dev_cli.shell`

**Main interactive shell.**

```python
from qwen_dev_cli.shell import InteractiveShell

# Initialize shell
shell = InteractiveShell()

# Access components
shell.indexer          # Semantic indexer
shell.lsp_client       # LSP client
shell.suggestion_engine  # Context suggestions
shell.refactoring_engine  # Refactoring tools
shell.context_manager  # Context management
```

---

### `qwen_dev_cli.intelligence.lsp_client`

**Multi-language LSP client.**

#### Classes

```python
from qwen_dev_cli.intelligence.lsp_client import (
    LSPClient,
    Language,
    CompletionItem,
    SignatureHelp,
)

# Language detection
lang = Language.detect(Path("myfile.ts"))
# Returns: Language.TYPESCRIPT

# Initialize client
client = LSPClient(root_path=Path.cwd(), language=Language.PYTHON)

# Start server
await client.start()

# Get completions
completions = await client.completion(
    file_path=Path("myfile.py"),
    line=10,
    character=5
)

# Get signature help
sig_help = await client.signature_help(
    file_path=Path("myfile.py"),
    line=15,
    character=20
)
```

#### Language Support

```python
class Language(Enum):
    PYTHON = "python"      # pylsp
    TYPESCRIPT = "typescript"  # typescript-language-server
    JAVASCRIPT = "javascript"  # typescript-language-server
    GO = "go"              # gopls
    UNKNOWN = "unknown"
```

---

### `qwen_dev_cli.refactoring.engine`

**Code refactoring utilities.**

```python
from qwen_dev_cli.refactoring.engine import (
    RefactoringEngine,
    RefactoringResult
)

engine = RefactoringEngine(project_root=Path.cwd())

# Rename symbol
result = engine.rename_symbol(
    file_path=Path("myfile.py"),
    old_name="old_func",
    new_name="new_func"
)

if result.success:
    print(f"✓ {result.message}")
    print(f"Files modified: {result.files_modified}")
else:
    print(f"✗ Error: {result.error}")

# Organize imports
result = engine.organize_imports(file_path=Path("myfile.py"))
```

#### RefactoringResult

```python
@dataclass
class RefactoringResult:
    success: bool
    message: str
    files_modified: List[Path]
    changes_preview: str
    error: Optional[str] = None
```

---

### `qwen_dev_cli.intelligence.context_suggestions`

**Context-aware file recommendations.**

```python
from qwen_dev_cli.intelligence.context_suggestions import (
    ContextSuggestionEngine,
    FileRecommendation
)

engine = ContextSuggestionEngine(
    project_root=Path.cwd(),
    indexer=indexer  # SemanticIndexer instance
)

# Get related files
suggestions = engine.suggest_related_files(
    file_path=Path("src/main.py"),
    max_suggestions=5
)

for rec in suggestions:
    print(f"{rec.file_path.name}: {rec.relevance_score:.2f}")
    print(f"  Reason: {rec.reason}")
```

---

### `qwen_dev_cli.intelligence.indexer`

**Semantic code indexing.**

```python
from qwen_dev_cli.intelligence.indexer import SemanticIndexer

indexer = SemanticIndexer(root_path=str(Path.cwd()))

# Index codebase
files_indexed = indexer.index_codebase(force=False)

# Search symbols
symbols = indexer.search_symbols("LSPClient", limit=10)

for symbol in symbols:
    print(f"{symbol.name} ({symbol.type}) in {symbol.file_path}")

# Find definition
location = indexer.find_definition("NameError: undefined_func")
if location:
    file_path, line = location
    print(f"Definition at {file_path}:{line}")
```

---

## 🎨 UI Components

### `qwen_dev_cli.tui.dashboard`

**Live system dashboard.**

```python
from qwen_dev_cli.tui.dashboard import Dashboard, OperationStatus

dashboard = Dashboard(console=console, max_history=5)

# Track operation
op_id = dashboard.start_operation(
    name="Build Project",
    description="Compiling source files"
)

# Update progress
dashboard.update_progress(op_id, current=50, total=100)

# Complete
dashboard.complete_operation(op_id, OperationStatus.SUCCESS)

# Render
dashboard.render()
```

---

### `qwen_dev_cli.tui.command_palette`

**Fuzzy command search.**

```python
from qwen_dev_cli.tui.command_palette import CommandPalette

commands = [
    {"name": "read", "description": "Read file"},
    {"name": "write", "description": "Write file"},
]

palette = CommandPalette(commands=commands)

# Show palette (blocking)
selected = palette.show()

if selected:
    print(f"Selected: {selected['name']}")
```

---

## 🔌 Extending the CLI

### Adding Custom Commands

```python
# In shell.py, add to _process_command()

elif cmd.startswith("/mycmd "):
    # Your command logic here
    arg = cmd[7:].strip()
    
    # Do something
    result = my_custom_function(arg)
    
    # Return (continue_loop, output)
    return False, f"Result: {result}"
```

### Adding LSP Language Support

```python
# In lsp_client.py

# 1. Add language to enum
class Language(Enum):
    # ...
    RUST = "rust"

# 2. Add server config
@classmethod
def get_configs(cls) -> Dict[Language, "LSPServerConfig"]:
    return {
        # ...
        Language.RUST: cls(
            language=Language.RUST,
            command=["rust-analyzer"],
            initialization_options={}
        ),
    }

# 3. Add file extension mapping
@classmethod
def detect(cls, file_path: Path) -> "Language":
    suffix = file_path.suffix.lower()
    mapping = {
        # ...
        ".rs": cls.RUST,
    }
    return mapping.get(suffix, cls.UNKNOWN)
```

### Adding Refactoring Operations

```python
# In refactoring/engine.py

def extract_function(
    self,
    file_path: Path,
    start_line: int,
    end_line: int,
    new_func_name: str
) -> RefactoringResult:
    """Extract lines into new function."""
    try:
        content = file_path.read_text()
        lines = content.splitlines()
        
        # Extract selected lines
        selected = lines[start_line:end_line+1]
        
        # Create new function
        new_func = f"def {new_func_name}():\n"
        new_func += "\n".join(f"    {line}" for line in selected)
        
        # Replace in original
        lines[start_line:end_line+1] = [f"{new_func_name}()"]
        
        # Add function definition
        lines.insert(start_line, new_func)
        
        # Write back
        file_path.write_text("\n".join(lines))
        
        return RefactoringResult(
            success=True,
            message=f"Extracted {end_line-start_line+1} lines",
            files_modified=[file_path],
            changes_preview=new_func
        )
    except Exception as e:
        return RefactoringResult(
            success=False,
            message="Extraction failed",
            files_modified=[],
            changes_preview="",
            error=str(e)
        )
```

---

## 🪝 Hooks System

**Automated actions on file operations.**

### Configuration

Create `.qwen-hooks.json`:

```json
{
  "hooks": [
    {
      "event": "post_write",
      "pattern": "*.py",
      "command": "black ${FILE}",
      "priority": "high"
    },
    {
      "event": "post_edit",
      "pattern": "*.ts",
      "command": "prettier --write ${FILE}",
      "priority": "normal"
    }
  ]
}
```

### Programmatic Usage

```python
from qwen_dev_cli.hooks.executor import HookExecutor
from qwen_dev_cli.hooks.events import HookEvent

executor = HookExecutor(
    config_path=Path(".qwen-hooks.json"),
    timeout=30,
    use_sandbox=True
)

# Execute hooks
results = await executor.execute_hooks(
    event=HookEvent.POST_WRITE,
    file_path=Path("myfile.py")
)

for result in results:
    if result.success:
        print(f"✓ {result.hook_name}: {result.output}")
    else:
        print(f"✗ {result.hook_name}: {result.error}")
```

### Available Events

```python
class HookEvent(Enum):
    PRE_WRITE = "pre_write"
    POST_WRITE = "post_write"
    PRE_EDIT = "pre_edit"
    POST_EDIT = "post_edit"
    PRE_DELETE = "pre_delete"
    POST_DELETE = "post_delete"
    PRE_GIT = "pre_git"
    POST_GIT = "post_git"
```

---

## 🔧 Testing Utilities

### Test Helpers

```python
from qwen_dev_cli.shell import InteractiveShell
from pathlib import Path

def test_shell_initialization():
    """Test shell starts correctly."""
    shell = InteractiveShell()
    
    assert shell.indexer is not None
    assert shell.lsp_client is not None
    assert shell.suggestion_engine is not None

def test_language_detection():
    """Test LSP language detection."""
    from qwen_dev_cli.intelligence.lsp_client import Language
    
    assert Language.detect(Path("test.py")) == Language.PYTHON
    assert Language.detect(Path("test.ts")) == Language.TYPESCRIPT
    assert Language.detect(Path("test.go")) == Language.GO
```

### Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "tests").mkdir()
    return tmp_path

@pytest.fixture
def lsp_client(temp_project):
    """LSP client for testing."""
    from qwen_dev_cli.intelligence.lsp_client import LSPClient
    return LSPClient(root_path=temp_project)
```

---

## 📊 Type Signatures

### Key Types

```python
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

# LSP Types
@dataclass
class Position:
    line: int
    character: int

@dataclass
class Range:
    start: Position
    end: Position

@dataclass
class Location:
    uri: str
    range: Range

@dataclass
class CompletionItem:
    label: str
    kind: int
    detail: Optional[str]
    documentation: Optional[str]
    insert_text: Optional[str]

# Refactoring Types
@dataclass
class RefactoringResult:
    success: bool
    message: str
    files_modified: List[Path]
    changes_preview: str
    error: Optional[str] = None

# Context Types
@dataclass
class FileRecommendation:
    file_path: Path
    relevance_score: float
    reason: str
```

---

## 🔒 Safety & Validation

### Input Validation

```python
from qwen_dev_cli.core.validation import validate_file_path

# Validate file paths
try:
    safe_path = validate_file_path(user_input, base_dir=Path.cwd())
    # Use safe_path
except ValueError as e:
    print(f"Invalid path: {e}")
```

### Rate Limiting

```python
from qwen_dev_cli.core.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=10, window_seconds=60)

if limiter.allow_request():
    # Process request
    pass
else:
    # Rate limited
    wait_time = limiter.time_until_next()
    print(f"Rate limited. Wait {wait_time}s")
```

---

## 📚 Further Reading

- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
- **Examples:** [EXAMPLES.md](EXAMPLES.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing:** [../CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 💡 Best Practices

### 1. **Type Everything**
Use type hints for all public APIs.

### 2. **Handle Errors Gracefully**
Return Result types instead of raising exceptions.

### 3. **Test Edge Cases**
Cover empty inputs, invalid paths, large files.

### 4. **Document Public APIs**
Docstrings for all public functions/classes.

### 5. **Async Where Appropriate**
Use `async/await` for I/O operations.

---

**Need Help?** Open an issue or check [USER_GUIDE.md](USER_GUIDE.md)

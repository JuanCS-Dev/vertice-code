# 🛠️ MCP & Tools Guide (Vértice)

> **"One Tool, Everywhere."**

This guide explains the unified architecture for adding, exposing, and managing tools in the Vértice ecosystem.

---

## 1. Architecture Overview

Vértice uses a **Unified Tool Catalog** (`src/vertice_cli/tools/catalog.py`) as the single source of truth.
When you add a tool here, it automatically becomes available in:
1.  **TUI (Interactive Mode):** For agentic workflows.
2.  **MCP Server:** For external clients like Claude Desktop or Cursor.
3.  **Headless Mode:** For CI/CD automation.

### Key Components
- **`BaseTool`**: The abstract base class for all tools.
- **`ToolCatalog`**: The builder pattern registry that groups tools by category.
- **`MCPManager`**: Manages the local MCP server (SSE/Stdio) and external connections.
- **`@cache_tool_result`**: Decorator for performance optimization.

---

## 2. How to Add a New Tool

### Step 1: Create the Tool Class

Create your tool in `src/vertice_cli/tools/<category>/`.
Inherit from `ValidatedTool` (recommended) or `BaseTool`.

```python
from vertice_cli.tools.base import ToolResult, ToolCategory
from vertice_cli.tools.validated import ValidatedTool
from vertice_cli.tools.caching import cache_tool_result

class MyNewTool(ValidatedTool):
    """Description of what the tool does."""

    def __init__(self):
        super().__init__()
        self.name = "my_new_tool"  # Snake case name
        self.category = ToolCategory.SYSTEM
        self.description = "Detailed description for the LLM"
        self.parameters = {
            "target": {
                "type": "string",
                "description": "Target to operate on",
                "required": True
            },
            "force": {
                "type": "boolean",
                "description": "Force operation",
                "required": False
            }
        }
        # Security: Require explicit approval for dangerous tools
        self.requires_approval = False

    def get_validators(self):
        """Optional: Pydantic-style validators."""
        return {
            "target": lambda v: len(str(v)) > 0
        }

    @cache_tool_result(ttl_seconds=60)  # Optional caching
    async def _execute_validated(self, target: str, force: bool = False) -> ToolResult:
        try:
            # Your logic here
            result = f"Processed {target}"

            return ToolResult(
                success=True,
                data=result,
                metadata={"target": target}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### Step 2: Register in Catalog

Update `src/vertice_cli/tools/catalog.py`:

1.  Import your tool.
2.  Add it to `add_defaults()` or a specific category method.

```python
# src/vertice_cli/tools/catalog.py

from vertice_cli.tools.my_category import MyNewTool

class ToolCatalog:
    # ...
    def add_defaults(self) -> "ToolCatalog":
        tools = [
            # ... existing tools
            MyNewTool,  # <--- Add this
        ]
        self._register_batch("defaults", tools)
        return self
```

### Step 3: Verify

Run the CLI to see your tool listed:

```bash
vertice tools
```

---

## 3. MCP Server Configuration

Vértice supports two MCP transport modes:

### A. SSE (Server-Sent Events) - Default
Best for local development and debugging.

```bash
# Start server on port 8000
vertice serve --transport sse --port 8000
```

### B. Stdio (Standard Input/Output)
Best for integration with Claude Desktop or IDEs.

```bash
vertice serve --transport stdio
```

### Claude Desktop Config
To use Vértice tools in Claude Desktop, add this to your config:

```json
{
  "mcpServers": {
    "vertice": {
      "command": "vertice",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

---

## 4. Advanced Features

### Observability & Tracing
All tool executions are automatically wrapped in a structured logging context.
You don't need to do anything special. Logs will include:
- `correlation_id`: Trace ID across async tasks.
- `duration_ms`: Execution time.
- `component`: Tool name.

### Caching
Use `@cache_tool_result(ttl_seconds=N)` for read-heavy operations (e.g., directory listing, file search).

```python
@cache_tool_result(ttl_seconds=300)
async def _execute_validated(self, ...):
```

### Security Tiers
- **Read-Only**: Safe to execute automatically.
- **Mutating**: Requires approval if `requires_approval = True`.
- **Governance**: The TUI governance layer intercepts sensitive calls.

---

## 5. Testing Tools

Create a unit test in `tests/tools/`:

```python
import pytest
from vertice_cli.tools.my_category import MyNewTool

@pytest.mark.asyncio
async def test_my_new_tool():
    tool = MyNewTool()
    result = await tool._execute_validated(target="test")

    assert result.success
    assert "Processed test" in str(result.data)
```

To run tests:
```bash
pytest tests/tools/
```

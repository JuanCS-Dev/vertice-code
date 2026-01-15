"""
🔧 VERTICE-CLI TOOLS BASE - CLEAN CONSOLIDATION

Consolidated base classes for the tool system.
Follows CODE_CONSTITUTION principles for simplicity and safety.

CODE_CONSTITUTION §3: Simplicity at Scale
CODE_CONSTITUTION §4: Safety First (Type Safety)
"""

from typing import Any, Dict, Optional


class ToolResult:
    """Represents the result of a tool execution."""
    
    def __init__(
        self,
        success: bool = True,
        message: str = '',
        data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.message = message
        self.data = data
        self.metadata = metadata or {}
        self.error = error
    
    def __repr__(self) -> str:
        return f"ToolResult(success={self.success}, message='{self.message}')"


class BaseTool:
    """Base class for all tools in the Vertice system."""
    
    name: str = "base_tool"
    description: str = "Base tool class"
    parameters: Dict[str, Any] = {}
    
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM tool use."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": [
                    k for k, v in self.parameters.items() 
                    if v.get('required', False)
                ]
            }
        }


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.
        
        If tool.name is 'base_tool' (default), derives name from class name:
        ReadFileTool -> read_file, ListDirectoryTool -> list_directory
        """
        name = getattr(tool, 'name', 'base_tool')
        
        # If name is the default, derive from class name
        if name == 'base_tool':
            class_name = tool.__class__.__name__
            # Convert CamelCase to snake_case and remove 'Tool' suffix
            import re
            name = re.sub(r'Tool$', '', class_name)
            name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        
        self.tools[name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Alias for get() for backward compatibility."""
        return self.get(name)
    
    def list_tools(self) -> list:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def get_all(self) -> Dict[str, BaseTool]:
        """Get all registered tools as a dictionary."""
        return self.tools


# Backward compatibility aliases
Tool = BaseTool
CleanToolRegistry = ToolRegistry


class ToolCategory:
    """Tool categories for organization."""
    
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_MGMT = "file_mgmt"
    SEARCH = "search"
    EXECUTION = "execution"
    GIT = "git"
    CONTEXT = "context"
    SYSTEM = "system"


__all__ = [
    "BaseTool",
    "Tool",
    "ToolResult", 
    "ToolRegistry",
    "CleanToolRegistry",
    "ToolCategory"
]

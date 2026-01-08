"""
🔧 VERTICE-CLI TOOLS BASE - CLEAN CONSOLIDATION

Consolidated base classes using clean_tool_system_v2.py.
Removes duplication and follows CODE_CONSTITUTION principles.

CODE_CONSTITUTION §3: Simplicity at Scale
CODE_CONSTITUTION §4: Safety First (Type Safety)
"""

# Import clean system (dependency injection principle)
from clean_tool_system_v2 import BaseTool as CleanBaseTool, ToolResult as CleanToolResult
from clean_tool_system_v2 import CleanToolRegistry

# Maintain backward compatibility
Tool = CleanBaseTool
ToolResult = CleanToolResult
ToolRegistry = CleanToolRegistry


# Legacy enum for compatibility (deprecated - use direct strings)
class ToolCategory:
    """Legacy tool categories - prefer direct usage in clean system."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_MGMT = "file_mgmt"
    SEARCH = "search"
    EXECUTION = "execution"
    GIT = "git"
    CONTEXT = "context"
    SYSTEM = "system"


__all__ = ["Tool", "ToolResult", "ToolRegistry", "ToolCategory"]

"""
Claude Code Parity Tools - Modular Architecture
================================================

Decomposed from claude_parity_tools.py (2069 lines) into focused modules.

Modules:
- file_tools: GlobTool, LSTool, MultiEditTool
- web_tools: WebFetchTool, WebSearchTool
- notebook_tools: NotebookReadTool, NotebookEditTool
- todo_tools: TodoReadTool, TodoWriteTool
- execution_tools: BackgroundTaskTool, BashOutputTool, KillShellTool
- interaction_tools: AskUserQuestionTool, SkillTool, SlashCommandTool
- task_tool: TaskTool (subagents)

Author: JuanCS Dev
Date: 2025-11-27
"""

from vertice_cli.tools.parity.file_tools import (
    GlobTool,
    LSTool,
    MultiEditTool,
    get_file_tools,
)
from vertice_cli.tools.parity.web_tools import (
    WebFetchTool,
    WebSearchTool,
    get_web_tools,
)
from vertice_cli.tools.parity.notebook_tools import (
    NotebookReadTool,
    NotebookEditTool,
    get_notebook_tools,
)
from vertice_cli.tools.parity.todo_tools import (
    TodoReadTool,
    TodoWriteTool,
    get_todo_tools,
)
from vertice_cli.tools.parity.execution_tools import (
    BackgroundTaskTool,
    BashOutputTool,
    KillShellTool,
    get_execution_tools,
)
from vertice_cli.tools.parity.interaction_tools import (
    AskUserQuestionTool,
    SkillTool,
    SlashCommandTool,
    get_interaction_tools,
)
from vertice_cli.tools.parity.task_tool import (
    TaskTool,
)

# P2.4 FIX: Import prometheus tools for memory capability
# Source: Google Developers - "Advanced agentic patterns: memory for robust agents"
try:
    from vertice_cli.tools.prometheus_tools import (
        PrometheusMemoryQueryTool,
        PrometheusExecuteTool,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from vertice_cli.tools.base import Tool
from typing import List


def get_claude_parity_tools(prometheus_provider=None) -> List[Tool]:
    """
    Get all Claude Code parity tools.

    P2.4 FIX: Now includes memory tools when prometheus_provider is available.

    Args:
        prometheus_provider: Optional PROMETHEUS provider for memory tools

    Returns:
        List of all parity tools for registration
    """
    tools = [
        *get_file_tools(),
        *get_web_tools(),
        *get_notebook_tools(),
        *get_todo_tools(),
        *get_execution_tools(),
        *get_interaction_tools(),
        TaskTool(),
    ]

    # P2.4: Add memory tools if prometheus is available
    if PROMETHEUS_AVAILABLE and prometheus_provider is not None:
        memory_tool = PrometheusMemoryQueryTool(prometheus_provider)
        execute_tool = PrometheusExecuteTool(prometheus_provider)
        tools.extend([memory_tool, execute_tool])

    return tools


def get_memory_tools(prometheus_provider=None) -> List[Tool]:
    """
    P2.4: Get memory-specific tools.

    Returns empty list if prometheus not available or provider not set.
    """
    if not PROMETHEUS_AVAILABLE or prometheus_provider is None:
        return []

    return [
        PrometheusMemoryQueryTool(prometheus_provider),
    ]


__all__ = [
    # File Tools
    "GlobTool",
    "LSTool",
    "MultiEditTool",
    # Web Tools
    "WebFetchTool",
    "WebSearchTool",
    # Notebook Tools
    "NotebookReadTool",
    "NotebookEditTool",
    # Todo Tools
    "TodoReadTool",
    "TodoWriteTool",
    # Execution Tools
    "BackgroundTaskTool",
    "BashOutputTool",
    "KillShellTool",
    # Interaction Tools
    "AskUserQuestionTool",
    "SkillTool",
    "SlashCommandTool",
    # Task/Subagent Tool
    "TaskTool",
    # Registry
    "get_claude_parity_tools",
    "get_memory_tools",  # P2.4: Memory tools getter
    "PROMETHEUS_AVAILABLE",  # P2.4: Check if prometheus is available
    # Module getters
    "get_file_tools",
    "get_web_tools",
    "get_notebook_tools",
    "get_todo_tools",
    "get_execution_tools",
    "get_interaction_tools",
]

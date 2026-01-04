"""
AGENTIC SYSTEM PROMPT - Claude Code Style
==========================================

This is the secret sauce that enables symbiotic human-AI interaction.

Based on leaked/documented Claude Code architecture:
- 40+ conditional prompt strings dynamically assembled
- Tool result instructions embedded in responses
- Single-threaded master loop with sub-agent spawning
- CLAUDE.md/JUANCS.md as project memory

Key Principles:
1. Model-Based Understanding - not keyword matching
2. Agentic Loop - gather → act → verify → repeat
3. Tool Selection via Reasoning - not rules
4. Context Injection - dynamic based on task
5. Minimal Output - efficient token usage

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .prompt_sections import (
    IDENTITY,
    AGENTIC_BEHAVIOR,
    TOOL_PROTOCOL,
    NLU_SECTION,
    PATTERNS_SECTION,
    SAFETY_SECTION,
    STYLE_SECTION,
    TOOL_GUIDANCE,
    ERROR_GUIDANCE,
)

logger = logging.getLogger(__name__)


def build_agentic_system_prompt(
    tools: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
    project_memory: Optional[str] = None,
    user_memory: Optional[str] = None,
) -> str:
    """
    Build Claude Code-style agentic system prompt.

    This prompt enables:
    - Natural language understanding (not keyword matching)
    - Multi-step task execution with verification
    - Context-aware tool selection
    - Error recovery and adaptation

    Args:
        tools: List of available tool schemas
        context: Dynamic context (cwd, git, files, etc.)
        project_memory: Contents of JUANCS.md (project-specific)
        user_memory: Contents of MEMORY.md (user preferences)

    Returns:
        Complete agentic system prompt
    """
    # Build tool section
    tool_section = _build_tool_section(tools)

    # Build context section
    context_section = _build_context_section(context)

    # Build memory section
    memory_section = _build_memory_section(project_memory, user_memory)

    # Assemble final prompt
    prompt = f"""{IDENTITY}

{tool_section}

{context_section}

{memory_section}

{AGENTIC_BEHAVIOR}

{TOOL_PROTOCOL}

{NLU_SECTION}

{PATTERNS_SECTION}

{SAFETY_SECTION}

{STYLE_SECTION}

---

Now, help the user with their request. Think step by step, use your tools effectively, and be the coding partner they need.
"""

    return prompt


def _build_tool_section(tools: List[Dict[str, Any]]) -> str:
    """Build the tool definitions section."""
    tool_section = "\n## Available Tools\n\n"

    # Group tools by category for better comprehension
    categories: Dict[str, List[Dict[str, Any]]] = {}
    for tool in tools:
        cat = tool.get("category", "general")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    for cat, cat_tools in sorted(categories.items()):
        tool_section += f"### {cat.replace('_', ' ').title()}\n"
        for t in cat_tools:
            name = t["name"]
            desc = t.get("description", "")
            params = t.get("parameters", {})
            required = params.get("required", [])
            properties = params.get("properties", {})

            param_info = []
            for p in required:
                ptype = properties.get(p, {}).get("type", "any")
                param_info.append(f"{p}: {ptype}")

            param_str = f"({', '.join(param_info)})" if param_info else "()"
            tool_section += f"- **{name}**{param_str}: {desc}\n"
        tool_section += "\n"

    return tool_section


def _build_context_section(context: Optional[Dict[str, Any]]) -> str:
    """Build the context section."""
    context_section = "\n## Current Context\n\n"

    if context:
        if context.get("cwd"):
            context_section += f"Working Directory: `{context['cwd']}`\n"
        if context.get("git_branch"):
            context_section += f"Git Branch: `{context['git_branch']}`\n"
        if context.get("git_status"):
            context_section += f"Git Status: {context['git_status']}\n"
        if context.get("modified_files"):
            files = list(context["modified_files"])[:10]
            context_section += f"Modified Files: {', '.join(f'`{f}`' for f in files)}\n"
        if context.get("recent_files"):
            files = list(context["recent_files"])[:5]
            context_section += f"Recent Files: {', '.join(f'`{f}`' for f in files)}\n"
    else:
        context_section += "No context available.\n"

    return context_section


def _build_memory_section(project_memory: Optional[str], user_memory: Optional[str]) -> str:
    """Build the memory section."""
    memory_section = ""

    if project_memory:
        memory_section += f"""
## Project Memory (JUANCS.md)

<project_memory>
{project_memory}
</project_memory>

Use this information to understand project conventions, architecture, and preferences.
"""

    if user_memory:
        memory_section += f"""
## User Memory

<user_memory>
{user_memory}
</user_memory>

Remember user preferences and apply them to your responses.
"""

    return memory_section


def load_project_memory(project_path: str = ".") -> Optional[str]:
    """Load VERTICE.md project memory file."""
    search_paths = [
        Path(project_path) / "VERTICE.md",
        Path(project_path) / ".vertice" / "VERTICE.md",
        Path(project_path) / "CLAUDE.md",
    ]

    for memory_file in search_paths:
        if memory_file.exists():
            try:
                return memory_file.read_text()
            except Exception as e:
                logger.debug(f"Failed to read {memory_file}: {e}")

    return None


def get_dynamic_context() -> Dict[str, Any]:
    """
    Gather dynamic context for the current session.

    Returns:
        Context dictionary with cwd, git info, recent files, etc.
    """
    context: Dict[str, Any] = {
        "cwd": os.getcwd(),
        "modified_files": set(),
        "recent_files": set(),
        "git_branch": None,
        "git_status": None,
    }

    # Get git branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            context["git_branch"] = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        logger.debug(f"Failed to get git branch: {e}")

    # Get git status summary
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines and lines[0]:
                modified = [
                    line[3:] for line in lines if line.startswith(" M") or line.startswith("M ")
                ]
                added = [
                    line[3:] for line in lines if line.startswith("A ") or line.startswith("??")
                ]
                context["modified_files"] = set(modified[:10])
                context["git_status"] = f"{len(modified)} modified, {len(added)} untracked"
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        logger.debug(f"Failed to get git status: {e}")

    return context


def enhance_tool_result(tool_name: str, result: str, success: bool) -> str:
    """
    Enhance tool result with embedded instructions.

    Claude Code embeds instructions in tool results because models
    adhere better to repeated in-context instructions than system prompt alone.

    Args:
        tool_name: Name of the tool that was executed
        result: Raw result from the tool
        success: Whether the tool succeeded

    Returns:
        Enhanced result with embedded guidance
    """
    if not success:
        return f"""<tool_result tool="{tool_name}" success="false">
{result}
</tool_result>

<guidance>
{ERROR_GUIDANCE}
</guidance>
"""

    # Get tool-specific guidance
    guidance = TOOL_GUIDANCE.get(tool_name, "")

    return f"""<tool_result tool="{tool_name}" success="true">
{result}
</tool_result>

<guidance>
{guidance}
</guidance>
"""

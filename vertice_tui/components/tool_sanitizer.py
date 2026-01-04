"""
Tool Call Sanitizer - Convert JSON tool calls to user-friendly display.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple, Pattern


# Tool call detection patterns (order matters - more specific first)
_TOOL_PATTERNS: List[Tuple[Pattern[str], bool]] = [
    # Nested FIRST: {"tool":{"tool":"bash_command","args":{...}}}
    (
        re.compile(
            r'\{"tool"\s*:\s*\{\s*"tool"\s*:\s*"(\w+)"\s*,\s*"args"\s*:\s*(\{[^{}]*\})\s*\}\s*\}',
            re.DOTALL,
        ),
        True,
    ),
    # {"tool": "bash_command", "args": {"command": "..."}}
    (
        re.compile(r'\{\s*"tool"\s*:\s*"(\w+)"\s*,\s*"args"\s*:\s*(\{[^{}]*\})\s*\}', re.DOTALL),
        False,
    ),
    # {"name": "bash_command", "arguments": {"command": "..."}}
    (
        re.compile(
            r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"(?:arguments|params)"\s*:\s*(\{[^{}]*\})\s*\}',
            re.DOTALL,
        ),
        False,
    ),
]


def _format_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Format a tool call for display.

    Args:
        tool_name: Name of the tool
        args: Tool arguments

    Returns:
        Formatted string for display
    """
    if tool_name in ("bash_command", "bash"):
        cmd = args.get("command", args.get("cmd", ""))
        if cmd:
            return f"```bash\n{cmd}\n```"

    elif tool_name == "write_file":
        path = args.get("path", args.get("file_path", ""))
        return f"📝 **Escrevendo arquivo:** `{path}`"

    elif tool_name == "read_file":
        path = args.get("path", args.get("file_path", ""))
        return f"📖 **Lendo arquivo:** `{path}`"

    elif tool_name == "edit_file":
        path = args.get("path", args.get("file_path", ""))
        return f"✏️ **Editando arquivo:** `{path}`"

    elif tool_name in ("web_search", "search"):
        query = args.get("query", args.get("q", ""))
        return f"🔍 **Pesquisando:** `{query}`"

    elif tool_name in ("web_fetch", "fetch_url"):
        url = args.get("url", "")
        return f"🌐 **Acessando:** `{url}`"

    # Fallback: show tool call cleanly
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
    return f"🔧 **{tool_name}**({args_str})"


def sanitize_tool_call_json(chunk: str) -> str:
    """
    Convert JSON tool calls to user-friendly display.

    Detects patterns like:
    - {"tool": "bash_command", "args": {"command": "..."}}
    - {"name": "bash_command", "arguments": {"command": "..."}}
    - {"functionCall": {"name": "...", "args": {...}}}

    And converts to readable format:
    ```bash
    sudo apt install ...
    ```

    Args:
        chunk: Text chunk that may contain JSON tool calls

    Returns:
        Sanitized chunk with tool calls formatted
    """
    result = chunk

    for pattern, _ in _TOOL_PATTERNS:

        def replace_tool_call(match: re.Match[str]) -> str:
            tool_name = match.group(1)
            try:
                args = json.loads(match.group(2))
            except json.JSONDecodeError:
                return match.group(0)  # Return original if parse fails

            return _format_tool_call(tool_name, args)

        result = pattern.sub(replace_tool_call, result)

    return result

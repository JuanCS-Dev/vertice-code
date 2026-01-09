"""
Tool Call Parser - Multi-Format Extraction
==========================================

Extracted from llm_client.py as part of SCALE & SUSTAIN refactoring.

Parses tool calls from LLM responses in multiple formats:
1. Native Gemini function calls (from API response)
2. Text markers [TOOL_CALL:name:args]
3. JSON tool_use blocks (Anthropic format)
4. Python-style function calls: function_name(arg='value', ...)
5. Code blocks with function calls

Author: JuanCS Dev
Date: 2025-11-27
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# KNOWN TOOLS REGISTRY
# =============================================================================

KNOWN_TOOLS: Set[str] = {
    # File operations
    "write_file",
    "read_file",
    "edit_file",
    "delete_file",
    "list_directory",
    "create_directory",
    "move_file",
    "copy_file",
    "insert_lines",
    "read_multiple_files",
    # Search
    "search_files",
    "get_directory_tree",
    "glob",
    "grep",
    # Execution
    "bash_command",
    "bash",
    "background_task",
    # Git
    "git_status",
    "git_diff",
    "git_commit",
    "git_log",
    # Web
    "web_search",
    "fetch_url",
    "web_fetch",
    "http_request",
    "download_file",
    # Context
    "restore_backup",
    "save_session",
    "get_context",
    "search_documentation",
    "package_search",
    # Terminal
    "cd",
    "ls",
    "pwd",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "touch",
    "cat",
    # Claude Code parity
    "task",
    "todo_write",
    "todo_read",
    "ask_user_question",
    "notebook_edit",
    "notebook_read",
    "enter_plan_mode",
    "exit_plan_mode",
    "image_read",
    "pdf_read",
    "screenshot_read",
    # Background execution
    "bash_output",
    "kill_shell",
    # Skills
    "skill",
    "slash_command",
    # Multi-edit
    "multi_edit",
}


# =============================================================================
# PARSING PATTERNS
# =============================================================================

# Pattern for explicit tool call markers (internal format)
MARKER_PATTERN = re.compile(r"\[TOOL_CALL:(\w+):(\{.*?\})\]", re.DOTALL)

# Pattern for Anthropic-style tool_use JSON blocks
ANTHROPIC_PATTERN = re.compile(
    r'"type"\s*:\s*"tool_use"[^}]*"name"\s*:\s*"(\w+)"[^}]*"input"\s*:\s*(\{[^}]+\})', re.DOTALL
)

# Pattern for JSON function call blocks (common LLM output)
JSON_FUNC_PATTERN = re.compile(
    r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"(?:arguments|params|parameters)"\s*:\s*(\{[^}]+\})\s*\}',
    re.DOTALL,
)

# Pattern for Gemini native function_call in JSON response
GEMINI_FC_PATTERN = re.compile(
    r'"functionCall"\s*:\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})', re.DOTALL
)

# Pattern for Python-style function calls in code blocks
# Matches: write_file(path='test.txt', content='Hello')
FUNC_PATTERN = re.compile(
    r"(\w+)\s*\(\s*"  # function_name(
    r"((?:[^()]*(?:\([^()]*\))?)*)"  # args (handles nested parens)
    r"\s*\)",
    re.DOTALL,
)

# Pattern for legacy JSON format ({"tool": "name", "args": {...}})
# This is the format we just removed from the prompt, but we keep support
# in case the model hallucinates it or for backward compatibility.
LEGACY_JSON_PATTERN = re.compile(
    r'\{\s*"tool"\s*:\s*"(\w+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})\s*\}', re.DOTALL
)

# Pattern for Vertex AI native tool call format ({"tool_call": {"name": "...", "arguments": {...}}})
# This is yielded by VertexAIProvider.stream_chat() when function calling is enabled.
VERTEX_TOOL_CALL_PATTERN = re.compile(
    r'\{\s*"tool_call"\s*:\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}\s*\}',
    re.DOTALL,
)


# =============================================================================
# TOOL CALL PARSER
# =============================================================================


class ToolCallParser:
    """
    Parse tool calls from LLM responses.

    Claude Code Parity - Multi-format parsing:
    1. Native Gemini function calls (from API response)
    2. Text markers [TOOL_CALL:name:args]
    3. JSON tool_use blocks (Anthropic format)
    4. Python-style function calls: function_name(arg='value', ...)
    5. Code blocks with function calls

    Usage:
        # From text response
        calls = ToolCallParser.extract(response_text)
        for name, args in calls:
            result = await execute_tool(name, args)

        # From native Gemini response
        calls = ToolCallParser.extract_from_native(response)

    Attributes:
        KNOWN_TOOLS: Set of recognized tool names (module-level)
        MARKER_PATTERN: Regex for [TOOL_CALL:...] format
        ANTHROPIC_PATTERN: Regex for Anthropic tool_use format
        JSON_FUNC_PATTERN: Regex for JSON function format
        FUNC_PATTERN: Regex for Python-style calls
    """

    # Class-level references to module patterns
    MARKER_PATTERN = MARKER_PATTERN
    ANTHROPIC_PATTERN = ANTHROPIC_PATTERN
    JSON_FUNC_PATTERN = JSON_FUNC_PATTERN
    LEGACY_JSON_PATTERN = LEGACY_JSON_PATTERN
    VERTEX_TOOL_CALL_PATTERN = VERTEX_TOOL_CALL_PATTERN
    FUNC_PATTERN = FUNC_PATTERN
    KNOWN_TOOLS = KNOWN_TOOLS

    @staticmethod
    def _extract_protobuf_value(value: Any) -> Any:
        """
        Extract Python value from protobuf Value type.

        Handles Gemini SDK's google.protobuf.struct_pb2.Value types.

        Args:
            value: Protobuf Value object

        Returns:
            Python native value (str, int, float, bool, list, dict, or None)
        """
        # Check for each possible value kind in protobuf Value
        if hasattr(value, "string_value") and value.HasField("string_value"):
            return value.string_value
        if hasattr(value, "number_value") and value.HasField("number_value"):
            return value.number_value
        if hasattr(value, "bool_value") and value.HasField("bool_value"):
            return value.bool_value
        if hasattr(value, "null_value") and value.HasField("null_value"):
            return None
        if hasattr(value, "list_value") and value.HasField("list_value"):
            return [ToolCallParser._extract_protobuf_value(v) for v in value.list_value.values]
        if hasattr(value, "struct_value") and value.HasField("struct_value"):
            return {
                k: ToolCallParser._extract_protobuf_value(v)
                for k, v in value.struct_value.fields.items()
            }
        # Fallback: try direct attribute access (older SDK versions)
        for attr in ("string_value", "number_value", "bool_value"):
            if hasattr(value, attr):
                try:
                    return getattr(value, attr)
                except (AttributeError, TypeError):
                    pass
        # Last resort: return as-is
        return value

    @staticmethod
    def _parse_python_args(args_str: str, tool_name: str = "") -> Dict[str, Any]:
        """
        Parse Python-style keyword and positional arguments.

        Args:
            args_str: String like "path='test.txt', content='Hello'" or "'test.txt', 'Hello'"
            tool_name: Optional tool name to map positional args

        Returns:
            Dictionary of parsed arguments
        """
        args: Dict[str, Any] = {}
        if not args_str.strip():
            return args

        # Positional argument mapping for common tools
        POSITIONAL_MAPS = {
            "write_file": ["path", "content"],
            "read_file": ["path"],
            "edit_file": ["path", "edits"],
            "delete_file": ["path"],
            "bash_command": ["command"],
            "run_command": ["command"],
            "search_files": ["pattern", "path"],
            "list_directory": ["path"],
        }

        # Use ast to safely parse
        try:
            import ast

            # Wrap in function call to parse
            fake_call = f"f({args_str})"
            tree = ast.parse(fake_call, mode="eval")
            call = tree.body

            # Handle positional arguments first
            pos_names = POSITIONAL_MAPS.get(tool_name, [])
            for i, arg in enumerate(call.args):
                if i < len(pos_names):
                    key = pos_names[i]
                    if isinstance(arg, ast.Constant):
                        args[key] = arg.value
                    elif isinstance(arg, ast.Str):  # Python 3.7 compat
                        args[key] = arg.s
                    elif isinstance(arg, ast.Num):
                        args[key] = arg.n
                    elif isinstance(arg, (ast.List, ast.Dict)):
                        args[key] = ast.literal_eval(ast.unparse(arg))

            # Handle keyword arguments
            for keyword in call.keywords:
                key = keyword.arg
                if key is None:
                    continue
                value = keyword.value
                # Extract literal values
                if isinstance(value, ast.Constant):
                    args[key] = value.value
                elif isinstance(value, ast.Str):  # Python 3.7 compat
                    args[key] = value.s
                elif isinstance(value, ast.Num):
                    args[key] = value.n
                elif isinstance(value, (ast.List, ast.Dict)):
                    args[key] = ast.literal_eval(ast.unparse(value))
        except (SyntaxError, ValueError, AttributeError) as e:
            # Fallback: regex-based parsing
            logger.debug(f"AST parsing failed, using regex fallback: {e}")
            # Match key='value' or key="value" or key=value
            kv_pattern = re.compile(r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\\S+))")
            for match in kv_pattern.finditer(args_str):
                key = match.group(1)
                value = match.group(2) or match.group(3) or match.group(4)
                args[key] = value

            # If no keyword args found, try parsing as positional
            if not args and tool_name in POSITIONAL_MAPS:
                pos_names = POSITIONAL_MAPS[tool_name]
                # Simple split on comma outside quotes
                parts = []
                current = []
                in_quotes = False
                quote_char = None
                for char in args_str:
                    if char in ('"', "'") and not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                    elif char == "," and not in_quotes:
                        parts.append("".join(current).strip().strip("\"'"))
                        current = []
                        continue
                    current.append(char)
                if current:
                    parts.append("".join(current).strip().strip("\"'"))

                for i, part in enumerate(parts):
                    if i < len(pos_names):
                        args[pos_names[i]] = part

        return args

    @staticmethod
    def extract(text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool calls from text using multi-format parsing.

        Claude Code Parity - Supports:
        1. Internal markers: [TOOL_CALL:name:{...}]
        2. Anthropic format: {"type": "tool_use", "name": "...", "input": {...}}
        3. JSON function format: {"name": "...", "arguments": {...}}
        4. Gemini functionCall: {"functionCall": {"name": "...", "args": {...}}}
        5. Python-style: function_name(arg='value', ...)

        Args:
            text: LLM response text to parse

        Returns:
            List of (tool_name, arguments) tuples, deduplicated
        """
        results: List[Tuple[str, Dict[str, Any]]] = []
        seen: Set[str] = set()  # Track (name, args_hash) to avoid duplicates

        def _add_result(name: str, args: Dict[str, Any]) -> None:
            """Add result avoiding duplicates."""
            try:
                args_hash = json.dumps(args, sort_keys=True)
            except (TypeError, ValueError):
                args_hash = str(args)
            key = f"{name}:{args_hash}"
            if key not in seen:
                seen.add(key)
                results.append((name, args))

        # 1. Check for explicit markers first (highest priority)
        marker_matches = MARKER_PATTERN.findall(text)
        for name, args_str in marker_matches:
            try:
                args = json.loads(args_str)
                _add_result(name, args)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse marker args: {e}")
                continue

        # 2. Check for Anthropic-style tool_use blocks
        anthropic_matches = ANTHROPIC_PATTERN.findall(text)
        for name, args_str in anthropic_matches:
            if name in KNOWN_TOOLS:
                try:
                    args = json.loads(args_str)
                    _add_result(name, args)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse Anthropic args: {e}")
                    continue

        # 3. Check for JSON function call format
        json_func_matches = JSON_FUNC_PATTERN.findall(text)
        for name, args_str in json_func_matches:
            if name in KNOWN_TOOLS:
                try:
                    args = json.loads(args_str)
                    _add_result(name, args)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON func args: {e}")
                    continue

        # 4. Check for Gemini native function_call format
        for match in GEMINI_FC_PATTERN.finditer(text):
            name, args_str = match.groups()
            if name in KNOWN_TOOLS:
                try:
                    args = json.loads(args_str)
                    _add_result(name, args)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse Gemini FC args: {e}")
                    continue

        # 5. Check for Python-style function calls (in code blocks)
        code_blocks = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
        search_text = "\n".join(code_blocks) if code_blocks else text

        for match in FUNC_PATTERN.finditer(search_text):
            func_name = match.group(1)
            args_str = match.group(2)

            # Only process known tools
            if func_name in KNOWN_TOOLS:
                args = ToolCallParser._parse_python_args(args_str, func_name)
                if args:  # Only add if we got valid args
                    _add_result(func_name, args)

        # 6. Check for legacy JSON format ({"tool": "name", "args": {...}})
        legacy_matches = ToolCallParser.LEGACY_JSON_PATTERN.findall(text)
        for name, args_str in legacy_matches:
            if name in KNOWN_TOOLS:
                try:
                    args = json.loads(args_str)
                    _add_result(name, args)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse legacy JSON args: {e}")
                    continue

        # 7. Check for Vertex AI native tool call format ({"tool_call": {"name": ..., "arguments": ...}})
        vertex_matches = VERTEX_TOOL_CALL_PATTERN.findall(text)
        for name, args_str in vertex_matches:
            if name in KNOWN_TOOLS:
                try:
                    args = json.loads(args_str)
                    _add_result(name, args)
                    logger.debug(f"Parsed Vertex AI tool call: {name}")
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse Vertex AI tool call args: {e}")
                    continue

        return results

    @staticmethod
    def extract_from_native(response: Any) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool calls from native Gemini API response object.

        This handles the structured function_call objects returned by the SDK,
        which is more reliable than text parsing.

        Args:
            response: Gemini API response object (GenerateContentResponse or chunk)

        Returns:
            List of (tool_name, arguments) tuples
        """
        results: List[Tuple[str, Dict[str, Any]]] = []

        # Handle list responses (batch)
        if isinstance(response, list):
            for item in response:
                results.extend(ToolCallParser.extract_from_native(item))
            return results

        # Handle candidates in response
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return results

        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue

            parts = getattr(content, "parts", [])
            for part in parts:
                # Check for function_call attribute (Gemini SDK format)
                fc = getattr(part, "function_call", None)
                if fc:
                    name = getattr(fc, "name", None)
                    if name:
                        # Convert args (protobuf Struct) to dict
                        # P0 FIX: Robust protobuf conversion with multiple fallbacks
                        args_obj = getattr(fc, "args", {})
                        args: Dict[str, Any] = {}

                        if isinstance(args_obj, dict):
                            args = args_obj
                        elif hasattr(args_obj, "items"):
                            # Direct dict-like access
                            args = dict(args_obj)
                        elif args_obj is not None:
                            # Try multiple protobuf conversion strategies
                            conversion_succeeded = False

                            # Strategy 1: google.protobuf MessageToDict
                            try:
                                from google.protobuf.json_format import MessageToDict

                                args = MessageToDict(args_obj, preserving_proto_field_name=True)
                                conversion_succeeded = True
                            except (ImportError, TypeError, ValueError, AttributeError):
                                pass

                            # Strategy 2: Direct field access (Gemini SDK specific)
                            if not conversion_succeeded:
                                try:
                                    # Gemini SDK Struct has .fields attribute
                                    if hasattr(args_obj, "fields"):
                                        args = {
                                            k: self._extract_protobuf_value(v)
                                            for k, v in args_obj.fields.items()
                                        }
                                        conversion_succeeded = True
                                except (AttributeError, TypeError):
                                    pass

                            # Strategy 3: __dict__ access
                            if not conversion_succeeded:
                                try:
                                    if hasattr(args_obj, "__dict__"):
                                        args = {
                                            k: v
                                            for k, v in args_obj.__dict__.items()
                                            if not k.startswith("_")
                                        }
                                        conversion_succeeded = True
                                except (AttributeError, TypeError):
                                    pass

                            # Strategy 4: JSON serialization roundtrip
                            if not conversion_succeeded:
                                try:
                                    import json

                                    if hasattr(args_obj, "SerializeToString"):
                                        # Try to serialize and parse
                                        from google.protobuf.json_format import MessageToJson

                                        json_str = MessageToJson(args_obj)
                                        args = json.loads(json_str)
                                        conversion_succeeded = True
                                except (ImportError, TypeError, ValueError, AttributeError):
                                    pass

                            # CRITICAL: Log warning if all strategies failed
                            if not conversion_succeeded:
                                logger.warning(
                                    f"All protobuf conversion strategies failed for tool '{name}'. "
                                    f"Args type: {type(args_obj).__name__}. "
                                    "Tool call will execute with empty arguments."
                                )
                                args = {}

                        # Check if known tool (case-insensitive)
                        if name in KNOWN_TOOLS or name.lower() in KNOWN_TOOLS:
                            results.append((name, args))

        return results

    @staticmethod
    def remove(text: str) -> str:
        """
        Remove tool call markers from text for clean display.

        Args:
            text: Text containing tool call markers

        Returns:
            Cleaned text without markers
        """
        text = MARKER_PATTERN.sub("", text)

        # Remove legacy JSON patterns
        text = LEGACY_JSON_PATTERN.sub("", text)

        # Also remove code blocks containing only tool calls
        lines = text.split("\n")
        clean_lines: List[str] = []
        in_tool_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_tool_block = not in_tool_block
                continue
            if in_tool_block:
                # Check if this line is just a tool call
                if any(tool in line for tool in KNOWN_TOOLS):
                    continue
            clean_lines.append(line)

        return "\n".join(clean_lines).strip()

    @staticmethod
    def format_marker(name: str, args: Dict[str, Any]) -> str:
        """
        Create a tool call marker string.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            Formatted marker string like [TOOL_CALL:name:{...}]
        """
        return f"[TOOL_CALL:{name}:{json.dumps(args)}]"

    @staticmethod
    def is_known_tool(name: str) -> bool:
        """
        Check if a tool name is in the known tools registry.

        Args:
            name: Tool name to check

        Returns:
            True if tool is known
        """
        return name in KNOWN_TOOLS or name.lower() in KNOWN_TOOLS

    @classmethod
    def register_tool(cls, name: str) -> None:
        """
        Register a new tool name.

        Args:
            name: Tool name to register
        """
        KNOWN_TOOLS.add(name)
        logger.debug(f"Registered tool: {name}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ToolCallParser",
    "KNOWN_TOOLS",
    "MARKER_PATTERN",
    "ANTHROPIC_PATTERN",
    "JSON_FUNC_PATTERN",
    "GEMINI_FC_PATTERN",
    "FUNC_PATTERN",
]

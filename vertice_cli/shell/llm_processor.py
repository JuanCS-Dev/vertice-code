"""
LLM Processor - Handles LLM interactions for the shell.

Responsibilities:
- Building prompts with context
- Processing LLM responses
- Parsing tool calls from responses
- Managing conversation flow

Design Principles:
- Single Responsibility: Only LLM interaction logic
- Dependency Injection: LLM client passed in
- Testable: Easy to mock LLM client
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tools.base import ToolRegistry
    from ..core.conversation import ConversationManager

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Parsed LLM response."""

    text: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    is_tool_response: bool = False


@dataclass
class ProcessingContext:
    """Context for LLM processing."""

    cwd: str
    modified_files: List[str] = field(default_factory=list)
    read_files: List[str] = field(default_factory=list)
    conversation_turns: int = 0
    context_usage_percent: float = 0.0


class LLMProcessor:
    """
    Processes user input through LLM to get tool calls or text responses.

    This class encapsulates all LLM interaction logic:
    - System prompt generation
    - Response parsing
    - Tool call extraction
    """

    def __init__(
        self,
        llm_client: Any,
        registry: "ToolRegistry",
        conversation: "ConversationManager",
    ):
        self.llm = llm_client
        self.registry = registry
        self.conversation = conversation

    def build_system_prompt(
        self,
        context: ProcessingContext,
    ) -> str:
        """Build system prompt with tool schemas and context."""
        tool_schemas = self.registry.get_schemas()

        tool_list = []
        for schema in tool_schemas:
            tool_list.append(f"- {schema['name']}: {schema['description']}")

        return f"""You are an AI code assistant with access to tools for file operations, git, search, and execution.

Available tools ({len(tool_schemas)} total):
{chr(10).join(tool_list)}

Current context:
- Working directory: {context.cwd}
- Modified files: {context.modified_files if context.modified_files else 'none'}
- Read files: {context.read_files if context.read_files else 'none'}
- Conversation turns: {context.conversation_turns}
- Context usage: {context.context_usage_percent:.0%}

INSTRUCTIONS:
1. Analyze the user's request (consider conversation history)
2. If it requires tools, respond ONLY with a JSON array of tool calls
3. If no tools needed, respond with helpful text

Tool call format:
[
  {{"tool": "tool_name", "args": {{"param": "value"}}}}
]

Examples:
User: "read api.py"
Response: [{{"tool": "readfile", "args": {{"path": "api.py"}}}}]

User: "show git status"
Response: [{{"tool": "gitstatus", "args": {{}}}}]

User: "search for TODO in python files"
Response: [{{"tool": "searchfiles", "args": {{"pattern": "TODO", "file_pattern": "*.py"}}}}]

User: "what time is it?"
Response: I don't have a tool to check the current time, but I can help you with code-related tasks."""

    async def process(
        self,
        user_input: str,
        context: ProcessingContext,
    ) -> LLMResponse:
        """
        Process user input through LLM.

        Args:
            user_input: User's message
            context: Current processing context

        Returns:
            LLMResponse with text and/or tool calls
        """
        # Start conversation turn
        turn = self.conversation.start_turn(user_input)

        try:
            # Build messages
            system_prompt = self.build_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history
            context_messages = self.conversation.get_context_for_llm(include_last_n=3)
            messages.extend(context_messages)

            # Add current input
            messages.append({"role": "user", "content": user_input})

            # Call LLM
            response = await self.llm.generate_async(
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
            )

            # Parse response
            response_text = response.get("content", "")
            tokens_used = response.get("tokens_used", len(response_text) // 4)

            # Track response
            self.conversation.add_llm_response(turn, response_text, tokens_used=tokens_used)

            # Try to parse tool calls
            tool_calls = self._parse_tool_calls(response_text)

            if tool_calls:
                self.conversation.add_tool_calls(turn, tool_calls)
                return LLMResponse(
                    text=response_text,
                    tool_calls=tool_calls,
                    tokens_used=tokens_used,
                    is_tool_response=True,
                )

            return LLMResponse(
                text=response_text,
                tokens_used=tokens_used,
                is_tool_response=False,
            )

        except Exception as e:
            turn.error = str(e)
            turn.error_category = "system"
            logger.error(f"LLM processing error: {e}")
            raise

    def _parse_tool_calls(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response.

        Looks for JSON array in response text.

        Args:
            response_text: Raw LLM response

        Returns:
            List of tool call dicts or empty list
        """
        try:
            if "[" not in response_text or "]" not in response_text:
                return []

            start = response_text.index("[")
            end = response_text.rindex("]") + 1
            json_str = response_text[start:end]

            tool_calls = json.loads(json_str)

            if isinstance(tool_calls, list) and tool_calls:
                # Validate structure
                for call in tool_calls:
                    if not isinstance(call, dict):
                        return []
                    if "tool" not in call:
                        return []
                return tool_calls

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Response is not tool calls JSON: {e}")

        return []

    def build_rich_context_prompt(
        self,
        user_input: str,
        rich_context: Dict[str, Any],
    ) -> str:
        """
        Build a prompt with rich context for command suggestions.

        Args:
            user_input: User's request
            rich_context: Context dict from RichContextBuilder

        Returns:
            Formatted prompt string
        """
        # Format recent files
        recent_files_str = ", ".join(
            [str(f) if isinstance(f, dict) else f for f in rich_context.get("recent_files", [])[:5]]
        )

        return f"""User request: {user_input}

Context:
- Project: {rich_context.get('cwd', '.')}
- Recent files: {recent_files_str}
- Git status: {rich_context.get('git_status', 'N/A')}

Suggest ONE shell command to accomplish this task.
Output ONLY the command, no explanation, no markdown."""


class CommandExtractor:
    """Extracts shell commands from LLM responses."""

    def extract(self, llm_response: str) -> str:
        """
        Extract command from LLM response.

        Handles:
        - Markdown code blocks
        - Shell prompt prefixes
        - Multi-line responses

        Args:
            llm_response: Raw LLM response

        Returns:
            Extracted command string
        """
        import re

        if not llm_response or not isinstance(llm_response, str):
            return "# Could not extract command"

        # Remove markdown code blocks
        code_block = re.search(
            r"```(?:bash|sh)?\s*\n?(.*?)\n?```",
            llm_response,
            re.DOTALL,
        )
        if code_block:
            return code_block.group(1).strip()

        # Process lines
        lines = llm_response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove shell prompt prefix
                if line.startswith("$"):
                    line = line[1:].strip()
                if line:
                    return line

        return llm_response.strip() if llm_response else "# Empty response"


class FallbackSuggester:
    """
    Provides command suggestions when LLM is unavailable.

    Uses pattern matching for common requests.
    """

    PATTERNS = {
        ("large file", "big file"): "find . -type f -size +100M",
        ("process", "memory"): "ps aux --sort=-%mem | head -10",
        ("disk", "space", "usage"): "df -h",
        ("list", "file"): "ls -lah",
        ("git", "status"): "git status",
        ("git", "diff"): "git diff",
        ("git", "log"): "git log --oneline -10",
    }

    def suggest(self, user_request: str) -> str:
        """
        Generate fallback command suggestion.

        Args:
            user_request: User's natural language request

        Returns:
            Suggested command or comment
        """
        req_lower = user_request.lower()

        for keywords, command in self.PATTERNS.items():
            if all(kw in req_lower for kw in keywords):
                return command

        # Truncate huge inputs
        max_display = 100
        truncated = (
            user_request[:max_display] + "..." if len(user_request) > max_display else user_request
        )
        return f"# Could not parse: {truncated}"

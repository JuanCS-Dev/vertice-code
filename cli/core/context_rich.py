"""
Rich Context Builder - Wrapper for enhanced context functionality.

Provides a class-based interface for building rich context information
for LLM interactions.
"""

from typing import Any, Dict, Optional

from ..intelligence.context_enhanced import (
    build_rich_context,
    RichContext,
)


class RichContextBuilder:
    """
    Builder for rich context information.

    Wraps the functional API from context_enhanced into a class-based interface
    for integration with InteractiveShell.
    """

    def __init__(self, working_dir: str = ".") -> None:
        """Initialize builder with optional working directory."""
        self.working_dir = working_dir
        self._cached_context: Optional[RichContext] = None

    def build_rich_context(
        self,
        user_message: str = "",
        session_history: Optional[list] = None,
    ) -> RichContext:
        """
        Build rich context for the current environment.

        Args:
            user_message: Current user message
            session_history: Conversation history

        Returns:
            RichContext with workspace, git, and session info
        """
        self._cached_context = build_rich_context(
            user_message=user_message,
            session_history=session_history or [],
            working_dir=self.working_dir,
        )
        return self._cached_context

    def format_context_for_llm(self, context: Optional[RichContext] = None) -> str:
        """
        Format context into a string suitable for LLM system prompt.

        Args:
            context: RichContext to format (uses cached if None)

        Returns:
            Formatted context string
        """
        ctx = context or self._cached_context
        if ctx is None:
            ctx = self.build_rich_context()

        parts = []

        # Workspace info
        if ctx.workspace:
            ws = ctx.workspace
            parts.append(f"Project: {ws.project_name}")
            if ws.languages:
                parts.append(f"Languages: {', '.join(ws.languages)}")
            if ws.frameworks:
                parts.append(f"Frameworks: {', '.join(ws.frameworks)}")

        # Git info
        if ctx.git:
            git = ctx.git
            parts.append(f"Git branch: {git.branch}")
            if git.has_changes:
                parts.append(f"Modified files: {git.modified_count}")

        return "\n".join(parts) if parts else "No context available"

    def invalidate_cache(self) -> None:
        """Clear cached context."""
        self._cached_context = None


__all__ = ["RichContextBuilder"]

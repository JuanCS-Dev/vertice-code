"""
ExplorerFormatter - Format file exploration and analysis results.

Handles codebase exploration outputs with relevant files,
dependencies, and token estimates.
"""

from typing import Any, AsyncIterator, List


class ExplorerFormatter:
    """
    Format ExplorerAgent file exploration and analysis results.

    Expected data structure:
        {
            "relevant_files": List[str | {path, relevance, reason, snippet}],
            "context_summary": str,
            "dependencies": List[str | {from, to, type}],
            "token_estimate": int
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains file exploration results ('relevant_files' key)."""
        return isinstance(data, dict) and 'relevant_files' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format file exploration with summaries, files, dependencies, and token counts."""
        if data.get('context_summary'):
            yield f"{data['context_summary']}\n\n"

        relevant_files = data.get('relevant_files', [])
        if relevant_files:
            yield "**Relevant Files:**\n"
            async for chunk in ExplorerFormatter._format_files(relevant_files):
                yield chunk
        else:
            yield "⚠️ No relevant files found for this query.\n"

        deps = data.get('dependencies', [])
        if deps:
            yield "\n**Dependencies:**\n"
            for d in deps:
                if isinstance(d, dict):
                    yield f"- `{d.get('from', '')}` → `{d.get('to', '')}` ({d.get('type', '')})\n"
                else:
                    yield f"- {d}\n"

        if data.get('token_estimate'):
            yield f"\n📊 *Token estimate: ~{data['token_estimate']} tokens*\n"

    @staticmethod
    async def _format_files(files: List[Any]) -> AsyncIterator[str]:
        """Format file list with relevance badges and optional code snippets."""
        for f in files:
            if isinstance(f, dict):
                path = f.get('path', 'unknown')
                relevance = f.get('relevance', '')
                reason = f.get('reason', '')

                relevance_badge = f" [{relevance}]" if relevance else ""
                reason_text = f" - {reason}" if reason else ""
                yield f"- `{path}`{relevance_badge}{reason_text}\n"

                snippet = f.get('snippet', '')
                if snippet:
                    preview = snippet[:200].strip()
                    if len(snippet) > 200:
                        preview += "..."
                    yield f"  ```\n  {preview}\n  ```\n"
            else:
                yield f"- `{f}`\n"

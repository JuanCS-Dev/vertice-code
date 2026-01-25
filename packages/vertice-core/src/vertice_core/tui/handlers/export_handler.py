"""
Export Handler - Markdown export with Frontmatter
===============================================

Handler para export de conversas em Markdown com Frontmatter YAML.
Suporta templates formatted (bonito) e raw (dados brutos).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from vertice_core.tui.widgets.session_tabs import SessionData


class ExportHandler:
    """
    Handles conversation export to Markdown with YAML frontmatter.

    Supports:
    - Formatted template (beautiful, readable)
    - Raw template (data dump for analysis)
    - YAML frontmatter with metadata
    - Session history with timestamps
    """

    def __init__(self):
        self.templates = {
            "formatted": self._format_template_formatted,
            "raw": self._format_template_raw,
        }

    def export_session(
        self, session: SessionData, template: str = "formatted", output_path: Optional[str] = None
    ) -> str:
        """
        Export session to Markdown file.

        Args:
            session: SessionData to export
            template: Template type ("formatted" or "raw")
            output_path: Optional output path, auto-generated if None

        Returns:
            Path to exported file
        """
        if template not in self.templates:
            raise ValueError(f"Unknown template: {template}")

        # Generate filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_title = session.title.replace(" ", "_").replace("/", "_")
            output_path = f"vertice_export_{session_title}_{timestamp}.md"

        # Generate content
        formatter = self.templates[template]
        content = formatter(session)

        # Write file
        Path(output_path).write_text(content, encoding="utf-8")

        return output_path

    def export_multiple_sessions(
        self, sessions: List[SessionData], template: str = "formatted", output_dir: str = "exports"
    ) -> List[str]:
        """
        Export multiple sessions to individual files.

        Args:
            sessions: List of SessionData to export
            template: Template type
            output_dir: Directory for exports

        Returns:
            List of exported file paths
        """
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        exported_files = []
        for session in sessions:
            filename = f"session_{session.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            output_path = os.path.join(output_dir, filename)

            try:
                exported_file = self.export_session(session, template, output_path)
                exported_files.append(exported_file)
            except Exception as e:
                print(f"Failed to export session {session.id}: {e}")

        return exported_files

    def _format_template_formatted(self, session: SessionData) -> str:
        """Format session as beautiful, readable Markdown."""
        # YAML Frontmatter
        frontmatter = self._generate_frontmatter(session, "formatted")

        # Session header
        header = f"# {session.title}\n\n"
        header += f"**Session ID:** `{session.id}`\n"
        header += f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"**Last Updated:** {session.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"**Total Messages:** {len(session.messages)}\n\n"

        # Context (if available)
        if session.context:
            header += "## Context\n\n"
            for key, value in session.context.items():
                header += f"- **{key}:** {value}\n"
            header += "\n"

        # Messages
        messages_md = "## Conversation\n\n"

        for i, message in enumerate(session.messages, 1):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")

            # Format role as header
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(role, "❓")

            messages_md += f"### {role_emoji} {role.title()} ({i})\n\n"
            messages_md += f"**Timestamp:** {timestamp}\n\n"
            messages_md += f"{content}\n\n"
            messages_md += "---\n\n"

        return frontmatter + header + messages_md

    def _format_template_raw(self, session: SessionData) -> str:
        """Format session as raw data dump for analysis."""
        # YAML Frontmatter
        frontmatter = self._generate_frontmatter(session, "raw")

        # Raw JSON-like dump
        raw_data = "## Raw Session Data\n\n"
        raw_data += "```json\n"
        raw_data += "{\n"
        raw_data += f'  "id": "{session.id}",\n'
        raw_data += f'  "title": "{session.title}",\n'
        raw_data += f'  "created_at": "{session.created_at.isoformat()}",\n'
        raw_data += f'  "last_updated": "{session.last_updated.isoformat()}",\n'
        raw_data += f'  "message_count": {len(session.messages)},\n'
        raw_data += '  "context": {\n'

        # Context
        for key, value in session.context.items():
            raw_data += f'    "{key}": "{value}",\n'
        raw_data = raw_data.rstrip(",\n") + "\n  },\n"

        # Messages
        raw_data += '  "messages": [\n'
        for message in session.messages:
            raw_data += "    {\n"
            raw_data += f'      "role": "{message.get("role", "unknown")}",\n'
            raw_data += f'      "content": {repr(message.get("content", ""))},\n'
            raw_data += f'      "timestamp": "{message.get("timestamp", "")}"\n'
            raw_data += "    },\n"
        raw_data = raw_data.rstrip(",\n") + "\n  ]\n"
        raw_data += "}\n"
        raw_data += "```\n\n"

        # Basic statistics
        raw_data += "## Statistics\n\n"
        raw_data += (
            f"- **Total Characters:** {sum(len(m.get('content', '')) for m in session.messages)}\n"
        )
        raw_data += (
            f"- **User Messages:** {sum(1 for m in session.messages if m.get('role') == 'user')}\n"
        )
        raw_data += f"- **Assistant Messages:** {sum(1 for m in session.messages if m.get('role') == 'assistant')}\n"

        return frontmatter + raw_data

    def _generate_frontmatter(self, session: SessionData, template: str) -> str:
        """Generate YAML frontmatter for the Markdown file."""
        frontmatter = "---\n"
        frontmatter += f'title: "{session.title}"\n'
        frontmatter += f'session_id: "{session.id}"\n'
        frontmatter += f'created_at: "{session.created_at.isoformat()}"\n'
        frontmatter += f'last_updated: "{session.last_updated.isoformat()}"\n'
        frontmatter += f"message_count: {len(session.messages)}\n"
        frontmatter += f'export_template: "{template}"\n'
        frontmatter += f'export_timestamp: "{datetime.now().isoformat()}"\n'
        frontmatter += 'tool: "Vertice-Code TUI"\n'
        frontmatter += 'version: "1.1"\n'

        # Add tags based on content
        tags = []
        all_content = " ".join([m.get("content", "") for m in session.messages])

        if "python" in all_content.lower() or "def " in all_content or "import " in all_content:
            tags.append("python")
        if "javascript" in all_content.lower() or "function" in all_content:
            tags.append("javascript")
        if "error" in all_content.lower() or "exception" in all_content.lower():
            tags.append("debugging")
        if "test" in all_content.lower():
            tags.append("testing")

        if tags:
            tag_list = ", ".join(f'"{tag}"' for tag in tags)
            frontmatter += f"tags: [{tag_list}]\n"

        frontmatter += "---\n\n"

        return frontmatter


# Global instance
_export_handler = None


def get_export_handler() -> ExportHandler:
    """Get global export handler instance."""
    global _export_handler
    if _export_handler is None:
        _export_handler = ExportHandler()
    return _export_handler

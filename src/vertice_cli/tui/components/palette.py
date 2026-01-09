"""
Command Palette - Cmd+K style command launcher with fuzzy search.

Phase 9 Visual Refresh:
- Unicode minimalista icons
- 20 agents (14 CLI + 6 Core)
- Slate/Blue accent colors

Inspiration:
- VSCode Command Palette (Cmd+K)
- Sublime Text Command Palette
- Apple Spotlight
- GitHub Command Palette

Philosophy:
- Instant feedback (< 50ms)
- Fuzzy search (forgiving)
- Keyboard-first (accessible)
- Categories with icons
- Recent commands (smart)

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from typing import List, Optional, Callable, Dict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from ..theme import COLORS
from ..styles import PRESET_STYLES
from ..wisdom import get_random_verse


class CommandCategory(Enum):
    """Command categories."""

    FILE = "file"
    EDIT = "edit"
    SEARCH = "search"
    GIT = "git"
    TOOLS = "tools"
    VIEW = "view"
    HELP = "help"
    SYSTEM = "system"
    AGENTS = "agents"


# Category icons and colors (Phase 9: Unicode minimalista)
CATEGORY_CONFIG = {
    CommandCategory.FILE: {"icon": "▪", "color": COLORS["accent_blue"]},
    CommandCategory.EDIT: {"icon": "▸", "color": COLORS["accent_green"]},
    CommandCategory.SEARCH: {"icon": "○", "color": COLORS["accent_yellow"]},
    CommandCategory.GIT: {"icon": "⎇", "color": COLORS["accent_purple"]},
    CommandCategory.TOOLS: {"icon": "⚡", "color": COLORS["accent_blue"]},
    CommandCategory.VIEW: {"icon": "◎", "color": COLORS["text_secondary"]},
    CommandCategory.HELP: {"icon": "ℹ", "color": COLORS["accent_yellow"]},
    CommandCategory.SYSTEM: {"icon": "⊡", "color": COLORS["text_secondary"]},
    CommandCategory.AGENTS: {"icon": "◆", "color": "#22D3EE"},
}


@dataclass
class Command:
    """Command definition for palette."""

    id: str
    title: str
    description: str
    category: CommandCategory
    keywords: List[str] = field(default_factory=list)
    keybinding: Optional[str] = None
    action: Optional[Callable] = None
    enabled: bool = True
    last_used: Optional[datetime] = None
    use_count: int = 0

    @property
    def search_text(self) -> str:
        """Get combined text for searching."""
        parts = [
            self.title.lower(),
            self.description.lower(),
            self.category.value.lower(),
        ] + [k.lower() for k in self.keywords]
        return " ".join(parts)

    @property
    def display_title(self) -> Text:
        """Get formatted title with category icon."""
        config = CATEGORY_CONFIG[self.category]
        text = Text()
        text.append(f"{config['icon']} ", style=config["color"])
        text.append(self.title, style=PRESET_STYLES.EMPHASIS)

        if self.keybinding:
            text.append(f"  [{self.keybinding}]", style=PRESET_STYLES.TERTIARY)

        return text

    def mark_used(self) -> None:
        """Mark command as used (for recency tracking)."""
        self.last_used = datetime.now()
        self.use_count += 1


class FuzzyMatcher:
    """Fuzzy string matching for command search."""

    def score(self, text: str, query: str) -> float:
        """Calculate fuzzy match score (0.0 = no match, 1.0 = perfect)."""
        if not query:
            return 1.0

        text = text.lower()
        query = query.lower()

        if query in text:
            position_score = 1.0 - (text.index(query) / len(text))
            return 0.8 + (0.2 * position_score)

        text_idx = 0
        query_idx = 0
        matches = []

        while query_idx < len(query) and text_idx < len(text):
            if text[text_idx] == query[query_idx]:
                matches.append(text_idx)
                query_idx += 1
            text_idx += 1

        if query_idx < len(query):
            return 0.0

        if not matches:
            return 0.0

        base_score = len(matches) / len(text)
        position_score = 1.0 - (matches[0] / len(text))

        consecutive_count = 0
        for i in range(1, len(matches)):
            if matches[i] == matches[i - 1] + 1:
                consecutive_count += 1
        consecutive_score = consecutive_count / max(len(matches) - 1, 1)

        final_score = base_score * 0.4 + position_score * 0.3 + consecutive_score * 0.3

        return min(final_score, 1.0)

    def matches(self, text: str, query: str, threshold: float = 0.3) -> bool:
        """Check if text matches query."""
        return self.score(text, query) >= threshold


class CommandPalette:
    """Command palette with fuzzy search and keyboard navigation."""

    def __init__(self) -> None:
        """Initialize command palette."""
        self.commands: Dict[str, Command] = {}
        self.matcher = FuzzyMatcher()
        self.recent_limit = 5

    def add_command(self, command: Command) -> None:
        """Add command to palette."""
        self.commands[command.id] = command

    def add_commands(self, commands: List[Command]) -> None:
        """Add multiple commands."""
        for cmd in commands:
            self.add_command(cmd)

    def get_command(self, command_id: str) -> Optional[Command]:
        """Get command by ID."""
        return self.commands.get(command_id)

    def search(
        self,
        query: str,
        limit: int = 10,
        category: Optional[CommandCategory] = None,
        include_recent: bool = True,
    ) -> List[Command]:
        """Search commands with fuzzy matching."""
        if not query.strip():
            if include_recent:
                return self.get_recent_commands(limit)
            return list(self.commands.values())[:limit]

        candidates = self.commands.values()
        if category:
            candidates = [c for c in candidates if c.category == category]

        scored = []
        for cmd in candidates:
            if not cmd.enabled:
                continue
            score = self.matcher.score(cmd.search_text, query)
            if score > 0.0:
                scored.append((score, cmd))

        scored.sort(key=lambda x: x[0], reverse=True)

        if include_recent:
            recent_ids = {cmd.id for cmd in self.get_recent_commands()}
            boosted = []
            for score, cmd in scored:
                if cmd.id in recent_ids:
                    score *= 1.2
                boosted.append((score, cmd))
            scored = boosted
            scored.sort(key=lambda x: x[0], reverse=True)

        return [cmd for _, cmd in scored[:limit]]

    def get_recent_commands(self, limit: int = 5) -> List[Command]:
        """Get recently used commands."""
        recent = [cmd for cmd in self.commands.values() if cmd.last_used]
        recent.sort(key=lambda c: c.last_used, reverse=True)
        return recent[:limit]

    def execute_command(self, command_id: str) -> bool:
        """Execute command by ID."""
        cmd = self.get_command(command_id)
        if not cmd or not cmd.enabled:
            return False

        cmd.mark_used()

        if cmd.action:
            try:
                cmd.action()
                return True
            except (TypeError, ValueError, RuntimeError):
                return False

        return True

    def render_search_results(
        self,
        query: str,
        selected_index: int = 0,
        limit: int = 8,
    ) -> Panel:
        """Render search results as panel."""
        results = self.search(query, limit=limit)

        if not results:
            content = Text()
            content.append("No commands found", style=PRESET_STYLES.TERTIARY)
            verse = get_random_verse(60)
            content.append(f"\n\n{verse}", style=PRESET_STYLES.DIM)

            return Panel(
                Align.center(content),
                title="[bold]Command Palette[/bold]",
                subtitle=f"[dim]{query}[/dim]" if query else None,
                border_style=COLORS["border_muted"],
                padding=(1, 2),
            )

        table = Table.grid(padding=(0, 1))
        table.add_column("", width=2)
        table.add_column("Command")
        table.add_column("Description")

        for idx, cmd in enumerate(results):
            indicator = "▶" if idx == selected_index else " "
            title = cmd.display_title
            desc = Text(cmd.description, style=PRESET_STYLES.TERTIARY)

            if idx == selected_index:
                table.add_row(
                    Text(indicator, style=PRESET_STYLES.SUCCESS),
                    title,
                    desc,
                    style=PRESET_STYLES.HIGHLIGHT,
                )
            else:
                table.add_row(indicator, title, desc)

        query_text = Text()
        query_text.append("Search: ", style=PRESET_STYLES.SECONDARY)
        query_text.append(
            query or "(type to search)",
            style=PRESET_STYLES.EMPHASIS if query else PRESET_STYLES.DIM,
        )

        return Panel(
            table,
            title="[bold]⌘ Command Palette[/bold]",
            subtitle=query_text,
            border_style=COLORS["accent_blue"],
            padding=(1, 2),
        )


# =============================================================================
# DEFAULT COMMANDS - Phase 9: 20 agents
# =============================================================================

DEFAULT_COMMANDS = [
    # File
    Command(
        "file.open", "Open File", "Open a file", CommandCategory.FILE, ["read", "load"], "Ctrl+O"
    ),
    Command(
        "file.save", "Save File", "Save current file", CommandCategory.FILE, ["write"], "Ctrl+S"
    ),
    Command(
        "file.tree",
        "File Tree",
        "Display directory tree",
        CommandCategory.FILE,
        ["directory", "folder"],
    ),
    # Search
    Command(
        "search.files",
        "Search Files",
        "Search by name",
        CommandCategory.SEARCH,
        ["find", "locate"],
        "Ctrl+P",
    ),
    Command(
        "search.content",
        "Search Content",
        "Search in files",
        CommandCategory.SEARCH,
        ["grep", "text"],
        "Ctrl+Shift+F",
    ),
    # Git
    Command(
        "git.status", "Git Status", "Repository status", CommandCategory.GIT, ["vcs", "version"]
    ),
    Command("git.diff", "Git Diff", "Show changes", CommandCategory.GIT, ["changes"]),
    Command("git.commit", "Git Commit", "Commit staged", CommandCategory.GIT, ["save"]),
    # Tools
    Command(
        "tools.terminal",
        "Terminal",
        "Open terminal",
        CommandCategory.TOOLS,
        ["shell", "bash"],
        "Ctrl+`",
    ),
    # View
    Command(
        "view.metrics",
        "Metrics",
        "LEI, HRI, CPI metrics",
        CommandCategory.VIEW,
        ["constitutional", "stats"],
    ),
    # Help
    Command(
        "help.commands",
        "All Commands",
        "List commands",
        CommandCategory.HELP,
        ["list", "palette"],
        "Ctrl+Shift+P",
    ),
    # CLI Agents (14)
    Command(
        "agent.planner",
        "Planner Agent",
        "GOAP planning",
        CommandCategory.AGENTS,
        ["plan", "goap", "decomposition"],
    ),
    Command(
        "agent.executor",
        "Executor Agent",
        "Secure execution",
        CommandCategory.AGENTS,
        ["run", "bash", "python"],
    ),
    Command(
        "agent.architect",
        "Architect Agent",
        "Architecture analysis",
        CommandCategory.AGENTS,
        ["design", "system", "veto"],
    ),
    Command(
        "agent.reviewer",
        "Reviewer Agent",
        "Code review",
        CommandCategory.AGENTS,
        ["review", "pr", "quality"],
    ),
    Command(
        "agent.explorer",
        "Explorer Agent",
        "Codebase exploration",
        CommandCategory.AGENTS,
        ["search", "navigate", "find"],
    ),
    Command(
        "agent.refactorer",
        "Refactorer Agent",
        "Code refactoring",
        CommandCategory.AGENTS,
        ["refactor", "improve", "clean"],
    ),
    Command(
        "agent.testing",
        "Testing Agent",
        "Test generation",
        CommandCategory.AGENTS,
        ["test", "coverage", "pytest"],
    ),
    Command(
        "agent.security",
        "Security Agent",
        "OWASP analysis",
        CommandCategory.AGENTS,
        ["scan", "audit", "vulnerabilities"],
    ),
    Command(
        "agent.documentation",
        "Documentation Agent",
        "Docs generation",
        CommandCategory.AGENTS,
        ["docs", "docstrings", "readme"],
    ),
    Command(
        "agent.performance",
        "Performance Agent",
        "Profiling",
        CommandCategory.AGENTS,
        ["profile", "optimize", "benchmark"],
    ),
    Command(
        "agent.devops",
        "DevOps Agent",
        "Infrastructure",
        CommandCategory.AGENTS,
        ["docker", "kubernetes", "deploy"],
    ),
    Command(
        "agent.justica",
        "Justica Agent",
        "Governance",
        CommandCategory.AGENTS,
        ["evaluate", "approve", "block"],
    ),
    Command(
        "agent.sofia",
        "Sofia Agent",
        "Ethical counsel",
        CommandCategory.AGENTS,
        ["counsel", "ethics", "wisdom"],
    ),
    Command(
        "agent.data",
        "Data Agent",
        "Database analysis",
        CommandCategory.AGENTS,
        ["database", "schema", "sql"],
    ),
    Command(
        "agent.jules",
        "Jules Agent",
        "Google Jules AI coding",
        CommandCategory.AGENTS,
        ["google", "external", "async", "complex"],
        "Ctrl+J",
    ),
    Command(
        "jules.monitor",
        "Jules Monitor",
        "Monitor Jules session",
        CommandCategory.AGENTS,
        ["observe", "status", "track"],
        "Ctrl+Shift+J",
    ),
    # Core Agents (6) - names must match registry (with _core suffix)
    Command(
        "agent.orchestrator_core",
        "Orchestrator (Core)",
        "Multi-agent coordination",
        CommandCategory.AGENTS,
        ["orchestration", "handoff", "autonomy"],
    ),
    Command(
        "agent.coder_core",
        "Coder (Core)",
        "Darwin-Godel evolution",
        CommandCategory.AGENTS,
        ["code", "generation", "darwin"],
    ),
    Command(
        "agent.reviewer_core",
        "Reviewer (Core)",
        "Deep-think review",
        CommandCategory.AGENTS,
        ["deep", "metacognition"],
    ),
    Command(
        "agent.architect_core",
        "Architect (Core)",
        "Agentic RAG design",
        CommandCategory.AGENTS,
        ["rag", "patterns"],
    ),
    Command(
        "agent.researcher_core",
        "Researcher (Core)",
        "Three-loop learning",
        CommandCategory.AGENTS,
        ["research", "knowledge", "synthesis"],
    ),
    Command(
        "agent.devops_core",
        "DevOps (Core)",
        "Incident handler",
        CommandCategory.AGENTS,
        ["incident", "infrastructure"],
    ),
]


def create_default_palette() -> CommandPalette:
    """Create palette with default commands."""
    palette = CommandPalette()
    palette.add_commands(DEFAULT_COMMANDS)
    return palette


if __name__ == "__main__":
    console = Console()
    palette = create_default_palette()
    for query in ["", "agent", "git", "planner"]:
        console.print(palette.render_search_results(query, selected_index=0))
        console.print()

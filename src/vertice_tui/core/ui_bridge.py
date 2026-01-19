"""
UI Bridge Module - Command Palette and Autocomplete
====================================================

Extracted from Bridge GOD CLASS (Nov 2025 Refactoring).

Features:
- CommandPaletteBridge: VS Code-style command discovery
- MinimalCommandPalette: Fallback implementation
- AutocompleteBridge: Fuzzy matching with @ file picker
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .tools_bridge import ToolBridge


class MinimalCommandPalette:
    """Minimal fallback command palette."""

    def __init__(self):
        self.commands = []
        self.recent_commands = []

    def get_suggestions(self, query: str, max_results: int = 10) -> List[Dict]:
        return []

    def execute(self, command_id: str):
        return {"status": "no_handler", "message": "Minimal palette"}

    def register_command(self, command):
        self.commands.append(command)


class CommandPaletteBridge:
    """
    Bridge to CommandPalette with fuzzy search.

    Provides command discovery and execution.
    """

    def __init__(self):
        self._palette = None

    @property
    def palette(self):
        """Lazy load command palette."""
        if self._palette is None:
            try:
                from vertice_cli.ui.command_palette import CommandPalette, Command

                self._palette = CommandPalette()

                # Register ALL 20 agent commands (14 CLI + 6 Core)
                agent_commands = [
                    # CLI Agents (14)
                    ("planner", "Planner", "GOAP planning", "agent"),
                    ("executor", "Executor", "Secure code execution", "agent"),
                    ("architect", "Architect", "Architecture analysis", "agent"),
                    ("reviewer", "Reviewer", "Enterprise code review", "agent"),
                    ("explorer", "Explorer", "Codebase navigation", "agent"),
                    ("refactorer", "Refactorer", "Code refactoring", "agent"),
                    ("testing", "Testing", "Test generation", "agent"),
                    ("security", "Security", "OWASP security scan", "agent"),
                    ("documentation", "Documentation", "Docs generation", "agent"),
                    ("performance", "Performance", "Profiling", "agent"),
                    ("devops", "DevOps", "Infrastructure", "agent"),
                    ("justica", "Justica", "Constitutional governance", "agent"),
                    ("sofia", "Sofia", "Ethical counsel", "agent"),
                    ("data", "Data", "Database analysis", "agent"),
                    # Core Agents (6)
                    (
                        "orchestrator_core",
                        "Orchestrator (Core)",
                        "Multi-agent coordination",
                        "agent",
                    ),
                    ("coder_core", "Coder (Core)", "Darwin-Godel evolution", "agent"),
                    ("reviewer_core", "Reviewer (Core)", "Deep-think review", "agent"),
                    ("architect_core", "Architect (Core)", "Agentic RAG design", "agent"),
                    ("researcher_core", "Researcher (Core)", "Three-loop learning", "agent"),
                    ("devops_core", "DevOps (Core)", "Incident handler", "agent"),
                ]

                for cmd_id, label, desc, category in agent_commands:
                    self._palette.register_command(
                        Command(
                            id=f"agent.{cmd_id}",
                            label=label,
                            description=desc,
                            category=category,
                            keybinding=f"/{cmd_id}",
                        )
                    )

            except ImportError:
                # Minimal fallback
                self._palette = MinimalCommandPalette()

        return self._palette

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Fuzzy search commands."""
        return self.palette.get_suggestions(query, max_results)

    def execute(self, command_id: str):
        """Execute command by ID."""
        return self.palette.execute(command_id)


class AutocompleteBridge:
    """
    Bridge to ContextAwareCompleter with fuzzy matching.

    Features:
    - Slash command completion (/)
    - File path completion (@) - Claude Code style
    - Tool name completion
    - History-based suggestions
    """

    # Default ignore patterns for file scanning
    IGNORE_PATTERNS = {
        # VCS
        ".git",
        ".svn",
        ".hg",
        # Python
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info",
        ".eggs",
        "*.pyc",
        "*.pyo",
        # Node
        "node_modules",
        # IDE
        ".idea",
        ".vscode",
        # OS
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        "*~",
        # Project-specific (VERTICE)
        ".archive",
        ".backup",
        ".bak",
        "prometheus_data",
        "memory_data",
        "cortex_data",
        ".vertice_cache",
        "logs",
        "*.log",
        "coverage_html",
        "site-packages",
        # Large binary/data
        "*.bin",
        "*.dat",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "*.pkl",
        "*.pickle",
        "*.h5",
        "*.hdf5",
        "*.parquet",
    }

    # Limits for file scanning (prevent TUI freeze)
    MAX_FILES = 300  # Reduced from 2000
    MAX_DEPTH = 4  # Reduced from 8

    # File type icons
    FILE_ICONS = {
        ".py": "🐍",
        ".js": "📜",
        ".ts": "💠",
        ".jsx": "📜",
        ".tsx": "💠",
        ".rs": "🦀",
        ".go": "🔵",
        ".md": "📝",
        ".json": "📋",
        ".yaml": "⚙️",
        ".yml": "⚙️",
        ".toml": "⚙️",
        ".html": "🌐",
        ".css": "🎨",
        ".sql": "🗃️",
        ".sh": "💻",
        ".bash": "💻",
    }

    def __init__(self, tool_bridge: Optional["ToolBridge"] = None):
        self.tool_bridge = tool_bridge
        self._completer = None
        self._suggestion_cache: Dict[str, str] = {}
        self._file_cache: List[str] = []
        self._file_cache_valid = False
        self._recent_files: List[str] = []
        # Performance: Cache completions to avoid recomputation
        self._completion_cache: Dict[str, List[Dict]] = {}
        self._completion_cache_time: float = 0.0
        self._lock = threading.Lock()

    def add_recent_file(self, file_path: str) -> None:
        """Track a recently accessed file for priority in @ completions."""
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)
        self._recent_files.insert(0, file_path)
        self._recent_files = self._recent_files[:50]  # Keep last 50

    def _scan_files(self, root: Path = None, max_files: int = None) -> List[str]:
        """Scan project files for @ completion.

        Uses MAX_FILES and MAX_DEPTH limits to prevent TUI freeze.
        """
        if self._file_cache_valid and self._file_cache:
            return self._file_cache

        import fnmatch

        root = root or Path.cwd()
        max_files = max_files or self.MAX_FILES
        files = []

        def should_ignore(path: Path) -> bool:
            name = path.name
            for pattern in self.IGNORE_PATTERNS:
                if fnmatch.fnmatch(name, pattern):
                    return True
            return False

        def scan_dir(dir_path: Path, depth: int = 0):
            if depth > self.MAX_DEPTH or len(files) >= max_files:
                return
            try:
                for entry in sorted(
                    dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
                ):
                    if len(files) >= max_files:
                        break
                    if should_ignore(entry):
                        continue
                    if entry.is_dir():
                        scan_dir(entry, depth + 1)
                    elif entry.is_file():
                        try:
                            rel_path = str(entry.relative_to(root))
                            files.append(rel_path)
                        except ValueError:
                            pass
            except (PermissionError, OSError):
                pass

        scan_dir(root)
        self._file_cache = files
        self._file_cache_valid = True
        return files

    def _get_file_icon(self, filename: str) -> str:
        """Get icon for file based on extension."""
        suffix = Path(filename).suffix.lower()
        return self.FILE_ICONS.get(suffix, "📄")

    def _get_file_completions(self, query: str, max_results: int = 15) -> List[Dict]:
        """Get file completions for @ query."""
        files = self._scan_files()
        query_lower = query.lower()

        scored = []
        for file_path in files:
            filename = Path(file_path).name.lower()

            # Calculate score
            score = 0.0
            is_recent = file_path in self._recent_files

            if not query:
                # Empty query - show recent files first, then alphabetically
                score = 100.0 if is_recent else 1.0  # Small score for non-recent
            elif query_lower == filename:
                score = 100.0
            elif filename.startswith(query_lower):
                score = 90.0 * (len(query) / len(filename))
            elif query_lower in filename:
                score = 70.0 * (len(query) / len(filename))
            elif query_lower in file_path.lower():
                score = 50.0 * (len(query) / len(file_path))
            else:
                # Fuzzy match
                qi = 0
                for c in filename:
                    if qi < len(query_lower) and c == query_lower[qi]:
                        score += 1.0
                        qi += 1
                if qi == len(query_lower):
                    score = 30.0 * (score / len(filename))
                else:
                    continue  # No match

            # Boost recent files
            if is_recent:
                score *= 1.5

            if score > 0:
                scored.append((score, file_path))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        completions = []
        for score, file_path in scored[:max_results]:
            filename = Path(file_path).name
            parent = str(Path(file_path).parent)
            icon = self._get_file_icon(filename)
            is_recent = file_path in self._recent_files

            completions.append(
                {
                    "text": f"@{file_path}",
                    "display": f"{icon} {'★ ' if is_recent else ''}{filename}",
                    "description": parent if parent != "." else "",
                    "type": "file",
                    "score": score,
                }
            )

        return completions

    def get_completions(self, text: str, max_results: int = 10) -> List[Dict]:
        """Get completions for text with fuzzy matching.

        OPTIMIZED: Uses caching to avoid recomputation on every keystroke.
        """
        if not text:
            return []

        # Check cache (valid for 500ms to allow fast typing)
        import time

        cache_key = f"{text}:{max_results}"
        now = time.time()
        if cache_key in self._completion_cache and (now - self._completion_cache_time) < 0.5:
            return self._completion_cache[cache_key]

        # Check for @ file picker trigger
        at_pos = None
        for i in range(len(text) - 1, -1, -1):
            if text[i] == "@" and (i == 0 or text[i - 1].isspace()):
                at_pos = i
                break

        if at_pos is not None:
            # @ file picker mode
            query = text[at_pos + 1 :]
            return self._get_file_completions(query, max_results)

        completions = []
        text_lower = text.lower()

        # Tool completions
        if self.tool_bridge:
            for tool_name in self.tool_bridge.list_tools():
                score = self._fuzzy_score(text_lower, tool_name)
                if score > 0:
                    completions.append(
                        {
                            "text": tool_name,
                            "display": f"🔧 {tool_name}",
                            "type": "tool",
                            "score": score + 10,  # Boost tools
                        }
                    )

        # Command completions - Claude Code parity (37+ commands)
        slash_commands = [
            # Navigation & Help
            ("/help", "Show help"),
            ("/clear", "Clear screen"),
            ("/quit", "Exit"),
            ("/exit", "Exit"),
            # Execution
            ("/run", "Execute bash"),
            ("/read", "Read file"),
            # Discovery
            ("/agents", "List agents"),
            ("/status", "Show status"),
            ("/tools", "List tools"),
            ("/palette", "Command palette"),
            ("/history", "Command history"),
            # Context Management (Claude Code parity)
            ("/context", "Show context"),
            ("/context-clear", "Clear context"),
            ("/compact", "Compact context"),
            ("/cost", "Token usage stats"),
            ("/tokens", "Token usage"),
            # Session Management (Claude Code parity)
            ("/save", "Save session"),
            ("/resume", "Resume session"),
            ("/sessions", "List sessions"),
            ("/checkpoint", "Create checkpoint"),
            ("/rewind", "Rewind to checkpoint"),
            ("/export", "Export conversation"),
            # Project (Claude Code parity)
            ("/init", "Initialize project"),
            ("/model", "Select model/provider"),
            ("/providers", "List LLM providers"),
            ("/doctor", "Check health"),
            ("/permissions", "Manage permissions"),
            # Todo Management (Claude Code parity)
            ("/todos", "List todos"),
            ("/todo", "Add todo"),
            # Agent Commands
            ("/plan", "Plan task"),
            ("/execute", "Execute code"),
            ("/architect", "Architecture"),
            ("/review", "Code review"),
            ("/explore", "Explore code"),
            ("/refactor", "Refactor"),
            ("/test", "Run tests"),
            ("/security", "Security scan"),
            ("/docs", "Generate docs"),
            ("/perf", "Performance"),
            ("/devops", "DevOps"),
            # Governance & Counsel Agents
            ("/justica", "Constitutional governance"),
            ("/sofia", "Ethical counsel"),
            # Data Agent
            ("/data", "Database analysis"),
            # Core Agents (6) - Phase 3 Evolution
            ("/orchestrator", "Multi-agent coordination (Core)"),
            ("/coder", "Darwin-Godel code evolution (Core)"),
            ("/researcher", "Three-loop learning (Core)"),
            # Advanced (Claude Code parity)
            ("/sandbox", "Enable sandbox"),
            ("/hooks", "Manage hooks"),
            ("/mcp", "MCP servers"),
            # Agent Router (NEW)
            ("/router", "Toggle auto-routing"),
            ("/router-status", "Show routing config"),
            ("/route", "Manually route message"),
            # Background Tasks (Claude Code /bashes parity)
            ("/bashes", "List background tasks"),
            ("/bg", "Start background task"),
            ("/kill", "Kill background task"),
            # Notebook Tools (Claude Code parity)
            ("/notebook", "Read notebook file"),
            # Plan Mode (Claude Code parity - WAVE 4)
            ("/plan-mode", "Enter plan mode"),
            ("/plan-status", "Plan mode status"),
            ("/plan-note", "Add plan note"),
            ("/plan-exit", "Exit plan mode"),
            ("/plan-approve", "Approve plan"),
            # PR Creation (Claude Code parity - WAVE 4)
            ("/pr", "Create pull request"),
            ("/pr-draft", "Create draft PR"),
            # Auth Management (Claude Code parity - WAVE 5)
            ("/login", "Login to provider"),
            ("/logout", "Logout from provider"),
            ("/auth", "Show auth status"),
            # Memory (Claude Code parity - WAVE 5)
            ("/memory", "View/manage memory"),
            ("/remember", "Add note to memory"),
            # Image/PDF Reading (Claude Code parity - WAVE 5)
            ("/image", "Read image file"),
            ("/pdf", "Read PDF file"),
            # WAVE 6: Beyond Claude Code Parity
            ("/audit", "View audit log"),
            ("/diff", "Diff preview"),
            ("/backup", "Create/list backups"),
            ("/restore", "Restore from backup"),
            ("/undo", "Undo last operation"),
            ("/redo", "Redo operation"),
            ("/undo-stack", "View undo stack"),
            ("/secrets", "Scan for secrets"),
            ("/secrets-staged", "Scan staged files"),
            # WAVE 7: Missing Commands (Audit Dec 2025)
            ("/prometheus", "Direct Prometheus query"),
            ("/task", "Launch subagent task"),
            ("/subagents", "List running subagents"),
            ("/ask", "Ask user question"),
            ("/commands", "List custom commands"),
            ("/command-create", "Create custom command"),
            ("/command-delete", "Delete custom command"),
            ("/a2a", "Agent-to-Agent protocol"),
            ("/autoaudit", "Run TUI audit"),
            ("/autoaudit quick", "Quick audit (<5s)"),
            ("/autoaudit list", "List scenarios"),
            ("/autoaudit help", "Audit help"),
            ("/tribunal", "Toggle TRIBUNAL mode"),
            # Core Agent Aliases (explicit slash access)
            ("/reviewer-core", "Deep-think code review (Core)"),
            ("/architect-core", "Agentic RAG design (Core)"),
            ("/devops-core", "Incident handler (Core)"),
        ]

        for cmd, desc in slash_commands:
            score = self._fuzzy_score(text_lower, cmd)
            if score > 0:
                completions.append(
                    {
                        "text": cmd,
                        "display": f"⚡ {cmd}",
                        "description": desc,
                        "type": "command",
                        "score": score + 20,  # Boost commands
                    }
                )

        # Sort by score
        completions.sort(key=lambda x: x["score"], reverse=True)
        result = completions[:max_results]

        # Cache result
        self._completion_cache[cache_key] = result
        self._completion_cache_time = time.time()

        return result

    def get_completions_threadsafe(self, text: str, max_results: int = 10) -> List[Dict]:
        """Thread-safe wrapper for `get_completions` (safe for asyncio.to_thread)."""
        with self._lock:
            return self.get_completions(text, max_results)

    def _fuzzy_score(self, query: str, target: str) -> float:
        """Calculate fuzzy match score."""
        if not query:
            return 0.0

        target_lower = target.lower()

        # Exact match
        if query == target_lower:
            return 100.0

        # Prefix match (highest non-exact score)
        if target_lower.startswith(query):
            return 90.0 * (len(query) / len(target))

        # Substring match
        if query in target_lower:
            return 70.0 * (len(query) / len(target))

        # Character sequence match (fuzzy)
        score = 0.0
        query_idx = 0
        for char in target_lower:
            if query_idx < len(query) and char == query[query_idx]:
                score += 1.0
                query_idx += 1

        if query_idx == len(query):
            return 50.0 * (score / len(target))

        return 0.0

    def get_suggestion(self, text: str) -> Optional[str]:
        """Get inline suggestion (Fish-style)."""
        if text in self._suggestion_cache:
            return self._suggestion_cache[text]

        completions = self.get_completions(text, max_results=1)
        if completions and completions[0]["score"] > 50:
            suggestion = completions[0]["text"]
            if suggestion.startswith(text):
                result = suggestion[len(text) :]
                self._suggestion_cache[text] = result
                return result

        return None


__all__ = [
    "CommandPaletteBridge",
    "MinimalCommandPalette",
    "AutocompleteBridge",
]

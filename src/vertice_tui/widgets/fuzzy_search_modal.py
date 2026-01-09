"""
Session Search Modal - Fuzzy search across sessions
===============================================

Modal de busca com fuzzy matching para histórico de sessões.
Inclui busca em sessão atual e sessões passadas.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, ListView, ListItem, Label, Button, Static
from textual.widget import Widget
from textual.message import Message
from textual.binding import Binding
from textual import events

try:
    from rapidfuzz import fuzz, process

    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


@dataclass
class SearchResult:
    """Result of a fuzzy search."""

    session_id: str
    message_index: int
    content: str
    score: float
    context: str


class FuzzySearchModal(Widget):
    """
    Modal for fuzzy search across sessions.

    Features:
    - Fuzzy matching with rapidfuzz
    - Real-time search as you type
    - Context preview
    - Keyboard navigation
    - Session filtering
    """

    DEFAULT_CSS = """
    FuzzySearchModal {
        width: 80%;
        height: 70%;
        border: solid $primary;
        background: $surface;
    }

    FuzzySearchModal > Container {
        height: 100%;
        padding: 1;
    }

    FuzzySearchModal Input {
        border: solid $secondary;
        margin-bottom: 1;
    }

    FuzzySearchModal ListView {
        border: solid $primary;
        height: 1fr;
    }

    FuzzySearchModal ListItem {
        padding: 0 1;
    }

    FuzzySearchModal .search-result {
        margin-bottom: 0.5;
    }

    FuzzySearchModal .result-content {
        color: $text;
    }

    FuzzySearchModal .result-context {
        color: $text-muted;
        font-size: 0.8;
    }

    FuzzySearchModal .result-score {
        color: $success;
        font-size: 0.8;
    }

    FuzzySearchModal Button {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close search"),
        Binding("enter", "select", "Select result"),
        Binding("up", "move_up", "Move up"),
        Binding("down", "move_down", "Move down"),
    ]

    class SearchCompleted(Message):
        """Search completed with results."""

        def __init__(self, results: List[SearchResult]):
            self.results = results
            super().__init__()

    class ResultSelected(Message):
        """A search result was selected."""

        def __init__(self, result: SearchResult):
            self.result = result
            super().__init__()

    def __init__(
        self,
        session_manager: Any,
        current_session_id: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(name=name, id=id)
        self.session_manager = session_manager
        self.current_session_id = current_session_id
        self.search_results: List[SearchResult] = []
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        """Compose the search modal."""
        with Container():
            with Vertical():
                # Search input
                yield Input(
                    placeholder="Search across sessions (fuzzy matching)...", id="search-input"
                )

                # Results list
                yield ListView(id="results-list")

                # Status and actions
                with Horizontal():
                    yield Static("Results: 0", id="status")
                    yield Button("Close", id="close-btn", variant="primary")

    def on_mount(self) -> None:
        """Initialize the modal."""
        self.add_class("modal")
        input_widget = self.query_one("#search-input", Input)
        input_widget.focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            query = event.value.strip()
            if len(query) >= 2:  # Minimum 2 chars for search
                await self._perform_search(query)
            else:
                await self._clear_results()

    async def _perform_search(self, query: str) -> None:
        """Perform fuzzy search across sessions."""
        if not FUZZY_AVAILABLE:
            await self._show_fallback_results(query)
            return

        try:
            # Search current session
            results = []
            if self.current_session_id:
                current_results = await self._search_session(
                    self.current_session_id, query, "current"
                )
                results.extend(current_results)

            # Search other sessions (limit to recent 5)
            other_sessions = await self._get_recent_sessions(5)
            for session_id in other_sessions:
                if session_id != self.current_session_id:
                    session_results = await self._search_session(session_id, query, "past")
                    results.extend(session_results)

            # Sort by score (best matches first)
            results.sort(key=lambda x: x.score, reverse=True)
            self.search_results = results[:20]  # Limit to 20 results

            await self._display_results()

        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")

    async def _search_session(
        self, session_id: str, query: str, session_type: str
    ) -> List[SearchResult]:
        """Search within a specific session."""
        results = []

        try:
            # Load session data (this would need to be implemented in SessionManager)
            session_data = await self._load_session_messages(session_id)

            for i, message in enumerate(session_data):
                content = message.get("content", "")
                if not content:
                    continue

                # Fuzzy search
                score = fuzz.partial_ratio(query.lower(), content.lower())
                if score > 60:  # Minimum score threshold
                    # Extract context (50 chars around match)
                    context = self._extract_context(content, query)

                    result = SearchResult(
                        session_id=session_id,
                        message_index=i,
                        content=content[:100] + "..." if len(content) > 100 else content,
                        score=score,
                        context=context,
                    )
                    results.append(result)

        except Exception as e:
            print(f"Error searching session {session_id}: {e}")

        return results

    async def _load_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Load messages from a session. This needs SessionManager integration."""
        # Placeholder - would integrate with actual SessionManager
        try:
            # This would call session_manager.get_session_messages(session_id)
            return []  # Placeholder
        except Exception:
            return []

    async def _get_recent_sessions(self, limit: int) -> List[str]:
        """Get recent session IDs."""
        # Placeholder - would integrate with SessionManager
        try:
            # This would call session_manager.get_recent_sessions(limit)
            return []  # Placeholder
        except Exception:
            return []

    def _extract_context(self, content: str, query: str) -> str:
        """Extract context around search query."""
        content_lower = content.lower()
        query_lower = query.lower()

        # Find position of query
        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:50] + "..."

        # Extract 30 chars before and after
        start = max(0, pos - 30)
        end = min(len(content), pos + len(query) + 30)

        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."

        return context

    async def _display_results(self) -> None:
        """Display search results in the list."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()

        for result in self.search_results:
            # Create result item
            item = ListItem()
            item.compose_add_child(self._create_result_widget(result))
            list_view.append(item)

        # Update status
        status = self.query_one("#status", Static)
        status.update(f"Results: {len(self.search_results)}")

    def _create_result_widget(self, result: SearchResult) -> Widget:
        """Create a widget for displaying a search result."""
        container = Vertical(classes="search-result")

        # Content
        content_label = Label(result.content, classes="result-content")
        container.compose_add_child(content_label)

        # Context
        context_label = Label(result.context, classes="result-context")
        container.compose_add_child(context_label)

        # Score and session info
        score_text = f"Score: {result.score:.1f}% | Session: {result.session_id[:8]}..."
        score_label = Label(score_text, classes="result-score")
        container.compose_add_child(score_label)

        return container

    async def _show_fallback_results(self, query: str) -> None:
        """Show basic results when fuzzy search is not available."""
        # Simple substring search as fallback
        results = []
        # This would do basic substring search across sessions

        self.search_results = results
        await self._display_results()

    async def _clear_results(self) -> None:
        """Clear search results."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()
        status = self.query_one("#status", Static)
        status.update("Results: 0")
        self.search_results = []

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            await self.action_close()

    def action_close(self) -> None:
        """Close the search modal."""
        self.remove()

    def action_select(self) -> None:
        """Select the currently highlighted result."""
        if self.search_results and self.selected_index < len(self.search_results):
            result = self.search_results[self.selected_index]
            self.post_message(self.ResultSelected(result))
            self.remove()

    def action_move_up(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._update_selection()

    def action_move_down(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.search_results) - 1:
            self.selected_index += 1
            self._update_selection()

    def _update_selection(self) -> None:
        """Update visual selection in list."""
        list_view = self.query_one("#results-list", ListView)
        # This would highlight the selected item visually

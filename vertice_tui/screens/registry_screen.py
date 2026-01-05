"""
Registry Screen - Central view for all Agents and Tools.

Exposes the entire arsenal of the Vertice system.
Implements user request: "TUI is where I want all tools and agents to be exposed"

Features:
- Tabbed view: Agents | Tools
- Detailed inspection pane
- Dynamic loading from AgentRegistry and ToolBridge
"""

from __future__ import annotations


from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, Container
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    DataTable,
    Static,
    Markdown,
)

from vertice_tui.core.agents.registry import AGENT_REGISTRY


class RegistryScreen(Screen):
    """
    Registry Screen showing all available Agents and Tools.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    RegistryScreen {
        layout: vertical;
        background: $surface;
    }

    .list-container {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }

    .detail-container {
        width: 2fr;
        height: 1fr;
        border: solid $secondary;
        padding: 1 2;
        overflow-y: auto;
    }

    DataTable {
        height: 1fr;
    }

    #agent-detail-header, #tool-detail-header {
        background: $primary-darken-2;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    """

    def __init__(self, bridge=None) -> None:
        super().__init__()
        self.bridge = bridge
        self.selected_agent = None
        self.selected_tool = None

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header(show_clock=True)

        with Container():
            with TabbedContent(initial="agents"):
                # --- AGENTS TAB ---
                with TabPane("Agents", id="agents"):
                    with Horizontal():
                        with Vertical(classes="list-container"):
                            yield DataTable(id="agent-table", cursor_type="row")
                        with Vertical(classes="detail-container"):
                            yield Static("Select an agent to view details", id="agent-detail-header")
                            yield Markdown(id="agent-detail-body")

                # --- TOOLS TAB ---
                with TabPane("Tools", id="tools"):
                    with Horizontal():
                        with Vertical(classes="list-container"):
                            yield DataTable(id="tool-table", cursor_type="row")
                        with Vertical(classes="detail-container"):
                            yield Static("Select a tool to view details", id="tool-detail-header")
                            yield Markdown(id="tool-detail-body")

        yield Footer()

    def on_mount(self) -> None:
        """Populate tables on mount."""
        self._populate_agents()
        self._populate_tools()

    def _populate_agents(self) -> None:
        """Populate agent table."""
        table = self.query_one("#agent-table", DataTable)
        table.clear()
        table.add_columns("Name", "Role", "Capabilities")

        for name, info in AGENT_REGISTRY.items():
            caps = ", ".join(info.capabilities[:2])
            if len(info.capabilities) > 2:
                caps += "..."
            table.add_row(name, info.role, caps, key=name)

    def _populate_tools(self) -> None:
        """Populate tool table."""
        table = self.query_one("#tool-table", DataTable)
        table.clear()
        table.add_columns("Category", "Name", "Description")

        if not self.bridge:
            return

        # Get tools (assuming bridge.tools.registry.get_all() returns dict of tools)
        try:
            # Need to access internal registry or list method
            # ToolBridge has get_tool and list_tools, but we need descriptions
            # bridge.tools.registry.get_all() returns {name: tool_instance}

            # Using private access to registry for efficiency, or we could loop list_tools
            # ToolBridge.registry (property) -> ToolRegistry
            registry = self.bridge.tools.registry
            all_tools = registry.get_all()

            # Group by category
            for name, tool in sorted(all_tools.items()):
                # Handle both ValidatedTool (category enum) and older tools
                cat = getattr(tool, "category", "General")
                desc = getattr(tool, "description", "No description")

                # Convert enum to string if needed
                if hasattr(cat, "value"):
                    cat = cat.value.replace("_", " ").title()
                else:
                    cat = str(cat).replace("_", " ").title()

                table.add_row(cat, name, desc, key=name)
        except Exception as e:
            table.add_row("Error", "Error loading tools", str(e))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        table_id = event.data_table.id
        row_key = event.row_key.value

        if table_id == "agent-table":
            self._show_agent_details(row_key)
        elif table_id == "tool-table":
            self._show_tool_details(row_key)

    def _show_agent_details(self, agent_name: str) -> None:
        """Show agent details."""
        info = AGENT_REGISTRY.get(agent_name)
        if not info:
            return

        header = self.query_one("#agent-detail-header", Static)
        body = self.query_one("#agent-detail-body", Markdown)

        header.update(f"{info.name.upper()} ({info.role})")

        md_text = f"""
**Description:**
{info.description}

**Capabilities:**
"""
        for cap in info.capabilities:
            md_text += f"- {cap}\n"

        md_text += f"""
**Implementation:**
- Module: `{info.module_path}`
- Class: `{info.class_name}`
- Core Agent: {"Yes" if getattr(info, "is_core", False) else "No"}
"""
        body.update(md_text)

    def _show_tool_details(self, tool_name: str) -> None:
        """Show tool details."""
        if not self.bridge:
            return

        tool = self.bridge.tools.get_tool(tool_name)
        if not tool:
            return

        header = self.query_one("#tool-detail-header", Static)
        body = self.query_one("#tool-detail-body", Markdown)

        header.update(f"{tool_name.upper()}")

        desc = getattr(tool, "description", "")

        md_text = f"""
**Description:**
{desc}

**Parameters:**
"""
        # Handle ValidatedTool parameters
        params = getattr(tool, "parameters", {})
        if params:
            for pname, pinfo in params.items():
                req = " (Required)" if pinfo.get("required") else ""
                md_text += f"- **{pname}**`{req}`: {pinfo.get('description', '')}\n"
        else:
            md_text += "- No parameters defined or simple tool.\n"

        # Usage example if available
        if hasattr(tool, "usage_example"):
            md_text += f"\n**Usage:**\n```python\n{tool.usage_example}\n```"

        body.update(md_text)

    def action_refresh(self) -> None:
        """Refresh lists."""
        self._populate_agents()
        self._populate_tools()

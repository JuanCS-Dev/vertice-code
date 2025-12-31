"""
Claude Parity Command Handler (Part 1).

Handles context, tokens, model, hooks, routing commands:
/compact, /cost, /tokens, /todos, /todo, /model, /init, /hooks, /mcp,
/router, /router-status, /route
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView


class ClaudeParityHandler:
    """Handler for Claude Code parity commands (Part 1)."""

    def __init__(self, app: "QwenApp"):
        self.app = app
        self._tasks_handler = None
        self._plan_handler = None

    @property
    def bridge(self):
        return self.app.bridge

    @property
    def tasks_handler(self):
        """Lazy load tasks handler."""
        if self._tasks_handler is None:
            from vertice_tui.handlers.claude_parity_tasks import ClaudeParityTasksHandler
            self._tasks_handler = ClaudeParityTasksHandler(self.app)
        return self._tasks_handler

    @property
    def plan_handler(self):
        """Lazy load plan handler."""
        if self._plan_handler is None:
            from vertice_tui.handlers.claude_parity_plan import ClaudeParityPlanHandler
            self._plan_handler = ClaudeParityPlanHandler(self.app)
        return self._plan_handler

    async def handle(
        self,
        command: str,
        args: str,
        view: "ResponseView"
    ) -> None:
        """Route to specific handler method."""
        # Local handlers
        local_handlers = {
            "/compact": self._handle_compact,
            "/cost": self._handle_cost,
            "/tokens": self._handle_tokens,
            "/todos": self._handle_todos,
            "/todo": self._handle_todo,
            "/model": self._handle_model,
            "/init": self._handle_init,
            "/hooks": self._handle_hooks,
            "/mcp": self._handle_mcp,
            "/router": self._handle_router,
            "/router-status": self._handle_router_status,
            "/route": self._handle_route,
        }

        # Task-related commands (delegate to tasks handler)
        task_commands = {"/bashes", "/bg", "/kill", "/notebook", "/task", "/subagents", "/ask"}

        # Plan-related commands (delegate to plan handler)
        plan_commands = {
            "/commands", "/command-create", "/command-delete",
            "/plan-mode", "/plan-status", "/plan-note", "/plan-exit", "/plan-approve"
        }

        if command in local_handlers:
            await local_handlers[command](args, view)
        elif command in task_commands:
            await self.tasks_handler.handle(command, args, view)
        elif command in plan_commands:
            await self.plan_handler.handle(command, args, view)

    async def _handle_compact(self, args: str, view: "ResponseView") -> None:
        focus = args if args else None
        try:
            result = self.bridge.compact_context(focus)
            view.add_system_message(
                f"## 📦 Context Compacted\n\n"
                f"- **Messages before:** {result.get('before', '?')}\n"
                f"- **Messages after:** {result.get('after', '?')}\n"
                f"- **Tokens saved:** ~{result.get('tokens_saved', '?')}\n"
                f"{'- **Focus:** ' + focus if focus else ''}"
            )
        except Exception as e:
            view.add_error(f"Compact failed: {e}")

    async def _handle_cost(self, args: str, view: "ResponseView") -> None:
        try:
            stats = self.bridge.get_token_stats()
            view.add_system_message(
                f"## 💰 Token Usage\n\n"
                f"- **Session tokens:** {stats.get('session_tokens', 0):,}\n"
                f"- **Total tokens:** {stats.get('total_tokens', 0):,}\n"
                f"- **Input tokens:** {stats.get('input_tokens', 0):,}\n"
                f"- **Output tokens:** {stats.get('output_tokens', 0):,}\n"
                f"- **Estimated cost:** ${stats.get('cost', 0):.4f}\n"
            )
        except Exception as e:
            view.add_system_message(f"## 💰 Token Usage\n\nToken tracking not available: {e}")

    async def _handle_tokens(self, args: str, view: "ResponseView") -> None:
        try:
            stats = self.bridge.get_token_stats()
            view.add_system_message(
                f"## 📊 Token Stats\n\n"
                f"**Session:** {stats.get('session_tokens', 0):,} tokens\n"
                f"**Context:** {stats.get('context_tokens', 0):,} / {stats.get('max_tokens', 128000):,}"
            )
        except Exception as e:
            view.add_system_message(f"## 📊 Token Stats\n\nNot available: {e}")

    async def _handle_todos(self, args: str, view: "ResponseView") -> None:
        try:
            todos = self.bridge.get_todos()
            if todos:
                lines = ["## 📋 Todo List\n"]
                for i, todo in enumerate(todos, 1):
                    status_icon = "✅" if todo.get('done') else "⬜"
                    lines.append(f"{status_icon} {i}. {todo.get('text', '?')}")
                view.add_system_message("\n".join(lines))
            else:
                view.add_system_message("## 📋 Todo List\n\nNo todos yet. Use `/todo <task>` to add one.")
        except Exception as e:
            view.add_system_message(f"## 📋 Todo List\n\nNot available: {e}")

    async def _handle_todo(self, args: str, view: "ResponseView") -> None:
        if not args:
            view.add_error("Usage: /todo <task description>")
        else:
            try:
                self.bridge.add_todo(args)
                view.add_system_message(f"✅ Added todo: {args}")
            except Exception as e:
                view.add_error(f"Failed to add todo: {e}")

    async def _handle_model(self, args: str, view: "ResponseView") -> None:
        if args:
            try:
                self.bridge.set_model(args)
                view.add_system_message(f"✅ Model changed to: **{args}**")
            except Exception as e:
                view.add_error(f"Failed to change model: {e}")
        else:
            current = self.bridge.get_current_model()
            available = self.bridge.get_available_models()
            view.add_system_message(
                f"## 🤖 Model Selection\n\n"
                f"**Current:** {current}\n\n"
                f"**Available:**\n" +
                "\n".join(f"- `{m}`" for m in available)
            )

    async def _handle_init(self, args: str, view: "ResponseView") -> None:
        try:
            result = self.bridge.init_project()
            view.add_system_message(
                f"## 🚀 Project Initialized\n\n"
                f"Created **JUANCS.md** with project context.\n\n"
                f"{result.get('summary', 'Project ready!')}"
            )
        except Exception as e:
            view.add_error(f"Init failed: {e}")

    async def _handle_hooks(self, args: str, view: "ResponseView") -> None:
        try:
            parts = args.split(maxsplit=2) if args else []
            subcommand = parts[0].lower() if parts else ""

            if subcommand == "enable" and len(parts) >= 2:
                hook_name = parts[1]
                if self.bridge.enable_hook(hook_name, True):
                    view.add_system_message(f"✅ Hook **{hook_name}** enabled")
                else:
                    view.add_error(f"Unknown hook: {hook_name}")

            elif subcommand == "disable" and len(parts) >= 2:
                hook_name = parts[1]
                if self.bridge.enable_hook(hook_name, False):
                    view.add_system_message(f"⬜ Hook **{hook_name}** disabled")
                else:
                    view.add_error(f"Unknown hook: {hook_name}")

            elif subcommand == "add" and len(parts) >= 3:
                hook_name = parts[1]
                command_str = parts[2]
                if self.bridge.add_hook_command(hook_name, command_str):
                    view.add_system_message(f"✅ Added command to **{hook_name}**: `{command_str}`")
                else:
                    view.add_error(f"Failed to add command to hook: {hook_name}")

            elif subcommand == "remove" and len(parts) >= 3:
                hook_name = parts[1]
                command_str = parts[2]
                if self.bridge.remove_hook_command(hook_name, command_str):
                    view.add_system_message(f"✅ Removed command from **{hook_name}**: `{command_str}`")
                else:
                    view.add_error(f"Failed to remove command from hook: {hook_name}")

            elif subcommand == "set" and len(parts) >= 3:
                hook_name = parts[1]
                commands = [c.strip() for c in parts[2].split(",")]
                if self.bridge.set_hook(hook_name, commands):
                    view.add_system_message(f"✅ Hook **{hook_name}** configured with {len(commands)} command(s)")
                else:
                    view.add_error(f"Failed to set hook: {hook_name}")

            elif subcommand == "stats":
                stats = self.bridge.get_hook_stats()
                lines = ["## 📊 Hook Statistics\n"]
                for key, value in stats.items():
                    lines.append(f"- **{key}:** {value}")
                view.add_system_message("\n".join(lines))

            else:
                hooks = self.bridge.get_hooks()
                if hooks:
                    lines = [
                        "## 🪝 Hooks Configuration\n",
                        "*Hooks run shell commands after file operations*\n",
                    ]
                    for hook_name, hook_info in hooks.items():
                        status = "✅" if hook_info.get('enabled') else "⬜"
                        lines.append(f"\n### {status} {hook_name}")
                        lines.append(f"*{hook_info.get('description', '')}*")
                        commands = hook_info.get('commands', [])
                        if commands:
                            lines.append("**Commands:**")
                            for cmd in commands:
                                lines.append(f"  - `{cmd}`")
                        else:
                            lines.append("*No commands configured*")

                    lines.append("\n**Usage:**")
                    lines.append("- `/hooks enable <hook>` - Enable a hook")
                    lines.append("- `/hooks disable <hook>` - Disable a hook")
                    lines.append("- `/hooks add <hook> <cmd>` - Add command")
                    lines.append("- `/hooks remove <hook> <cmd>` - Remove command")
                    lines.append("- `/hooks set <hook> <cmd1,cmd2>` - Set commands")
                    lines.append("- `/hooks stats` - Show execution stats")
                    view.add_system_message("\n".join(lines))
                else:
                    view.add_system_message("## 🪝 Hooks\n\nNo hooks configured.")
        except Exception as e:
            view.add_system_message(f"## 🪝 Hooks\n\nNot available: {e}")

    async def _handle_mcp(self, args: str, view: "ResponseView") -> None:
        """Handle /mcp commands (Phase 6.2 - MCP integration)."""
        parts = args.split(maxsplit=1) if args else []
        subcommand = parts[0].lower() if parts else "status"
        subargs = parts[1] if len(parts) > 1 else ""

        try:
            if subcommand == "status":
                await self._mcp_status(view)
            elif subcommand == "serve":
                port = int(subargs) if subargs.isdigit() else 3000
                await self._mcp_serve(port, view)
            elif subcommand == "stop":
                await self._mcp_stop(view)
            elif subcommand == "connect":
                await self._mcp_connect(subargs, view)
            elif subcommand == "disconnect":
                await self._mcp_disconnect(subargs, view)
            elif subcommand == "tools":
                await self._mcp_tools(view)
            else:
                await self._mcp_help(view)
        except Exception as e:
            view.add_error(f"MCP command failed: {e}")

    async def _mcp_status(self, view: "ResponseView") -> None:
        """Show MCP server and connection status."""
        status = self.bridge.get_mcp_status()
        server = status.get("server", {})
        connections = status.get("connections", [])

        lines = ["## 🔌 MCP Status\n"]

        # Server status
        if server.get("running"):
            lines.append(f"**Server:** 🟢 Running on `{server.get('host')}:{server.get('port')}`")
            lines.append(f"  - Transport: {server.get('transport', 'stdio')}")
            lines.append(f"  - Tools exposed: {server.get('exposed_tools', 0)}")
        else:
            lines.append("**Server:** 🔴 Stopped")

        # Connection status
        if connections:
            lines.append("\n**External Connections:**")
            for conn in connections:
                status_icon = "🟢" if conn.get("connected") else "🔴"
                lines.append(f"  {status_icon} `{conn.get('name')}` - {conn.get('url')}")
        else:
            lines.append("\n**External Connections:** None")

        lines.append(f"\n**Total tools:** {status.get('total_exposed_tools', 0)} exposed, {status.get('total_imported_tools', 0)} imported")
        view.add_system_message("\n".join(lines))

    async def _mcp_serve(self, port: int, view: "ResponseView") -> None:
        """Start MCP server."""
        result = await self.bridge.start_mcp_server(port)
        if result.get("success"):
            view.add_system_message(
                f"## 🚀 MCP Server Started\n\n"
                f"**Port:** {result.get('port')}\n"
                f"**Host:** {result.get('host')}\n"
                f"**Tools exposed:** {result.get('tools_exposed', 0)}"
            )
        else:
            view.add_error(f"Failed to start MCP server: {result.get('error')}")

    async def _mcp_stop(self, view: "ResponseView") -> None:
        """Stop MCP server."""
        result = await self.bridge.stop_mcp_server()
        if result.get("success"):
            view.add_system_message("## 🛑 MCP Server Stopped")
        else:
            view.add_error(f"Failed to stop MCP server: {result.get('error')}")

    async def _mcp_connect(self, url: str, view: "ResponseView") -> None:
        """Connect to external MCP server."""
        if not url:
            view.add_error("Usage: `/mcp connect <url>`")
            return
        result = await self.bridge.connect_mcp(url)
        if result.get("success"):
            view.add_system_message(
                f"## 🔗 Connected to MCP\n\n"
                f"**Name:** {result.get('name')}\n"
                f"**URL:** {result.get('url')}\n"
                f"**Tools:** {result.get('tools', 0)}"
            )
        else:
            view.add_error(f"Failed to connect: {result.get('error')}")

    async def _mcp_disconnect(self, name: str, view: "ResponseView") -> None:
        """Disconnect from external MCP server."""
        if not name:
            view.add_error("Usage: `/mcp disconnect <name>`")
            return
        result = await self.bridge.disconnect_mcp(name)
        if result.get("success"):
            view.add_system_message(f"## 🔌 Disconnected from `{name}`")
        else:
            view.add_error(f"Failed to disconnect: {result.get('error')}")

    async def _mcp_tools(self, view: "ResponseView") -> None:
        """List available MCP tools."""
        tools = self.bridge.list_mcp_tools()
        lines = ["## 🔧 MCP Tools\n"]

        exposed = tools.get("exposed", [])
        if exposed:
            lines.append(f"**Exposed ({len(exposed)}):**")
            for tool in exposed[:20]:  # Limit display
                lines.append(f"  - `{tool}`")
            if len(exposed) > 20:
                lines.append(f"  ... and {len(exposed) - 20} more")
        else:
            lines.append("**Exposed:** None (start server with `/mcp serve`)")

        imported = tools.get("imported", {})
        if imported:
            lines.append("\n**Imported:**")
            for source, source_tools in imported.items():
                lines.append(f"  *{source}:*")
                for tool in source_tools[:10]:
                    lines.append(f"    - `{tool}`")

        view.add_system_message("\n".join(lines))

    async def _mcp_help(self, view: "ResponseView") -> None:
        """Show MCP command help."""
        view.add_system_message(
            "## 🔌 MCP Commands\n\n"
            "- `/mcp status` - Show server and connection status\n"
            "- `/mcp serve [port]` - Start MCP server (default: 3000)\n"
            "- `/mcp stop` - Stop MCP server\n"
            "- `/mcp connect <url>` - Connect to external MCP server\n"
            "- `/mcp disconnect <name>` - Disconnect from server\n"
            "- `/mcp tools` - List available tools"
        )

    async def _handle_router(self, args: str, view: "ResponseView") -> None:
        try:
            enabled = self.bridge.toggle_auto_routing()
            status_emoji = "🟢" if enabled else "🔴"
            view.add_system_message(
                f"## 🎯 Agent Router\n\n"
                f"{status_emoji} Auto-routing is now **{'ENABLED' if enabled else 'DISABLED'}**\n\n"
                f"When enabled, messages are automatically routed to specialized agents based on intent."
            )
        except Exception as e:
            view.add_error(f"Router toggle failed: {e}")

    async def _handle_router_status(self, args: str, view: "ResponseView") -> None:
        try:
            status = self.bridge.get_router_status()
            lines = [
                "## 🎯 Agent Router Status\n",
                f"- **Enabled:** {'Yes' if status['enabled'] else 'No'}",
                f"- **Min Confidence:** {int(status['min_confidence']*100)}%",
                f"- **Agents:** {status['agents_configured']}",
                f"- **Patterns:** {status['pattern_count']}",
                "\n**Available Agents:**",
            ]
            for agent in status['available_agents']:
                lines.append(f"  - `/{agent}`")
            view.add_system_message("\n".join(lines))
        except Exception as e:
            view.add_error(f"Router status failed: {e}")

    async def _handle_route(self, args: str, view: "ResponseView") -> None:
        if not args:
            view.add_error("Usage: `/route <message>` - Test how a message would be routed")
        else:
            try:
                analysis = self.bridge.test_routing(args)
                lines = [
                    "## 🎯 Routing Analysis\n",
                    f"**Message:** `{analysis['message'][:50]}...`" if len(analysis['message']) > 50 else f"**Message:** `{analysis['message']}`",
                    f"**Should Route:** {'Yes' if analysis['should_route'] else 'No'}",
                ]

                if analysis['detected_intents']:
                    lines.append("\n**Detected Intents:**")
                    for intent in analysis['detected_intents'][:5]:
                        lines.append(f"  - `{intent['agent']}`: {intent['confidence']}")

                if analysis['selected_route']:
                    route = analysis['selected_route']
                    lines.append(f"\n**Would Route To:** `{route['agent']}` ({route['confidence']})")
                else:
                    lines.append("\n**Would Route To:** None (general LLM chat)")

                if analysis['suggestion']:
                    lines.append(f"\n**Suggestion:**\n{analysis['suggestion']}")

                view.add_system_message("\n".join(lines))
            except Exception as e:
                view.add_error(f"Route test failed: {e}")

"""
A2A Command Handler - /a2a commands for Agent-to-Agent protocol.

Phase 6.3 TUI Integration.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView


class A2ACommandHandler:
    """Handler for /a2a commands."""

    def __init__(self, app: "QwenApp") -> None:
        self.app = app

    @property
    def bridge(self) -> Any:
        """Access Bridge through app."""
        return self.app.bridge

    async def handle(self, command: str, args: str, view: "ResponseView") -> None:
        """
        Handle /a2a commands.

        Subcommands:
        - status: Show server and discovery status
        - serve [port]: Start gRPC server
        - stop: Stop server
        - discover: Discover agents on network
        - call <agent> <task>: Send task to remote agent
        - card: Show local agent card
        - sign <key>: Sign agent card with JWS
        """
        parts = args.split(maxsplit=1) if args else []
        subcommand = parts[0].lower() if parts else "status"
        subargs = parts[1] if len(parts) > 1 else ""

        handlers = {
            "status": self._handle_status,
            "serve": lambda v: self._handle_serve(int(subargs) if subargs.isdigit() else 50051, v),
            "stop": self._handle_stop,
            "discover": self._handle_discover,
            "call": lambda v: self._handle_call(subargs, v),
            "card": self._handle_card,
            "sign": lambda v: self._handle_sign(subargs, v),
            "agents": self._handle_agents,
        }

        try:
            handler = handlers.get(subcommand, self._handle_help)
            # Inspect handler signature to see if it takes view only or needs args wrapper
            # Simplification: handlers lambda wrappers above handle args

            # Direct dispatch if it's one of the mapped ones, else help
            # Direct dispatch (handler is already resolved)
            await handler(view)
        except Exception as e:
            view.add_error(f"A2A command failed: {e}")

    async def _handle_status(self, view: "ResponseView") -> None:
        """Show A2A server and discovery status."""
        status = self.bridge.get_a2a_status()
        server = status.get("server", {})

        lines = ["## 🤖 A2A Status\n"]

        # Server status
        if server.get("running"):
            lines.append(f"**Server:** 🟢 Running on port `{server.get('port')}`")
            lines.append(f"  - Agent: {server.get('agent_card_name', 'unnamed')}")
            lines.append(f"  - Active tasks: {server.get('active_tasks', 0)}")
            lines.append(f"  - Total processed: {server.get('total_tasks_processed', 0)}")
        else:
            lines.append("**Server:** 🔴 Stopped")

        # Discovery status
        discovered = status.get("discovered_agents", 0)
        lines.append(f"\n**Discovered Agents:** {discovered}")

        # Local card
        if status.get("local_card"):
            lines.append("\n**Local Card:** Configured")
        else:
            lines.append("\n**Local Card:** Not configured (start server first)")

        view.add_system_message("\n".join(lines))

    async def _handle_serve(self, port: int, view: "ResponseView") -> None:
        """Start A2A gRPC server."""
        result = await self.bridge.start_a2a_server(port)
        if result.get("success"):
            view.add_system_message(
                f"## 🚀 A2A Server Started\n\n"
                f"**Port:** {result.get('port')}\n"
                f"**Agent:** {result.get('agent_name')}\n\n"
                f"Other agents can now send tasks to this agent."
            )
        else:
            view.add_error(f"Failed to start A2A server: {result.get('error')}")

    async def _handle_stop(self, view: "ResponseView") -> None:
        """Stop A2A gRPC server."""
        result = await self.bridge.stop_a2a_server()
        if result.get("success"):
            view.add_system_message("## 🛑 A2A Server Stopped")
        else:
            view.add_error(f"Failed to stop A2A server: {result.get('error')}")

    async def _handle_discover(self, view: "ResponseView") -> None:
        """Discover agents on network."""
        view.add_system_message("## 🔍 Discovering Agents...\n")

        agents = await self.bridge.discover_a2a_agents()

        if agents:
            lines = [f"Found {len(agents)} agent(s):\n"]
            for agent in agents:
                lines.append(f"### {agent.get('name')}")
                lines.append(f"  - **ID:** `{agent.get('agent_id')}`")
                lines.append(f"  - **Version:** {agent.get('version')}")
                lines.append(f"  - **URL:** `{agent.get('url')}`")
                if agent.get("description"):
                    lines.append(f"  - **Description:** {agent.get('description')}")
                lines.append("")
            view.append_chunk("\n".join(lines))
        else:
            view.append_chunk("No agents discovered. Try again or check network.\n")

    async def _handle_call(self, args: str, view: "ResponseView") -> None:
        """Send task to remote agent."""
        if not args:
            view.add_error("Usage: `/a2a call <agent_id> <task>`")
            return

        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            view.add_error("Usage: `/a2a call <agent_id> <task>`")
            return

        agent_id = parts[0]
        task = parts[1]

        view.add_system_message(f"## 📞 Calling Agent: {agent_id}\n")

        async for chunk in self.bridge.call_a2a_agent(agent_id, task):
            view.append_chunk(chunk)

    async def _handle_card(self, view: "ResponseView") -> None:
        """Show local agent card."""
        card = self.bridge.get_a2a_card()

        if card is None:
            view.add_system_message(
                "## 📇 Agent Card\n\n"
                "No local card configured. Start server first with `/a2a serve`."
            )
            return

        lines = ["## 📇 Local Agent Card\n"]
        lines.append(f"**Name:** {card.get('name')}")
        lines.append(f"**Agent ID:** `{card.get('agentId')}`")
        lines.append(f"**Version:** {card.get('version')}")
        lines.append(f"**Provider:** {card.get('provider')}")
        lines.append(f"**URL:** `{card.get('url')}`")
        lines.append(f"**Description:** {card.get('description')}")

        caps = card.get("capabilities", {})
        lines.append("\n**Capabilities:**")
        lines.append(f"  - Streaming: {caps.get('streaming', False)}")
        lines.append(f"  - Push Notifications: {caps.get('pushNotifications', False)}")
        lines.append(f"  - State History: {caps.get('stateTransitionHistory', False)}")

        skills = card.get("skills", [])
        if skills:
            lines.append(f"\n**Skills ({len(skills)}):**")
            for skill in skills[:5]:
                lines.append(f"  - `{skill.get('name')}`: {skill.get('description')}")

        view.add_system_message("\n".join(lines))

    async def _handle_sign(self, key_path: str, view: "ResponseView") -> None:
        """Sign agent card with JWS."""
        if not key_path:
            view.add_error("Usage: `/a2a sign <private_key_path>`")
            return

        result = await self.bridge.sign_a2a_card(key_path)

        if result.get("success"):
            view.add_system_message(
                "## ✅ Agent Card Signed\n\n"
                "Card has been signed with JWS. Other agents can verify your identity."
            )
        else:
            view.add_error(f"Failed to sign card: {result.get('error')}")

    async def _handle_agents(self, view: "ResponseView") -> None:
        """List discovered agents."""
        agents = self.bridge.get_discovered_agents()

        if not agents:
            view.add_system_message(
                "## 🤖 Discovered Agents\n\nNo agents discovered. Run `/a2a discover` first."
            )
            return

        lines = [f"## 🤖 Discovered Agents ({len(agents)})\n"]
        for agent in agents:
            lines.append(f"- **{agent.get('name')}** (`{agent.get('agent_id')}`)")
            lines.append(f"  URL: `{agent.get('url')}`")

        view.add_system_message("\n".join(lines))

    async def _handle_help(self, view: "ResponseView") -> None:
        """Show A2A command help."""
        view.add_system_message(
            "## 🤖 A2A Commands\n\n"
            "- `/a2a status` - Show server and discovery status\n"
            "- `/a2a serve [port]` - Start gRPC server (default: 50051)\n"
            "- `/a2a stop` - Stop gRPC server\n"
            "- `/a2a discover` - Discover agents on network\n"
            "- `/a2a agents` - List discovered agents\n"
            "- `/a2a call <agent_id> <task>` - Send task to agent\n"
            "- `/a2a card` - Show local agent card\n"
            "- `/a2a sign <key>` - Sign card with JWS"
        )

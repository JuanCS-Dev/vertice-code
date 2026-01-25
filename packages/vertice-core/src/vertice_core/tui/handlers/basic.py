"""
Basic Command Handler.

Handles: /help, /clear, /quit, /exit, /run, /read, /agents, /status,
         /tools, /palette, /history, /context, /context-clear,
         /providers, /model
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from vertice_core.tui.constants import HELP_TOPICS

if TYPE_CHECKING:
    from vertice_core.tui.app import QwenApp
    from vertice_core.tui.widgets.response_view import ResponseView


class BasicCommandHandler:
    """Handler for basic system commands."""

    def __init__(self, app: "QwenApp"):
        self.app = app

    @property
    def bridge(self):
        return self.app.bridge

    async def handle(self, command: str, args: str, view: "ResponseView") -> None:
        """Route to specific handler method."""
        handlers = {
            "/help": self._handle_help,
            "/clear": self._handle_clear,
            "/quit": self._handle_quit,
            "/exit": self._handle_quit,
            "/run": self._handle_run,
            "/read": self._handle_read,
            "/agents": self._handle_agents,
            "/status": self._handle_status,
            "/tools": self._handle_tools,
            "/palette": self._handle_palette,
            "/history": self._handle_history,
            "/context": self._handle_context,
            "/context-clear": self._handle_context_clear,
            "/prometheus": self._handle_prometheus,
            "/providers": self._handle_providers,
            "/model": self._handle_model,
        }

        handler = handlers.get(command)
        if handler:
            await handler(args, view)

    async def _handle_help(self, args: str, view: "ResponseView") -> None:
        """Handle /help command."""
        topic = args.lower().strip() if args else ""
        if topic in HELP_TOPICS:
            view.add_system_message(HELP_TOPICS[topic])
        else:
            # Fuzzy match topic
            matches = [k for k in HELP_TOPICS.keys() if k and topic in k]
            if matches:
                view.add_system_message(HELP_TOPICS[matches[0]])
            else:
                view.add_system_message(
                    f"❓ **Tópico não encontrado:** `{topic}`\n\n"
                    f"Tópicos disponíveis: `commands`, `agents`, `tools`, `keys`, `tips`\n\n"
                    f"Use `/help` para ver o menu principal."
                )

    async def _handle_clear(self, args: str, view: "ResponseView") -> None:
        """Handle /clear command."""
        # Skip confirmation if --force flag
        if args.strip() == "--force":
            self._do_clear(view)
            return

        # Show confirmation dialog
        from vertice_core.tui.widgets.modal import ConfirmDialog

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._do_clear(view)

        self.app.push_screen(
            ConfirmDialog(
                "This will clear all context and conversation history.\nThis cannot be undone.",
                title="Clear Session?",
                yes_label="Clear",
                no_label="Cancel",
                destructive=True,
            ),
            on_confirm,
        )

    def _do_clear(self, view: "ResponseView") -> None:
        """Execute clear operation."""
        # Clear UI
        view.clear_all()
        view.add_banner()

        # Clear LLM Context (Fix for "dirty context" issues)
        self.bridge.history.clear_context()
        view.add_system_message("🧹 **Session & Context Cleared**")

    async def _handle_quit(self, args: str, view: "ResponseView") -> None:
        """Handle /quit and /exit commands."""
        self.app.exit()

    async def _handle_run(self, args: str, view: "ResponseView") -> None:
        """Handle /run command."""
        if not args:
            view.add_error("Usage: /run <command>")
            return
        await self.app._execute_bash(args, view)

    async def _handle_read(self, args: str, view: "ResponseView") -> None:
        """Handle /read command."""
        if not args:
            view.add_error("Usage: /read <file>")
            return
        await self.app._read_file(args, view)

    async def _handle_agents(self, args: str, view: "ResponseView") -> None:
        """Handle /agents command."""
        agents_list = (
            "\n".join(
                [
                    f"- **{name}**: {info.description}"
                    for name, info in self.bridge.agents.AGENT_REGISTRY.items()
                ]
            )
            if hasattr(self.bridge.agents, "AGENT_REGISTRY")
            else "20 agents available"
        )
        view.add_system_message(f"## 🤖 Available Agents\n\n{agents_list}")

    async def _handle_status(self, args: str, view: "ResponseView") -> None:
        """Handle /status command."""
        # Get provider info dynamically
        if self.bridge.is_connected:
            provider_info = "✅ Connected"
            if hasattr(self.bridge.llm, "_vertice_coreent") and self.bridge.llm._vertice_coreent:
                current = self.bridge.llm._vertice_coreent.current_provider
                providers = self.bridge.llm._vertice_coreent.get_available_providers()
                if current:
                    provider_info = f"✅ {current.capitalize()}"
                elif providers:
                    provider_info = f"✅ {len(providers)} providers available"
            else:
                provider_info = "✅ Gemini"
        else:
            provider_info = "❌ Not connected"

        status_msg = (
            f"## 📊 Status\n\n"
            f"- **LLM:** {provider_info}\n"
            f"- **Governance:** {self.bridge.governance.get_status_emoji()}\n"
            f"- **Agents:** {len(self.bridge.agents.available_agents)} available\n"
            f"- **Tools:** {self.bridge.tools.get_tool_count()} loaded\n"
            f"- **Context:** {len(self.bridge.history.context)} messages\n"
        )
        view.add_system_message(status_msg)

    async def _handle_tools(self, args: str, view: "ResponseView") -> None:
        """Handle /tools command."""
        view.add_system_message(self.bridge.get_tool_list())

    async def _handle_palette(self, args: str, view: "ResponseView") -> None:
        """Handle /palette command."""
        if args:
            results = self.bridge.palette.search(args)
            if results:
                lines = ["## 🔍 Command Search Results\n"]
                for r in results:
                    kb = f" `{r.get('keybinding', '')}`" if r.get("keybinding") else ""
                    lines.append(f"- **{r['command']}**{kb}: {r['description']}")
                view.add_system_message("\n".join(lines))
            else:
                view.add_system_message(f"No commands found for: `{args}`")
        else:
            # Show popular commands
            results = self.bridge.palette.search("", max_results=15)
            lines = ["## ⚡ Command Palette\n", "Type `/palette <query>` to search.\n"]
            for r in results:
                kb = f" `{r.get('keybinding', '')}`" if r.get("keybinding") else ""
                lines.append(f"- **{r['command']}**{kb}: {r['description']}")
            view.add_system_message("\n".join(lines))

    async def _handle_history(self, args: str, view: "ResponseView") -> None:
        """Handle /history command."""
        if args:
            results = self.bridge.history.search_history(args)
        else:
            results = self.bridge.history.get_recent(15)

        if results:
            lines = ["## 📜 Command History\n"]
            for i, cmd in enumerate(results, 1):
                lines.append(f"{i}. `{cmd}`")
            view.add_system_message("\n".join(lines))
        else:
            view.add_system_message("No history found.")

    async def _handle_context(self, args: str, view: "ResponseView") -> None:
        """Handle /context command."""
        context = self.bridge.history.get_context()
        if context:
            lines = [f"## 💬 Conversation Context ({len(context)} messages)\n"]
            for i, msg in enumerate(context[-10:], 1):
                role = "👤 User" if msg["role"] == "user" else "🤖 Assistant"
                content = (
                    msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                )
                lines.append(f"**{role}:** {content}\n")
            view.add_system_message("\n".join(lines))
        else:
            view.add_system_message("No conversation context yet. Start chatting!")

    async def _handle_context_clear(self, args: str, view: "ResponseView") -> None:
        """Handle /context-clear command."""
        self.bridge.history.clear_context()
        view.add_success("Conversation context cleared.")

    async def _handle_prometheus(self, args: str, view: "ResponseView") -> None:
        """Handle /prometheus command."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0] if parts else "status"

        if subcommand == "status":
            # Show PROMETHEUS status
            if self.bridge._prometheus_client:
                status = self.bridge._prometheus_client.get_health_status()
                view.add_system_message(f"## 🔥 PROMETHEUS Status\n\n```json\n{status}\n```")
            else:
                view.add_system_message(
                    "## 🔥 PROMETHEUS Status\n\nNot initialized (will lazy load on first complex task)."
                )

        elif subcommand == "evolve":
            # Run evolution cycle
            iterations = int(parts[1]) if len(parts) > 1 else 5
            view.add_system_message(f"🧬 Starting evolution cycle ({iterations} iterations)...")

            # Ensure client exists
            if self.bridge._prometheus_client is None:
                from vertice_core.tui.core.prometheus_client import PrometheusClient

                self.bridge._prometheus_client = PrometheusClient()

            result = await self.bridge._prometheus_client.evolve(iterations)
            view.add_system_message(f"✅ Evolution complete:\n```json\n{result}\n```")

        elif subcommand == "memory":
            # Show memory status
            if self.bridge._prometheus_client and self.bridge._prometheus_client._provider:
                memory_status = self.bridge._prometheus_client._provider.get_status()
                view.add_system_message(
                    f"## 🧠 Memory Status\n\n```json\n{memory_status.get('memory', {})}\n```"
                )
            else:
                view.add_system_message("PROMETHEUS not initialized")

        elif subcommand == "enable":
            # Enable PROMETHEUS mode - sync with StatusBar
            self.bridge.prometheus_mode = True
            try:
                from vertice_core.tui.widgets.status_bar import StatusBar
                from vertice_core.tui.themes import ThemeManager

                status = self.app.query_one(StatusBar)
                status.prometheus_mode = True
                ThemeManager.save_prometheus_preference(True)
            except Exception as e:
                import logging

                logging.debug(f"StatusBar sync failed (non-critical): {e}")
            view.add_success("🔥 PROMETHEUS mode enabled. Self-evolution active.")

        elif subcommand == "disable":
            # Disable PROMETHEUS mode - sync with StatusBar
            self.bridge.prometheus_mode = False
            try:
                from vertice_core.tui.widgets.status_bar import StatusBar
                from vertice_core.tui.themes import ThemeManager

                status = self.app.query_one(StatusBar)
                status.prometheus_mode = False
                ThemeManager.save_prometheus_preference(False)
            except Exception as e:
                import logging

                logging.debug(f"StatusBar sync failed (non-critical): {e}")
            view.add_success("❄️ PROMETHEUS mode disabled. Using standard Gemini.")

        else:
            view.add_system_message(
                """
## 🔥 PROMETHEUS Commands
- `/prometheus status`   - Show system status
- `/prometheus evolve N` - Run N evolution iterations
- `/prometheus memory`   - Show memory status
- `/prometheus enable`   - Enable PROMETHEUS mode
- `/prometheus disable`  - Disable PROMETHEUS mode
"""
            )

    async def _handle_providers(self, args: str, view: "ResponseView") -> None:
        """Handle /providers command - Show all available LLM providers."""
        try:
            providers = self.bridge.llm.get_available_providers()
            status = self.bridge.llm.get_provider_status()

            lines = [
                "## 🌐 LLM Providers\n",
                (
                    "**Available providers:** " + ", ".join(providers)
                    if providers
                    else "No providers available"
                ),
                "\n### Status Report\n",
                f"```\n{status}\n```",
                "\n### Provider Priority (FREE FIRST)\n",
                "| Priority | Provider | Tier | Daily Limit |",
                "|----------|----------|------|-------------|",
                "| 1 | Groq | Free | 14,400 req |",
                "| 2 | Cerebras | Free | 1M tokens |",
                "| 3 | Mistral | Free | 1B tokens/month |",
                "| 4 | OpenRouter | Free | 200 req |",
                "| 5 | Gemini | API Key | Quota |",
                "| 6 | Vertex AI | Enterprise | GCP |",
                "| 7 | Azure OpenAI | Enterprise | Azure |",
                "\n**Tip:** Set API keys to enable more providers.",
            ]
            view.add_system_message("\n".join(lines))
        except Exception as e:
            view.add_error(f"Failed to get providers: {e}")

    async def _handle_model(self, args: str, view: "ResponseView") -> None:
        """Handle /model command - Show or switch model/provider."""
        if not args:
            # Show current model info
            current = self.bridge.llm.model_name
            providers = self.bridge.llm.get_available_providers()
            view.add_system_message(
                f"## 🤖 Current Model\n\n"
                f"- **Model:** `{current}`\n"
                f"- **Available Providers:** {', '.join(providers) if providers else 'None'}\n\n"
                f"Use `/model <name>` to switch providers.\n"
                f"Examples:\n"
                f"- `/model groq` - Switch to Groq (ultra-fast)\n"
                f"- `/model cerebras` - Switch to Cerebras (fastest)\n"
                f"- `/model vertex-ai` - Switch to Vertex AI (enterprise)\n"
            )
        else:
            # Switch to specified provider
            provider_name = args.strip().lower()
            try:
                if hasattr(self.bridge.llm, "_vertice_coreent") and self.bridge.llm._vertice_coreent:
                    client = self.bridge.llm._vertice_coreent
                    available = client.get_available_providers()

                    if provider_name in available:
                        # Switch provider
                        if client.set_preferred_provider(provider_name):
                            new_order = client.get_priority_order()
                            view.add_system_message(
                                f"## ✅ Switched to {provider_name}\n\n"
                                f"- **Active:** `{provider_name}`\n"
                                f"- **Priority:** {' → '.join(new_order)}\n"
                                f"- **Fallback:** Auto (if {provider_name} fails)"
                            )
                        else:
                            view.add_error(f"Failed to switch to `{provider_name}`")
                    else:
                        view.add_error(
                            f"Provider `{provider_name}` not available.\n"
                            f"Available: {', '.join(available)}"
                        )
                else:
                    view.add_system_message(
                        f"VerticeClient not active. Using direct {self.bridge.llm.model_name}"
                    )
            except Exception as e:
                view.add_error(f"Failed to switch: {e}")

"""
Agent Command Handler.

Handles: /plan, /execute, /architect, /review, /explore, /refactor,
         /test, /security, /docs, /perf, /devops, /justica, /sofia, /data
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView

logger = logging.getLogger(__name__)


class AgentCommandHandler:
    """Handler for agent invocation commands."""

    # Agents that need file context from working directory
    FILE_CONTEXT_AGENTS = {"reviewer", "refactorer", "security", "testing", "documentation", "performance"}

    # File extensions to include in context
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"}

    def __init__(self, app: "QwenApp"):
        self.app = app

    @property
    def bridge(self):
        return self.app.bridge

    def _build_context(self, agent_name: str) -> Dict[str, Any]:
        """
        Build context for agent execution.

        Detects files in current working directory for agents that need file context.
        Fixes critical bug where ReviewerAgent couldn't find files.

        Args:
            agent_name: Name of the agent being invoked

        Returns:
            Context dict with 'files', 'cwd', and metadata
        """
        cwd = Path.cwd()
        context: Dict[str, Any] = {
            "cwd": str(cwd),
            "files": [],
            "project_name": cwd.name,
        }

        # Only scan files for agents that need file context
        if agent_name not in self.FILE_CONTEXT_AGENTS:
            logger.debug(f"Agent '{agent_name}' doesn't need file context")
            return context

        try:
            # Find code files in current directory (non-recursive for performance)
            files: List[str] = []

            # First, check immediate directory
            for ext in self.CODE_EXTENSIONS:
                files.extend(str(f) for f in cwd.glob(f"*{ext}") if f.is_file())

            # Then check src/ or lib/ if they exist (common patterns)
            for subdir in ["src", "lib", "app", "core"]:
                subpath = cwd / subdir
                if subpath.exists():
                    for ext in self.CODE_EXTENSIONS:
                        files.extend(str(f) for f in subpath.glob(f"*{ext}") if f.is_file())

            # Limit to avoid overwhelming the agent
            MAX_FILES = 50
            if len(files) > MAX_FILES:
                logger.warning(f"Found {len(files)} files, limiting to {MAX_FILES}")
                files = files[:MAX_FILES]

            context["files"] = files
            context["file_count"] = len(files)

            logger.info(f"Built context for '{agent_name}': {len(files)} files in {cwd}")

        except Exception as e:
            logger.error(f"Failed to build file context: {e}")

        return context

    async def handle(
        self,
        command: str,
        args: str,
        view: "ResponseView"
    ) -> None:
        """Route to specific agent handler."""
        handlers = {
            "/plan": self._handle_plan,
            "/execute": self._handle_execute,
            "/architect": self._handle_architect,
            "/review": self._handle_review,
            "/explore": self._handle_explore,
            "/refactor": self._handle_refactor,
            "/test": self._handle_test,
            "/security": self._handle_security,
            "/docs": self._handle_docs,
            "/perf": self._handle_perf,
            "/devops": self._handle_devops,
            "/justica": self._handle_justica,
            "/sofia": self._handle_sofia,
            "/data": self._handle_data,
        }

        handler = handlers.get(command)
        if handler:
            await handler(args, view)

    async def _handle_plan(self, args: str, view: "ResponseView") -> None:
        """Handle /plan command with v6.1 sub-commands."""
        if args:
            args_lower = args.lower().strip()
            if args_lower.startswith("multi ") or args_lower == "multi":
                task = args[6:].strip() if args_lower.startswith("multi ") else ""
                await self._invoke_planner_v61("multi", task or "Generate multiple plans", view)
            elif args_lower.startswith("clarify ") or args_lower == "clarify":
                task = args[8:].strip() if args_lower.startswith("clarify ") else ""
                await self._invoke_planner_v61("clarify", task or "Clarify requirements", view)
            elif args_lower.startswith("explore ") or args_lower == "explore":
                task = args[8:].strip() if args_lower.startswith("explore ") else ""
                await self._invoke_planner_v61("explore", task or "Explore codebase", view)
            else:
                await self._invoke_agent("planner", args, view)
        else:
            await self._invoke_agent("planner", "Create a plan", view)

    async def _handle_execute(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("executor", args or "Execute task", view)

    async def _handle_architect(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("architect", args or "Analyze architecture", view)

    async def _handle_review(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("reviewer", args or "Review code", view)

    async def _handle_explore(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("explorer", args or "Explore codebase", view)

    async def _handle_refactor(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("refactorer", args or "Refactor code", view)

    async def _handle_test(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("testing", args or "Generate tests", view)

    async def _handle_security(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("security", args or "Security scan", view)

    async def _handle_docs(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("documentation", args or "Generate documentation", view)

    async def _handle_perf(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("performance", args or "Profile performance", view)

    async def _handle_devops(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("devops", args or "DevOps task", view)

    async def _handle_justica(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("justica", args or "Evaluate governance", view)

    async def _handle_sofia(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("sofia", args or "Provide counsel", view)

    async def _handle_data(self, args: str, view: "ResponseView") -> None:
        await self._invoke_agent("data", args or "Database analysis", view)

    async def _invoke_agent(
        self,
        agent_name: str,
        task: str,
        view: "ResponseView"
    ) -> None:
        """
        Invoke a specific agent with streaming response.

        Automatically builds context with files from current working directory
        for agents that need file context (reviewer, refactorer, etc).
        """
        self.app.is_processing = True
        view.start_thinking()

        status = self.app.query_one("StatusBar")
        status.mode = f"🤖 {agent_name.upper()}"

        # Build context with files from working directory
        context = self._build_context(agent_name)

        # Log context for debugging
        if context.get("files"):
            logger.debug(f"Invoking {agent_name} with {len(context['files'])} files from {context['cwd']}")
            view.append_chunk(f"📁 Found **{len(context['files'])} files** in `{context['project_name']}`\n\n")

        try:
            async for chunk in self.bridge.invoke_agent(agent_name, task, context):
                view.append_chunk(chunk)
                await asyncio.sleep(0)

            view.add_success(f"✓ {agent_name.title()}Agent complete")
            status.governance_status = self.bridge.governance.get_status_emoji()

        except Exception as e:
            view.add_error(f"Agent error: {e}")
            status.errors += 1
        finally:
            self.app.is_processing = False
            status.mode = "READY"
            view.end_thinking()

    async def _invoke_planner_v61(
        self,
        mode: str,
        task: str,
        view: "ResponseView"
    ) -> None:
        """Invoke Planner v6.1 with specific mode."""
        self.app.is_processing = True
        view.start_thinking()

        status = self.app.query_one("StatusBar")
        mode_labels = {
            "multi": "MULTI-PLAN",
            "clarify": "CLARIFY",
            "explore": "EXPLORE"
        }
        status.mode = f"🎯 PLANNER:{mode_labels.get(mode, mode.upper())}"

        try:
            if mode == "multi":
                async for chunk in self.bridge.invoke_planner_multi(task):
                    view.append_chunk(chunk)
                    await asyncio.sleep(0)
            elif mode == "clarify":
                async for chunk in self.bridge.invoke_planner_clarify(task):
                    view.append_chunk(chunk)
                    await asyncio.sleep(0)
            elif mode == "explore":
                async for chunk in self.bridge.invoke_planner_explore(task):
                    view.append_chunk(chunk)
                    await asyncio.sleep(0)
            else:
                view.add_error(f"Unknown planner mode: {mode}")
                return

            view.add_success(f"✓ Planner v6.1 ({mode}) complete")
            status.governance_status = self.bridge.governance.get_status_emoji()

        except Exception as e:
            view.add_error(f"Planner v6.1 error: {e}")
            status.errors += 1
        finally:
            self.app.is_processing = False
            status.mode = "READY"
            view.end_thinking()

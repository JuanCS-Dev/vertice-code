"""Command handling for Maestro Shell."""
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from vertice_cli.ui.command_palette import Command, CommandCategory

class CommandsMixin:
    """Handles slash commands and agent registration."""

    def _register_agent_commands(self):
        """Register agent commands in Command Palette for fuzzy search"""
        agent_commands = [
            Command(
                id="agent.executor",
                label="Execute Bash Command",
                description="Run system commands directly (executor agent)",
                category=CommandCategory.AGENT.value,
                keybinding=None,
                handler=lambda: self.orch.agents.get('executor'),
                priority=10
            ),
            Command(
                id="agent.planner",
                label="Plan Task",
                description="Break down complex tasks with GOAP planning",
                category=CommandCategory.AGENT.value,
                keybinding=None,
                handler=lambda: self.orch.agents.get('planner'),
                priority=9
            ),
            Command(
                id="agent.reviewer",
                label="Review Code",
                description="AST + Code Graph analysis for quality checks",
                category=CommandCategory.AGENT.value,
                keybinding=None,
                handler=lambda: self.orch.agents.get('reviewer'),
                priority=8
            ),
            Command(
                id="agent.refactorer",
                label="Refactor Code",
                description="Transactional code surgery with LibCST",
                category=CommandCategory.AGENT.value,
                keybinding=None,
                handler=lambda: self.orch.agents.get('refactorer'),
                priority=7
            ),
            Command(
                id="agent.explorer",
                label="Explore Codebase",
                description="Build knowledge graph and analyze dependencies",
                category=CommandCategory.AGENT.value,
                keybinding=None,
                handler=lambda: self.orch.agents.get('explorer'),
                priority=6
            ),
        ]

        for cmd in agent_commands:
            self.command_palette.register_command(cmd)

    def cmd(self, c: str) -> bool:
        """Handle slash commands"""

        if c in ['/q', '/quit', '/exit']:
            self.running = False
            return True

        if c in ['/c', '/clear']:
            self.c.clear()
            self.c.print("\n  VÉRTICE v10.0", style="bold cyan")
            self.c.print()
            return True

        if c in ['/h', '/help']:
            help_panel = Panel(
                """[bold]Commands:[/bold]\n"
                "  /quit, /exit, /q     quit MAESTRO\n"
                "  /clear, /c           clear screen\n"
                "  /help, /h            show this help\n"
                "  /agents              list available agents\n"
                "  /data                quick access to DataAgent\n"
                "  /commands [query]    fuzzy search commands\n"
                "  /permissions         manage command permissions\n"
                "  /metrics             show agent metrics\n"
                "\n[bold]Tip:[/bold] Type / and press TAB to see all commands\n"
                "\n[bold]Agent Triggers:[/bold]\n"
                "  "review..."      → Reviewer v5.0 (AST + LLM analysis)\n"
                "  "plan..."        → Planner v5.0 (GOAP planning)\n"
                "  "refactor..."    → Refactorer v8.0 (Transactional surgery)\n"
                "  "explore..."     → Explorer (Knowledge graph)\n"
                "  "database..."    → DataAgent v1.0 (Schema + Query optimization)\n"
                "  "run/exec..."    → Executor (bash commands)\n"
                "\n[bold]Examples:[/bold]\n"
                "  review vertice_cli/agents/base.py\n"
                "  plan implement user authentication\n"
                "  refactor extract method from process_payment\n"
                "  explore map the codebase\n"
                "  analyze schema for users table\n"
                "  optimize query SELECT * FROM orders\n"
                "  list running processes""",
                title="💡 Help",
                border_style="blue"
            )
            self.c.print()
            self.c.print(help_panel)
            self.c.print()
            return True

        if c == '/data':
            # Quick access to DataAgent with info panel
            info_panel = Panel(
                """[bold cyan]🗄️  DataAgent v1.0 - Database Operations[/bold cyan]\n\n[bold]Capabilities:[/bold]\n  • Schema Analysis (detect issues, recommend fixes)\n  • Query Optimization (70%+ improvements)\n  • Migration Planning (risk assessment + rollback)\n  • Extended Thinking (5000 token budget)\n\n[bold]Usage Examples:[/bold]\n  analyze schema for users table\n  optimize query SELECT * FROM orders WHERE status='pending'\n  plan migration to add email_verified column\n  review database indexes\n\n[bold]Quick Commands:[/bold]\n  database help              Show database-specific help\n  schema issues              Analyze current schema\n  query performance          Get query optimization tips\n\n[dim]💡 Tip: DataAgent automatically activates for database keywords
(schema, query, sql, migration, table, index, etc.)[/dim]""",
                title="🗄️  DataAgent Quick Reference",
                border_style="cyan"
            )
            self.c.print()
            self.c.print(info_panel)
            self.c.print()
            return True

        if c.startswith('/commands'):
            # Parse optional query: /commands [query]
            parts = c.split(maxsplit=1)
            query = parts[1] if len(parts) > 1 else ""

            # Get suggestions from command palette
            suggestions = self.command_palette.get_suggestions(query, max_results=10)

            if not suggestions:
                self.c.print("\n[dim]No commands found[/dim]\n")
                return True

            # Display as table
            table = Table(title="🔍 Command Palette", border_style="cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Command", style="bold bright_cyan")
            table.add_column("Description", style="white")
            table.add_column("Category", style="dim")

            for idx, cmd in enumerate(suggestions, 1):
                table.add_row(
                    str(idx),
                    cmd['command'],
                    cmd['description'],
                    cmd['category']
                )

            self.c.print()
            self.c.print(table)
            self.c.print()
            self.c.print("[dim]Tip: Type [bold]/commands [query][/bold] to fuzzy search[/dim]")
            self.c.print()
            return True

        if c == '/agents':
            tree = Tree("[bold cyan]🤖 Available Agents (v6.0)[/bold cyan]")

            executor = tree.add("[bold white]💻 SimpleExecutor[/bold white]")
            executor.add("[dim]Direct bash command execution[/dim]")
            executor.add("[dim]System queries & file operations[/dim]")

            planner = tree.add("[bold yellow]⚡ Planner v5.0[/bold yellow]")
            planner.add("[dim]GOAP-based task decomposition[/dim]")
            planner.add("[dim]Dependency analysis & parallel execution[/dim]")

            reviewer = tree.add("[bold green]🔍 Reviewer v5.0[/bold green]")
            reviewer.add("[dim]AST + Code Graph analysis[/dim]")
            reviewer.add("[dim]Security, Performance, Logic checks[/dim]")

            refactorer = tree.add("[bold magenta]🔧 Refactorer v8.0[/bold magenta]")
            refactorer.add("[dim]Transactional code surgery[/dim]")
            refactorer.add("[dim]LibCST format preservation[/dim]")

            explorer = tree.add("[bold blue]🗺️ Explorer[/bold blue]")
            explorer.add("[dim]Knowledge graph construction[/dim]")
            explorer.add("[dim]Blast radius analysis[/dim]")

            data = tree.add("[bold cyan]🗄️ DataAgent v1.0[/bold cyan]")
            data.add("[dim]Schema analysis & optimization[/dim]")
            data.add("[dim]Query optimization (70%+ improvements)[/dim]")
            data.add("[dim]Migration planning with rollback[/dim]")
            data.add("[dim]Extended thinking (5000 token budget)[/dim]")

            self.c.print()
            self.c.print(tree)
            self.c.print()
            return True

        if c == '/permissions':
            # Get PermissionManager from executor
            try:
                executor_agent = self.orch.agents.get('executor')
                if not executor_agent or not hasattr(executor_agent, 'permission_manager'):
                    self.c.print("[red]❌ Permission manager not available[/red]\n")
                    return True

                pm = executor_agent.permission_manager

                # Title banner
                self.c.print()
                self.c.print(Panel(
                    "[bold bright_cyan]🔐 Permission Configuration[/bold bright_cyan]\n" \
                    "[dim]Based on Claude Code (Nov 2025) + OWASP Best Practices[/dim]",
                    border_style="cyan"
                ))
                self.c.print()

                # Get config summary
                summary = pm.get_config_summary()

                # Status table
                status_table = Table(show_header=False, box=None, padding=(0, 2))
                status_table.add_column("Label", style="dim")
                status_table.add_column("Value", style="bold")

                status_table.add_row("Mode", "[green]Safe Mode Enabled[/green]" if pm.safe_mode else "[red]Safe Mode Disabled[/red]")
                status_table.add_row("Allow Rules", f"[cyan]{summary['allow_count']}[/cyan] patterns")
                status_table.add_row("Deny Rules", f"[red]{summary['deny_count']}[/red] patterns")
                status_table.add_row("Auto-approve Read-only", "[green]Yes[/green]" if summary['auto_approve_enabled'] else "[dim]No[/dim]")
                status_table.add_row("Audit Logging", "[green]Enabled[/green]" if summary['audit_enabled'] else "[dim]Disabled[/dim]")

                self.c.print(status_table)
                self.c.print()

                # Allow list table
                allow_table = Table(title="✅ Allow List (Auto-approved)", border_style="green", show_lines=True)
                allow_table.add_column("Pattern", style="green", overflow="fold")

                for pattern in pm.config["permissions"]["allow"][:20]:  # Show first 20
                    allow_table.add_row(pattern)

                if len(pm.config["permissions"]["allow"]) > 20:
                    allow_table.add_row(f"[dim]... and {len(pm.config['permissions']['allow']) - 20} more[/dim]")

                self.c.print(allow_table)
                self.c.print()

                # Deny list table
                deny_table = Table(title="🛑 Deny List (Blocked)", border_style="red", show_lines=True)
                deny_table.add_column("Pattern", style="red", overflow="fold")

                for pattern in pm.config["permissions"]["deny"][:20]:  # Show first 20
                    deny_table.add_row(pattern)

                if len(pm.config["permissions"]["deny"]) > 20:
                    deny_table.add_row(f"[dim]... and {len(pm.config['permissions']['deny']) - 20} more[/dim]")

                self.c.print(deny_table)
                self.c.print()

                # Config file locations
                self.c.print(Panel(
                    "[bold]📁 Config File Hierarchy[/bold] [dim](precedence: Local > Project > User)[/dim]\n\n" +
                    "\n".join([
                        f"{'✅' if info['exists'] else '❌'} [bold]{'Local:' if 'local' in name else 'Project:' if 'project' in name else 'User:'}[/bold] [dim]{info['path']}[/dim]"
                        for name, info in summary['config_files'].items()
                    ]),
                    border_style="dim"
                ))
                self.c.print()

                # Audit log location
                if summary['audit_enabled']:
                    audit_file = pm.config["logging"]["auditFile"]
                    self.c.print(f"[dim]📝 Audit log: {audit_file}[/dim]\n")

                # Help text
                self.c.print("[dim]Tip: Use [bold]'always'[/bold] when approving commands to add them to the allow list[/dim]\n")

            except Exception as e:
                self.c.print(f"[red]❌ Error displaying permissions: {e}[/red]\n")

            return True

        if c == '/metrics':
            # Display NextGen Executor metrics
            try:
                executor_agent = self.orch.agents.get('executor')
                if not executor_agent or not hasattr(executor_agent, 'get_metrics'):
                    self.c.print("[red]❌ Metrics not available[/red]\n")
                    return True

                metrics = executor_agent.get_metrics()

                # Title banner
                self.c.print()
                self.c.print(Panel(
                    "[bold bright_cyan]📊 NextGen Executor Metrics[/bold bright_cyan]\n" \
                    "[dim]Real-time performance and usage statistics[/dim]",
                    border_style="cyan"
                ))
                self.c.print()

                # Execution metrics table
                exec_table = Table(title="Execution Statistics", border_style="green")
                exec_table.add_column("Metric", style="cyan", no_wrap=True)
                exec_table.add_column("Value", style="bold white")
                exec_table.add_column("Status", style="green")

                success_rate = metrics.get("success_rate", 0)
                status_emoji = "✅" if success_rate > 95 else "⚠️" if success_rate > 80 else "❌"

                exec_table.add_row(
                    "Total Executions",
                    str(metrics.get("executions", 0)),
                    ""
                )
                exec_table.add_row(
                    "Success Rate",
                    f"{success_rate:.2f}%",
                    status_emoji
                )
                exec_table.add_row(
                    "Average Latency",
                    f"{metrics.get('avg_latency', 0):.3f}s",
                    "⚡" if metrics.get('avg_latency', 0) < 0.5 else "🐌"
                )
                exec_table.add_row(
                    "Total Runtime",
                    f"{metrics.get('total_time', 0):.2f}s",
                    ""
                )

                self.c.print(exec_table)
                self.c.print()

                # Token usage table
                token_usage = metrics.get("token_usage", {})
                token_table = Table(title="Token Usage (MCP Pattern)", border_style="yellow")
                token_table.add_column("Type", style="cyan")
                token_table.add_column("Count", style="bold white")

                token_table.add_row("Input Tokens", str(token_usage.get("input", 0)))
                token_table.add_row("Output Tokens", str(token_usage.get("output", 0)))
                token_table.add_row("Total Tokens", f"[bold]{token_usage.get('total', 0)}[/bold]")

                self.c.print(token_table)
                self.c.print()

                # Footer with timestamp
                last_updated = metrics.get("last_updated", "N/A")
                self.c.print(f"[dim]Last updated: {last_updated}[/dim]\n")

            except Exception as e:
                self.c.print(f"[red]❌ Error displaying metrics: {e}[/red]\n")

            return True

        return False

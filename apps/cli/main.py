"""
Vértice - Unified Entry Point
==============================

Single command with multiple modes:
    vertice                 # Interactive TUI (default - 30 FPS)
    vertice chat "message"  # One-shot message
    vertice -p "prompt"     # Headless mode (CI/CD)
    vertice serve           # MCP server mode
    vertice shell           # Legacy shell mode

Philosophy: Sovereign Intelligence & Tactical Execution.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, TypeVar, Coroutine, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run async code safely, handling existing event loops.

    This prevents "asyncio.run() cannot be called from a running event loop"
    errors that occur when calling asyncio.run() from within an async context.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already have a loop - use run_until_complete or create_task
    if loop.is_running():
        # We're in a running loop (e.g., called from TUI)
        # Create a new loop in a new thread is one option,
        # but simpler is to use nest_asyncio or return a task
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


def validate_output_path(path_str: str) -> Path:
    """Validate output path is safe and allowed."""
    path = Path(path_str).resolve()
    cwd = Path.cwd().resolve()

    # Check 1: Must be within current working directory tree
    try:
        path.relative_to(cwd)
    except ValueError:
        raise ValueError(
            f"Security: Output path must be within current directory.\n"
            f"  Requested: {path}\n"
            f"  Allowed: {cwd} and subdirectories"
        )

    # Check 2: Forbidden paths/files
    forbidden_patterns = [".git", ".env", ".ssh", "id_rsa", "id_ed25519", "authorized_keys"]
    path_parts = path.parts

    for pattern in forbidden_patterns:
        if any(pattern in part for part in path_parts):
            raise ValueError(
                f"Security: Cannot write to protected path containing '{pattern}': {path}"
            )

    # Check 3: Parent directory must exist
    if not path.parent.exists():
        raise FileNotFoundError(
            f"Parent directory does not exist: {path.parent}\n"
            f"Create it first with: mkdir -p {path.parent}"
        )

    return path


# Create CLI app
app = typer.Typer(
    name="vertice",
    help="Vértice - Enterprise Multi-LLM Orchestration & Agentic Intelligence",
    add_completion=True,
    invoke_without_command=True,  # Allow running without subcommand
)

console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print("[bold cyan]Vértice[/bold cyan] v1.0.0")
        console.print("[dim]Enterprise Multi-LLM Orchestration & Agentic Intelligence[/dim]")
        console.print("[dim]Operando sob a CONSTITUIÇÃO VÉRTICE v3.0[/dim]")
        console.print("\n[bold]Available Modes:[/bold]")
        console.print("  vertice          → Interactive TUI (Executor Tático)")
        console.print("  vertice chat     → One-shot interaction")
        console.print("  vertice explain  → Explain code file")
        console.print("  vertice generate → Generate code")
        console.print("  vertice serve    → MCP Server Mode")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Option(
        None, "-p", "--prompt", help="Run in headless mode with given prompt"
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-o", help="Output format: text, json, stream-json"
    ),
    max_turns: int = typer.Option(
        10, "--max-turns", help="Maximum tool execution turns in headless mode"
    ),
    allowed_tools: Optional[List[str]] = typer.Option(
        None, "--allow-tool", help="Restrict to specific tools (can repeat)"
    ),
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Vértice - Enterprise Multi-LLM Orchestration.

    Operacional como Executor Tático sob a Constituição Vértice v3.0.

    Run without arguments to start the interactive TUI (30 FPS optimized).
    Use -p for headless mode (CI/CD, scripts, automation).

    Examples:
        vertice                           # Start TUI (Default)
        vertice -p "Check security"       # Headless one-shot
        vertice chat "Explain this code"  # Simple one-shot
        vertice status                    # Check system integrity
    """
    # Register providers with vertice_core (Dependency Injection)
    try:
        from vertice_core.providers.register import ensure_providers_registered

        ensure_providers_registered()
    except ImportError:
        pass

    # If a subcommand is being invoked, skip default behavior
    if ctx.invoked_subcommand is not None:
        return

    # Headless mode
    if prompt:
        run_async(
            _run_headless(
                prompt=prompt,
                output_format=output_format,
                max_turns=max_turns,
                allowed_tools=allowed_tools,
            )
        )
        return

    # Default: Interactive TUI
    _run_tui()


def _run_tui():
    """Run the interactive Textual TUI."""
    try:
        from vertice_core.ui_launcher import launch_tui

        launch_tui()
    except ImportError as e:
        console.print(f"[red]Error importing TUI:[/red] {e}")
        console.print("[dim]Falling back to shell_main...[/dim]")
        try:
            from vertice_core.shell_main import main as shell_main

            run_async(shell_main())
        except ImportError:
            console.print("[red]No shell available. Install textual:[/red]")
            console.print("  pip install textual")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


async def _run_headless(
    prompt: str,
    output_format: str = "text",
    max_turns: int = 10,
    allowed_tools: Optional[List[str]] = None,
):
    """
    Run in headless mode for CI/CD and automation.

    No interactive UI - just execute and output.
    """
    import json

    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        if not bridge.is_connected:
            if output_format == "json":
                print(json.dumps({"success": False, "error": "LLM not configured"}))
            else:
                console.print("[red]Error:[/red] LLM not configured. Set GEMINI_API_KEY.")
            raise typer.Exit(1)

        # Collect response
        response_parts = []
        tool_results = []

        async for chunk in bridge.chat(prompt):
            if output_format == "stream-json":
                # Stream JSON events
                print(json.dumps({"type": "chunk", "data": chunk}))
            elif output_format == "text":
                # Print as it streams
                print(chunk, end="", flush=True)

            response_parts.append(chunk)

        full_response = "".join(response_parts)

        if output_format == "json":
            # Final JSON output
            result = {
                "success": True,
                "response": full_response,
                "tool_results": tool_results,
            }
            print(json.dumps(result, indent=2))
        elif output_format == "stream-json":
            # Final event
            print(json.dumps({"type": "complete", "success": True}))
        elif output_format == "text":
            print()  # Final newline

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    transport: str = typer.Option(
        "sse", "--transport", "-t", help="Transport mode: sse (default) or stdio"
    ),
):
    """Start as MCP server."""
    console.print(
        f"[bold cyan]🔌 Starting MCP Server at {host}:{port} ({transport})...[/bold cyan]"
    )

    try:
        from vertice_core.cli_mcp import main as mcp_main

        # NOTE: cli_mcp.main() is a sync entrypoint that internally manages asyncio.
        mcp_main(host=host, port=port, transport=transport)
    except ImportError as e:
        console.print("[red]Error:[/red] MCP dependencies not installed")
        console.print(f"[dim]Details: {e}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def shell():
    """Start interactive shell (Legacy)."""
    console.print("[bold cyan]🐚 Starting shell...[/bold cyan]")

    try:
        from vertice_core.shell_main import main as shell_main

        run_async(shell_main())
    except ImportError as e:
        console.print(f"[red]Error:[/red] Shell not available: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send"),
    no_context: bool = typer.Option(False, "--no-context", help="Disable project context"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Send a single message (one-shot mode)."""
    run_async(
        _run_headless(
            prompt=message,
            output_format="json" if json_output else "text",
        )
    )


@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to file to explain"),
    context_files: Optional[List[str]] = typer.Option(
        None, "--context", help="Additional context files"
    ),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model to use"),
):
    """Explain code from a file."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        if model:
            bridge.set_model(model)

        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found:[/red] {file_path}")
            raise typer.Exit(1)

        content = path.read_text(encoding="utf-8")
        prompt = f"Please explain this code:\n\nFile: {file_path}\n```\n{content}\n```"

        if context_files:
            prompt += "\n\nContext:"
            for ctx_file in context_files:
                try:
                    ctx_content = Path(ctx_file).read_text(encoding="utf-8")
                    prompt += f"\nFile: {ctx_file}\n```\n{ctx_content}\n```"
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not read context file {ctx_file}: {e}[/yellow]"
                    )

        console.print(f"\n[bold blue]🔍 Explaining:[/bold blue] {file_path}\n")

        run_async(_run_headless(prompt=prompt, output_format="text"))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="What code to generate"),
    context_files: Optional[List[str]] = typer.Option(
        None, "--context", help="Context files for reference"
    ),
    output: Optional[str] = typer.Option(None, "--output", help="Save to file"),
    stream: bool = typer.Option(True, "--stream", help="Stream output"),
):
    """Generate code based on a prompt."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        full_prompt = f"Generate code for: {prompt}"

        if context_files:
            full_prompt += "\n\nContext:"
            for ctx_file in context_files:
                try:
                    ctx_content = Path(ctx_file).read_text(encoding="utf-8")
                    full_prompt += f"\nFile: {ctx_file}\n```\n{ctx_content}\n```"
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not read context file {ctx_file}: {e}[/yellow]"
                    )

        console.print(f"\n[bold blue]✨ Generating:[/bold blue] {prompt}\n")

        # Capture output if saving to file
        captured_output = []

        async def run_gen():
            async for chunk in bridge.chat(full_prompt):
                if stream:
                    print(chunk, end="", flush=True)
                captured_output.append(chunk)

        run_async(run_gen())
        print()  # Newline

        if output:
            try:
                safe_path = validate_output_path(output)
                full_text = "".join(captured_output)
                safe_path.write_text(full_text, encoding="utf-8")
                console.print(f"[green]✅ Saved to:[/green] {output}")
            except Exception as e:
                console.print(f"[red]Error saving file:[/red] {e}")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def config():
    """Show current configuration."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        console.print("\n[bold]📋 Configuration:[/bold]\n")
        console.print(f"  Model: {bridge.get_model_name()}")
        console.print(f"  Auth: {bridge.get_auth_status().get('provider', 'unknown')}")

        # Check MCP
        try:
            # Try CLI core MCP client
            from vertice_core.core.mcp import create_mcp_client

            mcp = create_mcp_client()
            health = mcp.get_health_status()
            console.print(f"  MCP Tools: {health['tools_registered']}")
        except Exception as e:
            console.print(f"  MCP Tools: Not configured ({e})")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """Show system status."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        console.print("\n[bold cyan]Vértice System Status[/bold cyan]\n")

        # LLM Status
        if bridge.is_connected:
            console.print(f"[green]✅ LLM:[/green] Connected ({bridge.llm.model_name})")
        else:
            console.print("[red]❌ LLM:[/red] Not configured")

        # Agents
        agent_count = len(bridge.agents.available_agents)
        console.print(f"[green]🤖 Agents:[/green] {agent_count} available")

        # Tools
        tool_count = bridge.tools.get_tool_count()
        console.print(f"[green]🔧 Tools:[/green] {tool_count} loaded")

        # Governance
        gov_status = bridge.governance.get_status_emoji()
        console.print(f"[green]👀 Governance:[/green] {gov_status}")

        # Context
        context_count = len(bridge.history.context)
        console.print(f"[green]💬 Context:[/green] {context_count} messages")

        console.print()

    except Exception as e:
        console.print(f"[red]Error getting status:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def agents():
    """List available agents."""
    try:
        from vertice_core.ui_launcher import get_agent_registry

        AGENT_REGISTRY = get_agent_registry()

        table = Table(title="Vértice Agent Registry")
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Capabilities", style="dim")

        for name, info in AGENT_REGISTRY.items():
            caps = ", ".join(info.capabilities[:3])
            if len(info.capabilities) > 3:
                caps += "..."
            table.add_row(name, info.role, info.description, caps)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def tools():
    """List available tools."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()
        console.print(bridge.get_tool_list())

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Session management commands
sessions_app = typer.Typer(name="sessions", help="Manage saved sessions")
app.add_typer(sessions_app, name="sessions")


@sessions_app.command("list")
def list_sessions(
    limit: int = typer.Option(10, "--limit", help="Number of sessions to show"),
):
    """List saved sessions."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        sessions = bridge.list_sessions(limit=limit)

        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        table = Table(title=f"Saved Sessions (Top {len(sessions)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Date", style="magenta")
        table.add_column("Messages", justify="right", style="green")
        table.add_column("File", style="dim")

        for session in sessions:
            table.add_row(
                session.get("session_id", "unknown"),
                session.get("timestamp", ""),
                str(session.get("message_count", 0)),
                session.get("file", ""),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@sessions_app.command("show")
def show_session(session_id: str):
    """Show session details."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        data = bridge.history.load_session(session_id)

        tree = Tree(f"[bold cyan]Session: {data.get('session_id')}[/bold cyan]")
        tree.add(f"Timestamp: {data.get('timestamp')}")
        tree.add(f"Messages: {data.get('message_count')}")

        console.print(tree)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@sessions_app.command("delete")
def delete_session(
    session_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a session."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        if not force:
            if not typer.confirm(f"Delete session {session_id}?"):
                raise typer.Abort()

        if bridge.history.delete_session(session_id):
            console.print(f"[green]Session {session_id} deleted[/green]")
        else:
            console.print(f"[red]Session {session_id} not found[/red]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@sessions_app.command("cleanup")
def cleanup_sessions(
    days: int = typer.Option(30, "--days", help="Delete sessions older than N days"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clean up old sessions."""
    try:
        from vertice_core.ui_launcher import get_bridge

        bridge = get_bridge()

        if not force:
            if not typer.confirm(f"Delete sessions older than {days} days?"):
                raise typer.Abort()

        # Iterate and delete (since HistoryManager might not have cleanup method)
        # Note: HistoryManager.list_sessions returns session info dicts
        all_sessions = bridge.list_sessions(limit=1000)
        deleted_count = 0
        now = datetime.now()

        for s in all_sessions:
            try:
                ts_str = s.get("timestamp")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str)
                    age = now - ts
                    if age.days > days:
                        sid = s.get("session_id")
                        if sid and bridge.history.delete_session(sid):
                            deleted_count += 1
            except Exception as e:
                # Only print in verbose mode to avoid noise
                if os.environ.get("VERTICE_DEBUG"):
                    console.print(f"[dim]Error during cleanup: {e}[/dim]")
                continue

        console.print(f"[green]Deleted {deleted_count} old sessions[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Skills management commands
skills_app = typer.Typer(name="skills", help="Manage static skills (SOPs)")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def list_skills():
    """List available static skills."""
    try:
        from vertice_core.core.skill_loader import SkillLoader
        from rich.table import Table

        loader = SkillLoader()
        skills = loader.load_all()

        if not skills:
            console.print("[yellow]No skills found in skills/ directory[/yellow]")
            return

        table = Table(title="Available Skills (SOPs)")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Path", style="dim")

        for name, skill in skills.items():
            table.add_row(name, skill.description, str(skill.path))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing skills:[/red] {e}")
        raise typer.Exit(1)


@skills_app.command("show")
def show_skill(name: str):
    """Show detailed skill content."""
    try:
        from vertice_core.core.skill_loader import SkillLoader
        from rich.markdown import Markdown

        loader = SkillLoader()
        skills = loader.load_all()
        skill = skills.get(name)

        if not skill:
            console.print(f"[red]Skill '{name}' not found[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]Skill: {skill.name}[/bold cyan]")
        console.print(f"[dim]{skill.path}[/dim]\n")
        console.print(Markdown(skill.content))

    except Exception as e:
        console.print(f"[red]Error showing skill:[/red] {e}")
        raise typer.Exit(1)


def cli_main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli_main()

"""Command-line interface for qwen-dev-cli."""

import asyncio
import json
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.llm import llm_client
from .core.context import context_builder
from .core.mcp import mcp_manager
from .core.config import config

app = typer.Typer(
    name="qwen-dev",
    help="AI-Powered Code Assistant with MCP Integration",
    add_completion=False
)
console = Console()


@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to file to explain"),
    context_files: Optional[List[str]] = typer.Option(
        None, "--context", help="Additional context files"
    ),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model to use"),
):
    """Explain code from a file."""
    console.print(f"\n[bold blue]🔍 Explaining:[/bold blue] {file_path}\n")
    
    # Read main file
    success, content, error = context_builder.read_file(file_path)
    
    if not success:
        console.print(f"[bold red]❌ Error:[/bold red] {error}")
        raise typer.Exit(1)
    
    # Add context files if provided
    if context_files:
        console.print(f"[dim]📂 Loading context files...[/dim]")
        results = context_builder.add_files(context_files)
        for file, result in results.items():
            console.print(f"  {result}")
    
    # Build prompt
    prompt = f"Please explain this code:\n\n```\n{content}\n```"
    
    if context_files:
        context = context_builder.get_context()
        prompt = context_builder.inject_to_prompt(prompt)
    
    # Generate explanation
    with console.status("[bold green]Generating explanation...", spinner="dots"):
        response = asyncio.run(llm_client.generate(prompt))
    
    console.print("\n[bold green]📝 Explanation:[/bold green]\n")
    console.print(Markdown(response))
    
    # Clear context for next use
    context_builder.clear()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="What code to generate"),
    context_files: Optional[List[str]] = typer.Option(
        None, "--context", help="Context files for reference"
    ),
    output: Optional[str] = typer.Option(None, "--output", help="Save to file"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream output"),
):
    """Generate code based on a prompt."""
    console.print(f"\n[bold blue]✨ Generating:[/bold blue] {prompt}\n")
    
    # Add context files if provided
    if context_files:
        console.print(f"[dim]📂 Loading context files...[/dim]")
        results = context_builder.add_files(context_files)
        for file, result in results.items():
            console.print(f"  {result}")
        
        context = context_builder.get_context()
        prompt = context_builder.inject_to_prompt(prompt)
    
    # Generate code
    console.print("[bold green]📝 Generated Code:[/bold green]\n")
    
    if stream:
        # Stream output
        async def stream_generation():
            async for chunk in llm_client.stream_chat(prompt):
                console.print(chunk, end="")
        
        asyncio.run(stream_generation())
    else:
        # Non-streaming
        with console.status("[bold green]Generating code...", spinner="dots"):
            response = asyncio.run(llm_client.generate(prompt))
        console.print(Markdown(response))
    
    console.print("\n")
    
    # Save to file if requested
    if output:
        Path(output).write_text(response)
        console.print(f"[bold green]✅ Saved to:[/bold green] {output}")
    
    # Clear context
    context_builder.clear()


@app.command()
def serve(
    port: int = typer.Option(7860, "--port", help="Port for web UI"),
    share: bool = typer.Option(False, "--share", help="Create public share link"),
):
    """Start the Gradio web UI."""
    console.print(f"\n[bold blue]🚀 Starting web UI on port {port}...[/bold blue]\n")
    
    # Import here to avoid loading Gradio unless needed
    try:
        from .ui import create_ui
        
        demo = create_ui()
        demo.launch(server_port=port, share=share)
        
    except ImportError as e:
        console.print(f"[bold red]❌ Error:[/bold red] Gradio not installed")
        console.print(f"[dim]Install with: pip install gradio>=6.0.0[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def chat(
    message: Optional[str] = typer.Option(None, "--message", help="Single message (non-interactive)"),
    no_context: bool = typer.Option(False, "--no-context", help="Disable project context"),
    output_file: Optional[str] = typer.Option(None, "--output", help="Save output to file"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Start interactive chat or execute single message.
    
    Examples:
        qwen chat                                        # Interactive mode
        qwen chat --message "list all Python files"      # Single command
        qwen chat --message "show git status" --json     # JSON output
        qwen chat --message "create README" --output result.txt
    """
    if message:
        # Non-interactive mode
        from .core.single_shot import execute_single_shot
        
        console.print(f"[dim]Executing:[/dim] {message}\n")
        
        # Execute
        result = asyncio.run(execute_single_shot(
            message,
            include_context=not no_context
        ))
        
        # Format output
        if json_output:
            output = json.dumps(result, indent=2)
        else:
            output = result['output']
            
            if not result['success'] and result['errors']:
                output += '\n\n[red]Errors:[/red]\n'
                output += '\n'.join(f"  - {err}" for err in result['errors'])
        
        # Save to file or print
        if output_file:
            Path(output_file).write_text(output)
            console.print(f"[green]✓ Output saved to:[/green] {output_file}")
        else:
            if json_output:
                console.print(output)
            else:
                from rich.markdown import Markdown
                console.print(Markdown(output))
        
        # Exit with appropriate code
        raise typer.Exit(0 if result['success'] else 1)
    
    else:
        # Interactive mode - launch shell
        console.print("\n[bold blue]🚀 Starting interactive shell...[/bold blue]\n")
        console.print("[dim]Type 'quit' or press Ctrl+D to exit[/dim]\n")
        
        try:
            from .shell import main as shell_main
            asyncio.run(shell_main())
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye! 👋[/yellow]\n")
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}\n")
            raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    console.print("\n[bold]qwen-dev-cli[/bold] v0.1.0")
    console.print("AI-Powered Code Assistant with MCP Integration")
    console.print("\n[dim]Powered by:[/dim]")
    console.print(f"  • Model: {config.hf_model}")
    console.print(f"  • MCP: {'Enabled' if mcp_manager.enabled else 'Disabled'}")
    console.print()


@app.command()
def config_show():
    """Show current configuration."""
    console.print("\n[bold]📋 Configuration:[/bold]\n")
    
    # LLM settings
    console.print("[bold blue]LLM Settings:[/bold blue]")
    console.print(f"  Model: {config.hf_model}")
    console.print(f"  Max Tokens: {config.max_tokens}")
    console.print(f"  Temperature: {config.temperature}")
    console.print(f"  Streaming: {config.stream}")
    
    # Context settings
    console.print("\n[bold blue]Context Settings:[/bold blue]")
    console.print(f"  Max Files: {config.max_context_files}")
    console.print(f"  Max File Size: {config.max_file_size_kb}KB")
    
    # MCP settings
    console.print("\n[bold blue]MCP Settings:[/bold blue]")
    stats = mcp_manager.get_stats()
    console.print(f"  Enabled: {stats['enabled']}")
    console.print(f"  Root Dir: {stats['root_dir']}")
    console.print(f"  Files in Context: {stats['files']}")
    
    console.print()


@app.command()
def shell():
    """Start interactive shell with tool-based architecture."""
    from .shell import InteractiveShell
    
    console.print("[cyan]Starting interactive shell...[/cyan]")
    
    try:
        shell_instance = InteractiveShell()
        asyncio.run(shell_instance.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shell interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()

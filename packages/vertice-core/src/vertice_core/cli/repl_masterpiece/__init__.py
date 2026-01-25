"""
REPL MASTERPIECE - A DIVINE CODING EXPERIENCE

"Perfeição não é quando não há nada a adicionar,
mas quando não há nada a remover." - Antoine de Saint-Exupéry

Features:
- Streaming que parece mágica
- Feedback imediato e satisfatório
- Comandos que FUNCIONAM na primeira vez
- Visual que inspira criatividade
- Performance que impressiona

Architecture:
    - completer.py: SmartCompleter with fuzzy matching
    - commands.py: Command definitions and metadata
    - handlers.py: Command handler functions
    - agent_adapter.py: Agent registration and formatting
    - tools.py: Tool execution handlers
    - streaming.py: Streaming response handler
    - natural.py: Natural language processing
    - repl.py: Main MasterpieceREPL class

Usage:
    from vertice_core.cli.repl_masterpiece import start_masterpiece_repl
    start_masterpiece_repl()

Soli Deo Gloria
"""

import sys
import warnings

from rich.console import Console

from .repl import MasterpieceREPL


def start_masterpiece_repl() -> None:
    """Entry point for MasterpieceREPL."""
    # Suppress aiohttp cleanup warnings
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", message=".*Unclosed.*")
    warnings.filterwarnings("ignore", message=".*unclosed.*")

    console = Console()

    try:
        repl = MasterpieceREPL()
        repl.run()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]👋 Goodbye![/bold yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]\n")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]\n")
        sys.exit(1)


__all__ = [
    "MasterpieceREPL",
    "start_masterpiece_repl",
]

"""CLI package for Juan-Dev-Code"""

# Setup logging FIRST
from vertice_core.core.logging_setup import setup_logging

setup_logging()

from .repl_masterpiece import MasterpieceREPL, start_masterpiece_repl  # noqa: E402
from .shell_context import ShellContext  # noqa: E402
from .intent_detector import IntentDetector  # noqa: E402

# Re-export app and validate_output_path from cli_app module for backward compatibility
# This avoids circular import issues from vertice_core.cli.py vs vertice_core/cli/ package conflict
from vertice_core.cli_app import app, validate_output_path, get_squad  # noqa: E402


def main():
    """Main entry point for the CLI."""
    app()


__all__ = [
    "MasterpieceREPL",
    "start_masterpiece_repl",
    "ShellContext",
    "IntentDetector",
    "app",
    "validate_output_path",
    "get_squad",
    "main",
]

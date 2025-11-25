"""CLI package for Qwen Dev CLI"""

# Setup logging FIRST
from qwen_dev_cli.core.logging_setup import setup_logging
setup_logging()

from .repl_masterpiece import MasterpieceREPL, start_masterpiece_repl
from .shell_context import ShellContext
from .intent_detector import IntentDetector

# Re-export app and validate_output_path from cli_app module for backward compatibility
# This avoids circular import issues from qwen_dev_cli.cli.py vs qwen_dev_cli/cli/ package conflict
from qwen_dev_cli.cli_app import app, validate_output_path

__all__ = [
    "MasterpieceREPL",
    "start_masterpiece_repl",
    "ShellContext",
    "IntentDetector",
    "app",
    "validate_output_path",
]

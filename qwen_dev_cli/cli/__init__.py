"""CLI package for Qwen Dev CLI"""

# Setup logging FIRST
from qwen_dev_cli.core.logging_setup import setup_logging
setup_logging()

from .repl_masterpiece import MasterpieceREPL, start_masterpiece_repl
from .shell_context import ShellContext
from .intent_detector import IntentDetector

__all__ = [
    "MasterpieceREPL",
    "start_masterpiece_repl",
    "ShellContext",
    "IntentDetector"
]

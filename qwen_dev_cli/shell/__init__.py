from .repl import main

# Re-export from shell_main for backward compatibility with tests
from qwen_dev_cli.shell_main import InteractiveShell, SessionContext

__all__ = ["main", "InteractiveShell", "SessionContext"]

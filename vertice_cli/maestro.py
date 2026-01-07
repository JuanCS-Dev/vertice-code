"""
DEPRECATED: Use vertice_cli.maestro package instead.

This module is kept for backward compatibility.
Import from vertice_cli.maestro for new code.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "vertice_cli.maestro module is deprecated. Use vertice_cli.maestro package instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from package for backward compatibility
from vertice_cli.maestro import (  # noqa: E402
    GlobalState,
    OutputFormat,
    app,
    console,
    execute_agent_task,
    run,
    state,
)

# Legacy exports
from vertice_cli.maestro.bootstrap import ensure_initialized  # noqa: E402
from vertice_cli.maestro.formatters import (  # noqa: E402
    render_code,
    render_error,
    render_plan,
    render_success,
)

__all__ = [
    "app",
    "state",
    "GlobalState",
    "OutputFormat",
    "console",
    "execute_agent_task",
    "ensure_initialized",
    "render_plan",
    "render_code",
    "render_error",
    "render_success",
    "run",
]

# Entry point (backward compat)
if __name__ == "__main__":
    run()

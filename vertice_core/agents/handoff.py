"""Backward compatibility shim for handoff module.

Deprecated: Import from vertice_core.agents.handoff package directly.
"""

import warnings

warnings.warn(
    "Importing from vertice_core.agents.handoff as module is deprecated. "
    "Use 'from vertice_core.agents.handoff import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .handoff import *

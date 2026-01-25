"""Backward compatibility shim for prompts module.

Deprecated: Import from vertice_core.utils.prompts package directly.
"""

import warnings

warnings.warn(
    "Importing from vertice_core.utils.prompts as module is deprecated. "
    "Use 'from vertice_core.utils.prompts import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .prompts import *

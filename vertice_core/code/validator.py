"""Backward compatibility shim for validator module.

Deprecated: Import from vertice_core.code.validator package directly.
"""

import warnings

warnings.warn(
    "Importing from vertice_core.code.validator as module is deprecated. "
    "Use 'from vertice_core.code.validator import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .validator import *

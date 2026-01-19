"""Backward compatibility shim for maestro_v10_integrated.

Deprecated: Use scripts.maestro directly.
"""
import warnings

warnings.warn(
    "maestro_v10_integrated.py is deprecated. " "Use 'from scripts.maestro import main' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from scripts.maestro import main

if __name__ == "__main__":
    main()

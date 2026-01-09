"""
Language Detector for JuanCS Dev-Code.

DEPRECATED: This module now re-exports from vertice_core.language_detector.
Import directly from vertice_core for new code.

Migration:
    # Old (deprecated)
    from vertice_tui.core.language_detector import LanguageDetector

    # New (preferred)
    from vertice_core import LanguageDetector
"""

# Re-export from vertice_core for backward compatibility
from vertice_core.language_detector import LanguageDetector, LANGUAGE_NAMES

__all__ = ["LanguageDetector", "LANGUAGE_NAMES"]

"""
Language Detector for JuanCS Dev-Code.

DEPRECATED: This module now re-exports from jdev_core.language_detector.
Import directly from jdev_core for new code.

Migration:
    # Old (deprecated)
    from jdev_tui.core.language_detector import LanguageDetector

    # New (preferred)
    from jdev_core import LanguageDetector
"""

# Re-export from jdev_core for backward compatibility
from jdev_core.language_detector import LanguageDetector, LANGUAGE_NAMES

__all__ = ["LanguageDetector", "LANGUAGE_NAMES"]

"""
🎨 Vertice TUI - AI-Powered Text User Interface
🕐 Temporally Conscious TUI System

A beautiful, 60fps TUI for AI-powered development.
Temporal Awareness: ACTIVE

Soli Deo Gloria
"""

__version__ = "1.0.0"
__author__ = "JuanCS"

from .app import VerticeApp, main

# Backward compatibility alias
QwenApp = VerticeApp

__all__ = ["VerticeApp", "QwenApp", "main", "__version__"]

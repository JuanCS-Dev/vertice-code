"""
Compatibility shim for the core agent library.

The implementation of `BaseAgent` lives in `vertice_core.agents.base` and is reused
by both the deployable `agents.*` and the local/CLI `vertice_core.agents.*` layers.
"""

from __future__ import annotations

from vertice_core.agents.base import BaseAgent

__all__ = ["BaseAgent"]

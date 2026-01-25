"""
Core agent library (Google Singularity).

This package is intentionally separate from `vertice_core.agents.*` (CLI/DevSquad agents)
to avoid name collisions (e.g. `vertice_core.agents.architect` exists as a module).

Phase 2 goal: make these agents "pure" and deployable to Vertex AI Reasoning Engines.
"""

from __future__ import annotations

__all__ = [
    "base",
    "architect",
    "coder",
    "devops",
    "orchestrator",
    "researcher",
    "reviewer",
    "stubs",
]

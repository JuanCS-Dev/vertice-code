"""
Procedural Memory - "How I do things"

Stores learned skills and procedures.
Enables reuse of successful solutions.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from .types import MemoryEntry, MemoryType


class ProceduralMemory:
    """
    Procedural Memory subsystem.

    Stores learned procedures organized by:
    - Skill name
    - Success rate
    - Keyword index for search
    """

    def __init__(self):
        """Initialize procedural memory."""
        self.procedures: Dict[str, MemoryEntry] = {}
        self._skill_index: Dict[str, List[str]] = {}

    def store_procedure(
        self,
        skill_name: str,
        steps: List[str],
        success_rate: float = 0.0,
        preconditions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """
        Store a learned procedure.

        Args:
            skill_name: Name of the skill/procedure
            steps: List of steps to execute
            success_rate: Historical success rate (0-1)
            preconditions: Required conditions
            tags: Optional tags

        Returns:
            Created memory entry
        """
        entry = MemoryEntry(
            id=hashlib.md5(skill_name.encode()).hexdigest()[:12],
            type=MemoryType.PROCEDURAL,
            content="\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)]),
            metadata={
                "skill_name": skill_name,
                "steps": steps,
                "steps_count": len(steps),
                "success_rate": success_rate,
                "execution_count": 0,
                "preconditions": preconditions or [],
            },
            importance=success_rate,
            tags=tags or [],
        )

        self.procedures[skill_name] = entry
        self._update_skill_index(skill_name, steps)

        return entry

    def get_procedure(self, skill_name: str) -> Optional[MemoryEntry]:
        """Get procedure by skill name."""
        entry = self.procedures.get(skill_name)
        if entry:
            entry.update_access()
        return entry

    def get_steps(self, skill_name: str) -> Optional[List[str]]:
        """Get steps for a procedure."""
        entry = self.get_procedure(skill_name)
        if entry:
            return entry.metadata.get("steps", [])
        return None

    def search_procedures(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """Search procedures by keywords."""
        query_words = set(query.lower().split())
        results = []

        for keyword in query_words:
            if keyword in self._skill_index:
                for skill_name in self._skill_index[keyword]:
                    if skill_name in self.procedures:
                        entry = self.procedures[skill_name]
                        results.append(entry)

        # Deduplicate and sort by success rate
        seen = set()
        unique_results = []
        for entry in results:
            if entry.id not in seen:
                seen.add(entry.id)
                unique_results.append(entry)

        unique_results.sort(
            key=lambda e: e.metadata.get("success_rate", 0), reverse=True
        )
        return unique_results[:top_k]

    def update_success_rate(self, skill_name: str, success: bool) -> None:
        """Update success rate after execution."""
        if skill_name in self.procedures:
            entry = self.procedures[skill_name]
            current_rate = entry.metadata.get("success_rate", 0.5)
            exec_count = entry.metadata.get("execution_count", 0)

            # Exponential moving average with more weight on recent
            alpha = 0.2 if exec_count > 5 else 0.5
            new_rate = (1 - alpha) * current_rate + alpha * (1.0 if success else 0.0)

            entry.metadata["success_rate"] = new_rate
            entry.metadata["execution_count"] = exec_count + 1
            entry.importance = new_rate

    def add_step(
        self, skill_name: str, step: str, position: Optional[int] = None
    ) -> None:
        """Add a step to an existing procedure."""
        if skill_name in self.procedures:
            entry = self.procedures[skill_name]
            steps = entry.metadata.get("steps", [])

            if position is not None and 0 <= position <= len(steps):
                steps.insert(position, step)
            else:
                steps.append(step)

            entry.metadata["steps"] = steps
            entry.metadata["steps_count"] = len(steps)
            entry.content = "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])

    def _update_skill_index(self, skill_name: str, steps: List[str]) -> None:
        """Update keyword index."""
        words = set(skill_name.lower().split())
        for step in steps:
            words.update(step.lower().split())

        for word in words:
            if len(word) > 2:
                if word not in self._skill_index:
                    self._skill_index[word] = []
                if skill_name not in self._skill_index[word]:
                    self._skill_index[word].append(skill_name)

    def list_skills(self) -> List[str]:
        """List all skill names."""
        return list(self.procedures.keys())

    def export(self) -> dict:
        """Export procedural memory."""
        return {skill: entry.to_dict() for skill, entry in self.procedures.items()}


__all__ = ["ProceduralMemory"]

"""
Skill proficiency tracking for Executor Agent.

Tracks skill development through practice with exponential moving average.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SkillProfile:
    """Profile of a learned skill."""

    name: str
    proficiency: float  # 0-1
    practice_count: int = 0
    last_practiced: Optional[datetime] = None
    success_history: List[bool] = field(default_factory=list)

    def update(self, success: bool):
        """Update skill based on practice result."""
        self.practice_count += 1
        self.last_practiced = datetime.now()
        self.success_history.append(success)

        # Keep last 20 results
        if len(self.success_history) > 20:
            self.success_history = self.success_history[-20:]

        # Update proficiency with exponential moving average
        alpha = 0.2 if self.practice_count > 5 else 0.5
        self.proficiency = (1 - alpha) * self.proficiency + alpha * (1.0 if success else 0.0)

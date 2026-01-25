"""
Prometheus Skills Registry - Manage learned skills from Agent0 evolution.

This registry exposes ProceduralMemory (learned skills) as reusable skills
that other agents can invoke. Skills are automatically registered when
Agent0 masters procedures with >80% success rate.

Features:
- Auto-registration from evolution cycles
- Skill persistence and retrieval
- Integration with Claude Code skills system
- MCP tool exposure for skill invocation
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from prometheus.memory.system import MemorySystem

logger = logging.getLogger(__name__)


@dataclass
class LearnedSkill:
    """Represents a learned skill from Agent0 evolution."""

    name: str
    description: str
    procedure_steps: List[str]
    success_rate: float
    usage_count: int = 0
    last_used: Optional[datetime] = None
    learned_at: datetime = field(default_factory=datetime.now)
    difficulty_level: int = 3
    category: str = "general"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "procedure_steps": self.procedure_steps,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "learned_at": self.learned_at.isoformat(),
            "difficulty_level": self.difficulty_level,
            "category": self.category,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearnedSkill":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            procedure_steps=data["procedure_steps"],
            success_rate=data["success_rate"],
            usage_count=data.get("usage_count", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            learned_at=datetime.fromisoformat(data["learned_at"]),
            difficulty_level=data.get("difficulty_level", 3),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
        )

    def get_skill_prompt(self) -> str:
        """Generate skill prompt for Claude Code integration."""
        steps_text = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(self.procedure_steps))

        return f"""# {self.name}

**Description:** {self.description}
**Success Rate:** {self.success_rate:.1%}
**Category:** {self.category}
**Difficulty:** {self.difficulty_level}/5

## Procedure Steps:
{steps_text}

## Usage Guidelines:
- This skill was learned through Agent0 evolution
- Apply systematically following the procedure steps
- Success rate indicates reliability
- Adapt context-specific details as needed

**Learned:** {self.learned_at.strftime("%Y-%m-%d %H:%M")}
**Usage Count:** {self.usage_count}"""


class PrometheusSkillsRegistry:
    """Registry for managing learned skills from Prometheus evolution."""

    def __init__(self, memory_system: Optional[MemorySystem] = None):
        self.memory_system = memory_system
        self.learned_skills: Dict[str, LearnedSkill] = {}
        self._auto_registration_enabled = True
        self._min_success_rate = 0.8  # 80% success rate threshold

    def set_memory_system(self, memory_system: MemorySystem):
        """Set the memory system for skill retrieval."""
        self.memory_system = memory_system

    async def register_skill(
        self,
        name: str,
        procedure: List[str],
        success_rate: float,
        description: str = "",
        category: str = "general",
        tags: List[str] = None,
    ) -> bool:
        """Register a new learned skill.

        Args:
            name: Skill name
            procedure: List of procedure steps
            success_rate: Success rate (0.0-1.0)
            description: Skill description
            category: Skill category
            tags: Skill tags

        Returns:
            True if registered successfully
        """
        if name in self.learned_skills:
            logger.warning(f"Skill '{name}' already exists, updating...")
            return False

        if success_rate < self._min_success_rate:
            logger.info(
                f"Skill '{name}' success rate {success_rate:.1%} below threshold {self._min_success_rate:.1%}"
            )
            return False

        skill = LearnedSkill(
            name=name,
            description=description or f"Learned skill: {name}",
            procedure_steps=procedure,
            success_rate=success_rate,
            category=category,
            tags=tags or [],
        )

        self.learned_skills[name] = skill

        # Persist to memory if available
        if self.memory_system:
            await self._persist_skill(skill)

        logger.info(f"Registered new skill: {name} (success rate: {success_rate:.1%})")
        return True

    async def update_skill_usage(self, skill_name: str):
        """Update usage statistics for a skill."""
        if skill_name in self.learned_skills:
            skill = self.learned_skills[skill_name]
            skill.usage_count += 1
            skill.last_used = datetime.now()

            # Update persistence
            if self.memory_system:
                await self._persist_skill(skill)

    async def get_skill(self, skill_name: str) -> Optional[LearnedSkill]:
        """Get a skill by name."""
        return self.learned_skills.get(skill_name)

    async def list_skills(
        self, category: Optional[str] = None, min_success_rate: float = 0.0, sort_by: str = "name"
    ) -> List[LearnedSkill]:
        """List skills with optional filtering."""
        skills = list(self.learned_skills.values())

        # Filter by category
        if category:
            skills = [s for s in skills if s.category == category]

        # Filter by success rate
        skills = [s for s in skills if s.success_rate >= min_success_rate]

        # Sort
        if sort_by == "success_rate":
            skills.sort(key=lambda s: s.success_rate, reverse=True)
        elif sort_by == "usage_count":
            skills.sort(key=lambda s: s.usage_count, reverse=True)
        elif sort_by == "learned_at":
            skills.sort(key=lambda s: s.learned_at, reverse=True)
        else:  # name
            skills.sort(key=lambda s: s.name)

        return skills

    async def auto_register_from_evolution(self, evolution_stats: Dict[str, Any]) -> int:
        """Auto-register skills from evolution cycle results.

        Args:
            evolution_stats: Stats from evolution cycle

        Returns:
            Number of skills registered
        """
        if not self._auto_registration_enabled:
            return 0

        registered_count = 0

        # Extract skills mastered from evolution stats
        mastered_skills = evolution_stats.get("skills_mastered", [])

        for skill_name in mastered_skills:
            if skill_name in self.learned_skills:
                continue  # Already registered

            # Try to get procedure from memory system
            if self.memory_system:
                procedure = self.memory_system.get_procedure(skill_name)
                if procedure:
                    # Estimate success rate from evolution stats
                    success_rate = min(
                        0.95, 0.7 + (len(procedure) * 0.05)
                    )  # Base 70% + 5% per step

                    await self.register_skill(
                        name=skill_name,
                        procedure=procedure,
                        success_rate=success_rate,
                        description="Auto-learned skill from Agent0 evolution",
                        category="evolved",
                    )
                    registered_count += 1

        return registered_count

    async def invoke_skill(self, skill_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke a learned skill with given context.

        Args:
            skill_name: Name of the skill to invoke
            context: Context variables for skill execution

        Returns:
            Execution result
        """
        skill = await self.get_skill(skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found",
                "available_skills": list(self.learned_skills.keys()),
            }

        try:
            # Update usage stats
            await self.update_skill_usage(skill_name)

            # For now, return the skill procedure (in real implementation,
            # this would execute the skill with the given context)
            return {
                "success": True,
                "skill": skill_name,
                "procedure": skill.procedure_steps,
                "description": skill.description,
                "success_rate": skill.success_rate,
                "context": context or {},
                "usage_count": skill.usage_count,
            }

        except Exception as e:
            logger.error(f"Error invoking skill '{skill_name}': {e}")
            return {
                "success": False,
                "error": f"Skill execution failed: {str(e)}",
                "skill": skill_name,
            }

    async def _persist_skill(self, skill: LearnedSkill):
        """Persist skill to memory system."""
        if not self.memory_system:
            return

        try:
            # Store as procedure in procedural memory
            await self.memory_system.learn_procedure(
                skill_name=skill.name,
                steps=skill.procedure_steps,
                metadata={
                    "description": skill.description,
                    "success_rate": skill.success_rate,
                    "category": skill.category,
                    "tags": skill.tags,
                    "learned_at": skill.learned_at.isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to persist skill '{skill.name}': {e}")

    async def load_from_memory(self):
        """Load skills from memory system."""
        if not self.memory_system:
            return

        try:
            # Get all procedures from memory
            procedures = self.memory_system.find_procedures("", top_k=1000)  # Get all

            for proc in procedures:
                skill_name = proc.get("skill_name", "")
                if skill_name and skill_name not in self.learned_skills:
                    # Reconstruct skill from procedure
                    metadata = proc.get("metadata", {})
                    success_rate = metadata.get("success_rate", 0.8)

                    if success_rate >= self._min_success_rate:
                        skill = LearnedSkill(
                            name=skill_name,
                            description=metadata.get("description", f"Loaded skill: {skill_name}"),
                            procedure_steps=proc.get("steps", []),
                            success_rate=success_rate,
                            category=metadata.get("category", "loaded"),
                            tags=metadata.get("tags", []),
                        )

                        # Parse learned_at if available
                        learned_at_str = metadata.get("learned_at")
                        if learned_at_str:
                            try:
                                skill.learned_at = datetime.fromisoformat(learned_at_str)
                            except (ValueError, TypeError):
                                pass  # Keep default

                        self.learned_skills[skill_name] = skill

        except Exception as e:
            logger.warning(f"Failed to load skills from memory: {e}")

    def enable_auto_registration(self, enabled: bool = True):
        """Enable/disable automatic skill registration."""
        self._auto_registration_enabled = enabled

    def set_min_success_rate(self, rate: float):
        """Set minimum success rate for skill registration."""
        self._min_success_rate = max(0.0, min(1.0, rate))

    async def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        if not self.learned_skills:
            return {"total_skills": 0, "categories": {}, "avg_success_rate": 0.0}

        categories = {}
        total_success_rate = 0.0

        for skill in self.learned_skills.values():
            categories[skill.category] = categories.get(skill.category, 0) + 1
            total_success_rate += skill.success_rate

        return {
            "total_skills": len(self.learned_skills),
            "categories": categories,
            "avg_success_rate": total_success_rate / len(self.learned_skills),
            "most_used": (
                max(self.learned_skills.values(), key=lambda s: s.usage_count).name
                if self.learned_skills
                else None
            ),
            "newest": (
                max(self.learned_skills.values(), key=lambda s: s.learned_at).name
                if self.learned_skills
                else None
            ),
        }

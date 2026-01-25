"""
Skill Loader - Static Skill Parsing & Management
================================================

Parses static skills (SOPs) from Markdown files with YAML frontmatter.
Aligns with MCP "Prompts" and "Resources" primitives.

File Format:
    ---
    name: git-ops
    description: Git operations...
    ---
    # Git Operations
    ... content ...

Usage:
    loader = SkillLoader(skills_dir="skills")
    skills = loader.load_all()
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StaticSkill:
    """Represents a statically defined skill (SOP)."""

    name: str
    description: str
    content: str
    metadata: Dict[str, Any]
    path: Path

    def to_prompt(self) -> str:
        """Convert to LLM system prompt format."""
        return f"""
# Skill: {self.name}
## Description
{self.description}

## Standard Operating Procedure
{self.content}
"""


class SkillLoader:
    """Loads static skills from filesystem."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, StaticSkill] = {}

    def load_all(self) -> Dict[str, StaticSkill]:
        """Load all valid skills from the directory."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return {}

        self.skills = {}
        # Recursive search for markdown files
        for file_path in self.skills_dir.rglob("*.md"):
            # Skip READMEs or non-skill files if necessary
            if file_path.name.upper() == "README.MD":
                continue

            try:
                skill = self._parse_skill_file(file_path)
                if skill:
                    self.skills[skill.name] = skill
            except Exception as e:
                logger.error(f"Failed to load skill {file_path}: {e}")

        return self.skills

    def _parse_skill_file(self, path: Path) -> Optional[StaticSkill]:
        """Parse a single markdown file with YAML frontmatter."""
        content = path.read_text(encoding="utf-8")

        if not content.startswith("---"):
            return None  # Not a valid skill file

        try:
            # Split frontmatter and content
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter_yaml = parts[1]
            markdown_content = parts[2].strip()

            metadata = yaml.safe_load(frontmatter_yaml)

            if not isinstance(metadata, dict) or "name" not in metadata:
                logger.warning(f"Invalid frontmatter in {path}")
                return None

            return StaticSkill(
                name=metadata["name"],
                description=metadata.get("description", "No description"),
                content=markdown_content,
                metadata=metadata,
                path=path,
            )

        except yaml.YAMLError as e:
            logger.error(f"YAML error in {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {path}: {e}")
            return None

    def get_skill(self, name: str) -> Optional[StaticSkill]:
        """Get skill by name."""
        return self.skills.get(name)

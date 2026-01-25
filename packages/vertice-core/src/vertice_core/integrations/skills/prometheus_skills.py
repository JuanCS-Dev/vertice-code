"""
Prometheus Skills Provider - Bridge to Claude Code skills system.

This provider exposes learned Prometheus skills as reusable skills
that can be invoked by other agents through the Claude Code skills API.

Integration points:
- /skills list command
- /skill invoke command
- MCP tools exposure
- Skill persistence and retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from prometheus.skills.registry import PrometheusSkillsRegistry

logger = logging.getLogger(__name__)


class PrometheusSkillsProvider:
    """Provider for Prometheus-learned skills integration with Claude Code."""

    def __init__(self, skills_registry: Optional[PrometheusSkillsRegistry] = None):
        self.skills_registry = skills_registry or PrometheusSkillsRegistry()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes

    def set_skills_registry(self, registry: PrometheusSkillsRegistry):
        """Set the skills registry."""
        self.skills_registry = registry

    async def list_skills(self) -> List[Dict[str, str]]:
        """List all available Prometheus skills for Claude Code integration.

        Returns:
            List of skill dictionaries compatible with Claude Code format
        """
        try:
            skills = await self.skills_registry.list_skills()

            skill_list = []
            for skill in skills:
                skill_dict = {
                    "name": f"prometheus:{skill.name}",
                    "description": skill.description,
                    "scope": "global",
                    "file": f"prometheus://skills/{skill.name}",
                    "category": skill.category,
                    "success_rate": f"{skill.success_rate:.1%}",
                    "usage_count": str(skill.usage_count),
                    "difficulty": str(skill.difficulty_level),
                    "learned_at": skill.learned_at.strftime("%Y-%m-%d %H:%M"),
                    "tags": ",".join(skill.tags) if skill.tags else "",
                }
                skill_list.append(skill_dict)

            return skill_list

        except Exception as e:
            logger.error(f"Error listing Prometheus skills: {e}")
            return []

    async def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Get the content/prompt for a specific skill.

        Args:
            skill_name: Skill name (with or without prometheus: prefix)

        Returns:
            Skill content as string, or None if not found
        """
        # Remove prometheus: prefix if present
        if skill_name.startswith("prometheus:"):
            skill_name = skill_name[11:]  # Remove "prometheus:" prefix

        try:
            skill = await self.skills_registry.get_skill(skill_name)
            if skill:
                return skill.get_skill_prompt()
            return None

        except Exception as e:
            logger.error(f"Error getting skill content for '{skill_name}': {e}")
            return None

    async def invoke_skill(self, skill_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke a Prometheus skill with given context.

        Args:
            skill_name: Skill name (with or without prometheus: prefix)
            context: Context variables for skill execution

        Returns:
            Execution result
        """
        # Remove prometheus: prefix if present
        if skill_name.startswith("prometheus:"):
            skill_name = skill_name[11:]

        try:
            result = await self.skills_registry.invoke_skill(skill_name, context or {})

            # Format for Claude Code compatibility
            if result["success"]:
                return {
                    "success": True,
                    "skill": f"prometheus:{skill_name}",
                    "result": result.get("procedure", []),
                    "description": result.get("description", ""),
                    "context": result.get("context", {}),
                    "usage_count": result.get("usage_count", 0),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "skill": f"prometheus:{skill_name}",
                    "available_skills": [
                        f"prometheus:{s}" for s in result.get("available_skills", [])
                    ],
                }

        except Exception as e:
            logger.error(f"Error invoking skill '{skill_name}': {e}")
            return {
                "success": False,
                "error": f"Skill invocation failed: {str(e)}",
                "skill": f"prometheus:{skill_name}",
            }

    async def search_skills(
        self, query: str, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search skills by query and optional category.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of matching skills
        """
        try:
            # For now, get all skills and filter client-side
            # In a real implementation, this would be done in the registry
            all_skills = await self.skills_registry.list_skills(category=category)

            matching_skills = []
            query_lower = query.lower()

            for skill in all_skills:
                # Search in name, description, and tags
                searchable_text = f"{skill.name} {skill.description} {' '.join(skill.tags)}".lower()

                if query_lower in searchable_text:
                    skill_dict = {
                        "name": f"prometheus:{skill.name}",
                        "description": skill.description,
                        "category": skill.category,
                        "success_rate": f"{skill.success_rate:.1%}",
                        "difficulty": skill.difficulty_level,
                        "usage_count": skill.usage_count,
                        "tags": skill.tags,
                        "relevance_score": 1.0,  # Could implement better scoring
                    }
                    matching_skills.append(skill_dict)

            # Sort by relevance (usage count as proxy)
            matching_skills.sort(key=lambda s: s["usage_count"], reverse=True)

            return matching_skills

        except Exception as e:
            logger.error(f"Error searching skills with query '{query}': {e}")
            return []

    async def get_skill_stats(self) -> Dict[str, Any]:
        """Get statistics about available skills."""
        try:
            registry_stats = await self.skills_registry.get_stats()

            return {
                "total_prometheus_skills": registry_stats.get("total_skills", 0),
                "categories": registry_stats.get("categories", {}),
                "avg_success_rate": registry_stats.get("avg_success_rate", 0.0),
                "most_used_skill": registry_stats.get("most_used"),
                "newest_skill": registry_stats.get("newest"),
                "skills_provider": "prometheus",
                "last_updated": "2026-01-06T18:15:00Z",
            }

        except Exception as e:
            logger.error(f"Error getting skill stats: {e}")
            return {"total_prometheus_skills": 0, "error": str(e), "skills_provider": "prometheus"}

    async def refresh_cache(self):
        """Refresh the internal skills cache."""
        self._cache.clear()
        logger.info("Prometheus skills cache refreshed")

    # Claude Code Skills Integration Methods

    def get_claude_skill_files(self) -> List[Path]:
        """Get skill files in Claude Code format (for compatibility)."""
        # This would return virtual file paths for Claude integration
        # In practice, skills are accessed through the provider API
        return []

    async def load_claude_skill(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """Load a skill from Claude Code format (for compatibility)."""
        # Convert Claude skill format to Prometheus skill format
        try:
            if skill_path.name.startswith("prometheus:"):
                skill_name = skill_path.name[11:]  # Remove prefix
                skill = await self.skills_registry.get_skill(skill_name)

                if skill:
                    return {
                        "name": skill_path.name,
                        "content": skill.get_skill_prompt(),
                        "description": skill.description,
                        "scope": "global",
                        "file": str(skill_path),
                        "metadata": {
                            "success_rate": skill.success_rate,
                            "usage_count": skill.usage_count,
                            "category": skill.category,
                            "tags": skill.tags,
                        },
                    }

            return None

        except Exception as e:
            logger.error(f"Error loading Claude skill from {skill_path}: {e}")
            return None

    # MCP Integration Methods

    def create_mcp_skill_tool(self, skill_name: str):
        """Create an MCP tool wrapper for a specific skill."""

        async def invoke_prometheus_skill(
            context: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """Invoke a learned Prometheus skill."""
            return await self.invoke_skill(skill_name, context or {})

        invoke_prometheus_skill.__name__ = f"invoke_prometheus_skill_{skill_name}"
        invoke_prometheus_skill.__doc__ = f"Execute learned Prometheus skill: {skill_name}"

        return invoke_prometheus_skill

    async def register_skills_as_mcp_tools(self, mcp_server) -> int:
        """Register all available skills as MCP tools.

        Args:
            mcp_server: MCP server instance

        Returns:
            Number of skills registered
        """
        try:
            skills = await self.list_skills()
            registered_count = 0

            for skill_info in skills:
                skill_name = skill_info["name"]

                # Create MCP tool for this skill
                mcp_tool = self.create_mcp_skill_tool(skill_name.replace("prometheus:", ""))

                # Register with MCP server
                mcp_server.tool(name=skill_name)(mcp_tool)
                registered_count += 1

            logger.info(f"Registered {registered_count} Prometheus skills as MCP tools")
            return registered_count

        except Exception as e:
            logger.error(f"Error registering skills as MCP tools: {e}")
            return 0

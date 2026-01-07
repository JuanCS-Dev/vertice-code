"""
Tests for Prometheus Skills System.

Comprehensive test suite covering:
- Skills registry functionality
- Skills provider integration
- Auto-registration from evolution
- MCP tool integration
- Edge cases and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from prometheus.skills.registry import PrometheusSkillsRegistry
from prometheus.memory.system import MemorySystem
from vertice_cli.integrations.skills.prometheus_skills import PrometheusSkillsProvider


class TestPrometheusSkillsRegistry:
    """Test the skills registry functionality."""

    @pytest.fixture
    def memory_system(self):
        """Mock memory system for testing."""
        memory = Mock(spec=MemorySystem)
        memory.learn_procedure = AsyncMock()
        return memory

    @pytest.fixture
    def skills_registry(self, memory_system):
        """Create skills registry for testing."""
        registry = PrometheusSkillsRegistry(memory_system)
        return registry

    def test_registry_initialization(self, skills_registry, memory_system):
        """Test registry initialization."""
        assert skills_registry.memory_system == memory_system
        assert skills_registry.learned_skills == {}
        assert skills_registry._auto_registration_enabled is True
        assert skills_registry._min_success_rate == 0.8

    @pytest.mark.asyncio
    async def test_register_skill_success(self, skills_registry, memory_system):
        """Test successful skill registration."""
        procedure = [
            "Step 1: Analyze the problem",
            "Step 2: Apply solution",
            "Step 3: Verify result",
        ]

        result = await skills_registry.register_skill(
            name="debug_performance_issue",
            procedure=procedure,
            success_rate=0.95,
            description="Debug performance issues in code",
            category="debugging",
        )

        assert result is True
        assert "debug_performance_issue" in skills_registry.learned_skills

        skill = skills_registry.learned_skills["debug_performance_issue"]
        assert skill.name == "debug_performance_issue"
        assert skill.procedure_steps == procedure
        assert skill.success_rate == 0.95
        assert skill.category == "debugging"
        assert skill.usage_count == 0

        # Verify persistence was called
        memory_system.learn_procedure.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_skill_low_success_rate(self, skills_registry):
        """Test rejection of skills with low success rate."""
        result = await skills_registry.register_skill(
            name="low_quality_skill",
            procedure=["Do something"],
            success_rate=0.5,  # Below threshold
            description="Low quality skill",
        )

        assert result is False
        assert "low_quality_skill" not in skills_registry.learned_skills

    @pytest.mark.asyncio
    async def test_register_duplicate_skill(self, skills_registry):
        """Test registering a skill that already exists."""
        # Register first time
        await skills_registry.register_skill(
            name="existing_skill", procedure=["Step 1"], success_rate=0.9
        )

        # Try to register again
        result = await skills_registry.register_skill(
            name="existing_skill", procedure=["Different step"], success_rate=0.95
        )

        assert result is False
        # Original skill should still exist
        assert skills_registry.learned_skills["existing_skill"].procedure_steps == ["Step 1"]

    @pytest.mark.asyncio
    async def test_get_skill(self, skills_registry):
        """Test retrieving a skill."""
        await skills_registry.register_skill(
            name="test_skill", procedure=["Test step"], success_rate=0.9
        )

        skill = await skills_registry.get_skill("test_skill")
        assert skill is not None
        assert skill.name == "test_skill"

        # Test non-existent skill
        skill = await skills_registry.get_skill("non_existent")
        assert skill is None

    @pytest.mark.asyncio
    async def test_list_skills(self, skills_registry):
        """Test listing skills with filtering."""
        # Register multiple skills
        await skills_registry.register_skill("skill1", ["step"], 0.9, category="debug")
        await skills_registry.register_skill("skill2", ["step"], 0.85, category="debug")
        await skills_registry.register_skill("skill3", ["step"], 0.95, category="test")

        # List all
        all_skills = await skills_registry.list_skills()
        assert len(all_skills) == 3

        # Filter by category
        debug_skills = await skills_registry.list_skills(category="debug")
        assert len(debug_skills) == 2

        # Filter by success rate
        high_success = await skills_registry.list_skills(min_success_rate=0.9)
        assert len(high_success) == 2

        # Sort by success rate
        sorted_skills = await skills_registry.list_skills(sort_by="success_rate")
        assert sorted_skills[0].success_rate >= sorted_skills[1].success_rate

    @pytest.mark.asyncio
    async def test_update_skill_usage(self, skills_registry):
        """Test updating skill usage statistics."""
        await skills_registry.register_skill("usage_test", ["step"], 0.9)

        skill = await skills_registry.get_skill("usage_test")
        assert skill.usage_count == 0

        await skills_registry.update_skill_usage("usage_test")

        skill = await skills_registry.get_skill("usage_test")
        assert skill.usage_count == 1
        assert skill.last_used is not None

    @pytest.mark.asyncio
    async def test_invoke_skill_success(self, skills_registry):
        """Test successful skill invocation."""
        await skills_registry.register_skill(
            "invoke_test", ["Step 1", "Step 2"], 0.9, "Test skill invocation"
        )

        result = await skills_registry.invoke_skill("invoke_test", {"param": "value"})

        assert result["success"] is True
        assert result["skill"] == "invoke_test"
        assert result["procedure"] == ["Step 1", "Step 2"]
        assert result["context"] == {"param": "value"}

        # Usage should be updated
        skill = await skills_registry.get_skill("invoke_test")
        assert skill.usage_count == 1

    @pytest.mark.asyncio
    async def test_invoke_skill_not_found(self, skills_registry):
        """Test invoking non-existent skill."""
        result = await skills_registry.invoke_skill("non_existent")

        assert result["success"] is False
        assert "not found" in result["error"]
        assert "available_skills" in result

    @pytest.mark.asyncio
    async def test_auto_register_from_evolution(self, skills_registry, memory_system):
        """Test auto-registration from evolution results."""
        # Mock memory system to return a procedure
        memory_system.get_procedure = Mock(return_value=["Mock procedure step"])

        evolution_stats = {
            "skills_mastered": ["auto_skill"],
            "procedural_skills": {"auto_skill": {"success_rate": 0.9}},
        }

        registered_count = await skills_registry.auto_register_from_evolution(evolution_stats)

        assert registered_count == 1
        assert "auto_skill" in skills_registry.learned_skills

    @pytest.mark.asyncio
    async def test_load_from_memory(self, skills_registry, memory_system):
        """Test loading skills from memory system."""
        # Mock procedures in memory
        mock_procedures = [
            {
                "skill_name": "loaded_skill",
                "steps": ["Loaded step"],
                "metadata": {
                    "success_rate": 0.85,
                    "category": "loaded",
                    "learned_at": datetime.now().isoformat(),
                },
            }
        ]

        memory_system.find_procedures = Mock(return_value=mock_procedures)

        await skills_registry.load_from_memory()

        assert "loaded_skill" in skills_registry.learned_skills
        skill = skills_registry.learned_skills["loaded_skill"]
        assert skill.success_rate == 0.85
        assert skill.category == "loaded"

    def test_configuration_methods(self, skills_registry):
        """Test configuration methods."""
        # Test auto-registration toggle
        skills_registry.enable_auto_registration(False)
        assert skills_registry._auto_registration_enabled is False

        skills_registry.enable_auto_registration(True)
        assert skills_registry._auto_registration_enabled is True

        # Test min success rate
        skills_registry.set_min_success_rate(0.9)
        assert skills_registry._min_success_rate == 0.9

    @pytest.mark.asyncio
    async def test_get_stats(self, skills_registry):
        """Test getting registry statistics."""
        # Empty registry
        stats = await skills_registry.get_stats()
        assert stats["total_skills"] == 0
        assert stats["avg_success_rate"] == 0.0

        # Add skills
        await skills_registry.register_skill("stat_skill1", ["step"], 0.9)
        await skills_registry.register_skill("stat_skill2", ["step"], 0.8)

        stats = await skills_registry.get_stats()
        assert stats["total_skills"] == 2
        assert abs(stats["avg_success_rate"] - 0.85) < 0.01


class TestPrometheusSkillsProvider:
    """Test the skills provider functionality."""

    @pytest.fixture
    def skills_registry(self):
        """Mock skills registry for testing."""
        registry = Mock(spec=PrometheusSkillsRegistry)
        return registry

    @pytest.fixture
    def skills_provider(self, skills_registry):
        """Create skills provider for testing."""
        provider = PrometheusSkillsProvider(skills_registry)
        return provider

    @pytest.mark.asyncio
    async def test_list_skills(self, skills_provider, skills_registry):
        """Test listing skills for Claude Code."""
        mock_skills = [
            Mock(
                name="test_skill",
                description="Test description",
                success_rate=0.9,
                usage_count=5,
                difficulty_level=3,
                category="test",
                learned_at=datetime.now(),
                tags=["tag1"],
            )
        ]

        skills_registry.list_skills = AsyncMock(return_value=mock_skills)

        skills_list = await skills_provider.list_skills()

        assert len(skills_list) == 1
        skill = skills_list[0]
        assert skill["name"] == "prometheus:test_skill"
        assert skill["description"] == "Test description"
        assert skill["success_rate"] == "90.0%"
        assert skill["usage_count"] == "5"

    @pytest.mark.asyncio
    async def test_get_skill_content(self, skills_provider, skills_registry):
        """Test getting skill content."""
        mock_skill = Mock()
        mock_skill.get_skill_prompt.return_value = "Skill prompt content"

        skills_registry.get_skill = AsyncMock(return_value=mock_skill)

        content = await skills_provider.get_skill_content("test_skill")

        assert content == "Skill prompt content"
        skills_registry.get_skill.assert_called_once_with("test_skill")

        # Test non-existent skill
        skills_registry.get_skill = AsyncMock(return_value=None)
        content = await skills_provider.get_skill_content("non_existent")
        assert content is None

    @pytest.mark.asyncio
    async def test_invoke_skill_success(self, skills_provider, skills_registry):
        """Test successful skill invocation."""
        invoke_result = {
            "success": True,
            "procedure": ["Step 1", "Step 2"],
            "description": "Test skill",
            "usage_count": 1,
        }

        skills_registry.invoke_skill = AsyncMock(return_value=invoke_result)

        result = await skills_provider.invoke_skill("test_skill", {"param": "value"})

        assert result["success"] is True
        assert result["skill"] == "prometheus:test_skill"
        assert result["result"] == ["Step 1", "Step 2"]
        assert result["context"] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_invoke_skill_with_prefix(self, skills_provider, skills_registry):
        """Test invoking skill with prometheus: prefix."""
        skills_registry.invoke_skill = AsyncMock(return_value={"success": True})

        result = await skills_provider.invoke_skill("prometheus:test_skill")

        skills_registry.invoke_skill.assert_called_once_with("test_skill", {})

    @pytest.mark.asyncio
    async def test_search_skills(self, skills_provider, skills_registry):
        """Test searching skills."""
        mock_skills = [
            Mock(
                name="debug_skill",
                description="Debug performance issues",
                success_rate=0.9,
                usage_count=10,
                difficulty_level=3,
                category="debugging",
                tags=["performance", "debug"],
            ),
            Mock(
                name="test_skill",
                description="Testing utilities",
                success_rate=0.8,
                usage_count=5,
                difficulty_level=2,
                category="testing",
                tags=["test"],
            ),
        ]

        skills_registry.list_skills = AsyncMock(return_value=mock_skills)

        results = await skills_provider.search_skills("debug")

        assert len(results) == 1
        assert results[0]["name"] == "prometheus:debug_skill"
        assert "performance" in results[0]["tags"]

    @pytest.mark.asyncio
    async def test_get_skill_stats(self, skills_provider, skills_registry):
        """Test getting skill statistics."""
        stats = {
            "total_skills": 5,
            "categories": {"debugging": 2, "testing": 3},
            "avg_success_rate": 0.87,
            "most_used_skill": "debug_skill",
            "newest_skill": "new_skill",
        }

        skills_registry.get_stats = AsyncMock(return_value=stats)

        result = await skills_provider.get_skill_stats()

        assert result["total_prometheus_skills"] == 5
        assert result["categories"] == {"debugging": 2, "testing": 3}
        assert result["avg_success_rate"] == 0.87
        assert result["most_used_skill"] == "debug_skill"


class TestSkillsIntegration:
    """Test integration between components."""

    @pytest.mark.asyncio
    async def test_end_to_end_skill_lifecycle(self):
        """Test complete skill lifecycle from learning to invocation."""
        from prometheus.memory.system import MemorySystem

        # Create real components
        memory_system = MemorySystem()
        skills_registry = PrometheusSkillsRegistry(memory_system)
        skills_provider = PrometheusSkillsProvider(skills_registry)

        # Register a skill
        procedure = ["Analyze the issue", "Apply fix", "Test solution"]
        await skills_registry.register_skill(
            name="debug_workflow",
            procedure=procedure,
            success_rate=0.92,
            description="Complete debugging workflow",
            category="debugging",
            tags=["debug", "workflow"],
        )

        # Verify skill was registered
        skill = await skills_registry.get_skill("debug_workflow")
        assert skill is not None
        assert skill.procedure_steps == procedure
        assert skill.success_rate == 0.92

        # List skills via provider
        skills_list = await skills_provider.list_skills()
        assert len(skills_list) == 1
        assert skills_list[0]["name"] == "prometheus:debug_workflow"

        # Invoke skill
        result = await skills_provider.invoke_skill(
            "prometheus:debug_workflow", {"issue": "performance"}
        )
        assert result["success"] is True
        assert result["procedure"] == procedure
        assert result["context"] == {"issue": "performance"}

        # Check usage was updated
        skill = await skills_registry.get_skill("debug_workflow")
        assert skill.usage_count == 1

    @pytest.mark.asyncio
    async def test_skill_persistence(self):
        """Test skill persistence across registry instances."""
        from prometheus.memory.system import MemorySystem

        # First registry instance
        memory1 = MemorySystem()
        registry1 = PrometheusSkillsRegistry(memory1)

        await registry1.register_skill("persistent_skill", ["Step"], 0.9)

        # Second registry instance (simulating restart)
        memory2 = MemorySystem()
        registry2 = PrometheusSkillsRegistry(memory2)

        # Load from memory
        await registry2.load_from_memory()

        # Skill should be loaded
        skill = await registry2.get_skill("persistent_skill")
        assert skill is not None
        assert skill.name == "persistent_skill"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_procedure_registration(self):
        """Test registering skill with empty procedure."""
        registry = PrometheusSkillsRegistry()

        result = await registry.register_skill(
            name="empty_skill",
            procedure=[],  # Empty procedure
            success_rate=0.9,
        )

        assert result is True
        skill = await registry.get_skill("empty_skill")
        assert skill.procedure_steps == []

    @pytest.mark.asyncio
    async def test_very_long_skill_names(self):
        """Test skills with very long names."""
        registry = PrometheusSkillsRegistry()

        long_name = "a" * 200  # 200 character name
        result = await registry.register_skill(long_name, ["step"], 0.9)

        assert result is True
        skill = await registry.get_skill(long_name)
        assert skill.name == long_name

    @pytest.mark.asyncio
    async def test_special_characters_in_skill_names(self):
        """Test skill names with special characters."""
        registry = PrometheusSkillsRegistry()

        special_names = [
            "skill-with-dashes",
            "skill_with_underscores",
            "skill.with.dots",
            "skill123numbers",
        ]

        for name in special_names:
            result = await registry.register_skill(name, ["step"], 0.9)
            assert result is True

            skill = await registry.get_skill(name)
            assert skill.name == name

    @pytest.mark.asyncio
    async def test_concurrent_skill_operations(self):
        """Test concurrent skill operations."""
        registry = PrometheusSkillsRegistry()

        async def register_skill(i):
            await registry.register_skill(f"concurrent_skill_{i}", ["step"], 0.9)
            return i

        # Register skills concurrently
        tasks = [register_skill(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert len(registry.learned_skills) == 10

    @pytest.mark.asyncio
    async def test_memory_system_failure(self):
        """Test behavior when memory system fails."""
        failing_memory = Mock()
        failing_memory.learn_procedure = AsyncMock(side_effect=Exception("Memory failure"))

        registry = PrometheusSkillsRegistry(failing_memory)

        # Should still register skill even if persistence fails
        result = await registry.register_skill("test_skill", ["step"], 0.9)
        assert result is True

        skill = await registry.get_skill("test_skill")
        assert skill is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

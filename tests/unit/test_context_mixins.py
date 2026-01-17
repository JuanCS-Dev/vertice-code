"""
Tests for Context Mixins - Sprint 2 Refactoring.

Tests cover:
    - ContextVariablesMixin: Variable management
"""

from vertice_core.agents.context.mixins.variables import ContextVariablesMixin


class TestContextVariablesMixin:
    """Test ContextVariablesMixin."""

    def test_mixin_instantiation(self) -> None:
        """Test mixin can be instantiated."""
        mixin = ContextVariablesMixin()
        assert hasattr(mixin, "get")
        assert hasattr(mixin, "set")
        assert hasattr(mixin, "update")
        assert hasattr(mixin, "delete")
        assert hasattr(mixin, "variables")

    def test_get_set_operations(self) -> None:
        """Test basic get/set operations."""
        mixin = ContextVariablesMixin()

        # Set and get
        mixin.set("task_id", "task-123")
        assert mixin.get("task_id") == "task-123"

        # Get with default
        assert mixin.get("nonexistent", "default") == "default"

        # Get without default (should be None)
        assert mixin.get("nonexistent") is None

    def test_update_multiple_variables(self) -> None:
        """Test updating multiple variables at once."""
        mixin = ContextVariablesMixin()

        variables = {"user_id": "user-456", "project": "vertice", "priority": "high"}

        mixin.update(variables)

        assert mixin.get("user_id") == "user-456"
        assert mixin.get("project") == "vertice"
        assert mixin.get("priority") == "high"

    def test_delete_variable(self) -> None:
        """Test deleting variables."""
        mixin = ContextVariablesMixin()

        mixin.set("temp_var", "temporary")
        assert mixin.get("temp_var") == "temporary"

        # Delete existing variable
        assert mixin.delete("temp_var") is True
        assert mixin.get("temp_var") is None

        # Delete non-existent variable
        assert mixin.delete("nonexistent") is False

    def test_variables_copy(self) -> None:
        """Test that variables() returns a copy."""
        mixin = ContextVariablesMixin()

        mixin.set("key1", "value1")
        variables = mixin.variables()

        # Modify the returned dict
        variables["key2"] = "value2"

        # Original should be unchanged
        assert mixin.get("key2") is None
        assert len(mixin.variables()) == 1

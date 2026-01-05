
import pytest

@pytest.mark.asyncio
async def test_debugging_scenario(cortex):
    """Simulate a debugging session."""
    # Arrange
    await cortex.semantic.store("The bug is in the authentication logic.", category="debugging")

    # Act
    context = await cortex.to_context_prompt("What could be causing the login to fail?")

    # Assert
    assert "authentication" in context

@pytest.mark.asyncio
async def test_code_refactoring_scenario(cortex):
    """Simulate a code refactoring session."""
    # Arrange
    await cortex.semantic.store("The `process_data` function is too long and should be broken down.", category="refactoring")

    # Act
    context = await cortex.to_context_prompt("Which function should I refactor?")

    # Assert
    assert "process_data" in context

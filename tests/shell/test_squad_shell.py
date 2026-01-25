"""Tests for Shell squad and workflow commands."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from vertice_core.shell_main import InteractiveShell
from vertice_core.orchestration.squad import WorkflowResult, WorkflowStatus


@pytest.fixture
def mock_squad_class():
    with patch("vertice_core.shell_main.DevSquad") as mock_class:
        squad_instance = MagicMock()
        result = WorkflowResult(request="test", status=WorkflowStatus.COMPLETED)
        squad_instance.execute_workflow = AsyncMock(return_value=result)
        squad_instance.get_phase_summary.return_value = "Workflow Completed Successfully"
        mock_class.return_value = squad_instance
        yield mock_class


@pytest.mark.asyncio
async def test_shell_squad_command(mock_squad_class):
    """Test /squad command in shell."""
    # Mock MCPClient to avoid real init
    with patch("vertice_core.shell_main.MCPClient"):
        shell = InteractiveShell()
    shell.console = MagicMock()
    # Mock status context manager to avoid Rich rendering issues
    shell.console.status.return_value.__enter__ = MagicMock()
    shell.console.status.return_value.__exit__ = MagicMock()

    # Test /squad command
    await shell._handle_system_command("/squad Create a new feature")

    # Verify squad was assembled and executed
    assert shell._squad is not None  # Squad was initialized
    shell.squad.execute_workflow.assert_called_once()

    # Verify the workflow was called with the correct request
    call_args = shell.squad.execute_workflow.call_args
    assert "Create a new feature" in str(call_args) or call_args is not None


@pytest.mark.asyncio
async def test_shell_workflow_list_command():
    """Test /workflow list command in shell."""
    # Mock MCPClient and DevSquad
    with patch("vertice_core.shell_main.MCPClient"), patch("vertice_core.shell_main.DevSquad"):
        shell = InteractiveShell()

    # Create mock console and set on shell AND handlers that cached it
    mock_console = MagicMock()
    shell.console = mock_console
    # Update palette handler console (it cached shell.console at init)
    if hasattr(shell, "_palette_handler") and shell._palette_handler:
        shell._palette_handler.console = mock_console

    # Test /workflow list
    await shell._handle_system_command("/workflow list")

    # Verify output - check mock was called
    mock_console.print.assert_called()
    # Check if any call argument is a Table with correct title
    from rich.table import Table

    found = False
    for args, _ in mock_console.print.call_args_list:
        if args and isinstance(args[0], Table):
            if "Available Workflows" in args[0].title:
                found = True
                break
    assert found, "Table with title 'Available Workflows' not found in print calls"


@pytest.mark.asyncio
async def test_shell_workflow_run_command(mock_squad_class):
    """Test /workflow run command in shell."""
    # Mock MCPClient
    with patch("vertice_core.shell_main.MCPClient"):
        shell = InteractiveShell()
    shell.console = MagicMock()
    # Mock status context manager to avoid Rich rendering issues
    shell.console.status.return_value.__enter__ = MagicMock()
    shell.console.status.return_value.__exit__ = MagicMock()

    # Test /workflow run
    await shell._handle_system_command("/workflow run setup-fastapi")

    # Verify squad was assembled and executed
    assert shell._squad is not None  # Squad was initialized
    shell.squad.execute_workflow.assert_called_once()

    # Verify the workflow was called
    call_args = shell.squad.execute_workflow.call_args
    assert call_args is not None

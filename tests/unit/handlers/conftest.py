"""
Fixtures for handler unit tests.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_shell():
    """Provides a mock InteractiveShell instance."""
    shell = MagicMock()
    shell.llm = AsyncMock()
    shell.console = MagicMock()
    shell.context = MagicMock()
    shell.workflow_viz = MagicMock()
    shell.dashboard = MagicMock()
    shell.session_state = MagicMock()
    shell.rich_context = MagicMock()
    shell.state_transition = MagicMock()
    shell.context_engine = MagicMock()
    shell.enhanced_input = MagicMock()
    shell.recovery_engine = AsyncMock()
    shell.conversation = MagicMock()
    shell.registry = MagicMock()
    return shell

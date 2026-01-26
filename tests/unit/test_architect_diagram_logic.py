import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.architect.reasoning_engine_app import ArchitectReasoningEngineApp


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(
        return_value="## Architecture Design\n```mermaid\ngraph TD\n  A --> B\n```"
    )
    return provider


@pytest.mark.asyncio
async def test_architect_prompts_for_mermaid_diagrams(mock_provider):
    """Garante que o Arquiteto sempre solicite diagramas Mermaid no prompt."""
    app = ArchitectReasoningEngineApp()
    app._provider = mock_provider

    task = "Design a distributed payment gateway"
    await app.query(input=task)

    args, _ = mock_provider.generate.call_args
    user_message = args[0][1]["content"]

    assert "DESIGN TASK: " + task in user_message
    assert "Mermaid diagram" in user_message
    assert "trade-offs" in user_message


@pytest.mark.asyncio
async def test_architect_handles_complex_dict_input(mock_provider):
    """Valida o suporte a inputs complexos (dict) no Arquiteto."""
    app = ArchitectReasoningEngineApp()
    app._provider = mock_provider

    complex_input = {
        "user_input": "Scalable chat system",
        "constraints": ["latency < 100ms", "high availability"],
    }
    await app.query(input=complex_input)

    args, _ = mock_provider.generate.call_args
    user_message = args[0][1]["content"]

    assert "DESIGN TASK: Scalable chat system" in user_message

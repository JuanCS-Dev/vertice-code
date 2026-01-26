import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.reviewer.reasoning_engine_app import ReviewerReasoningEngineApp


@pytest.fixture
def mock_cortex():
    with patch("agents.reviewer.reasoning_engine_app.MemoryCortex") as mock:
        instance = mock.return_value
        instance.to_context_prompt = AsyncMock(
            return_value="RELEVANT_FACT: Always use PascalCase for classes."
        )
        yield instance


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="Review output")
    return provider


@pytest.mark.asyncio
async def test_reviewer_injects_semantic_memory_context(mock_cortex, mock_provider):
    """Garante que o Revisor consulte a memória semântica antes de gerar a revisão."""
    app = ReviewerReasoningEngineApp()
    app._provider = mock_provider
    app._cortex = mock_cortex

    code_input = "class user_auth: pass"
    await app.query(input={"code": code_input})

    # Verifica se o contexto foi solicitado ao Cortex baseado no input
    mock_cortex.to_context_prompt.assert_called_once_with(code_input)

    # Verifica se o contexto retornado pelo Cortex foi parar no prompt enviado ao LLM
    args, kwargs = mock_provider.generate.call_args
    messages = args[0]
    user_message = messages[1]["content"]

    assert "RELEVANT_FACT: Always use PascalCase for classes." in user_message
    assert "REVIEW TASK:" in user_message

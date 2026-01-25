import pytest
from unittest.mock import AsyncMock, patch
from vertice_tui.core.managers.auth_manager import AuthenticationManager


@pytest.fixture
def auth_manager():
    return AuthenticationManager()


@pytest.mark.parametrize(
    "provider, key, expected, error_part",
    [
        # OpenAI tests
        ("openai", "sk-" + "a" * 48, True, ""),
        ("openai", "sk-" + "a" * 47, False, "format"),
        ("openai", "sk-" + "a" * 49, False, "format"),
        ("openai", "fk-" + "a" * 48, False, "format"),
        # Anthropic tests
        ("anthropic", "sk-ant-api" + "a" * 93, True, ""),
        ("anthropic", "sk-ant-api" + "a" * 92, False, "format"),
        ("anthropic", "sk-ant-api" + "a" * 94, False, "format"),
        # Google tests
        ("google", "AIza" + "a" * 35, True, ""),
        ("google", "AIza" + "a" * 34, False, "format"),
        ("google", "AIza" + "a" * 36, False, "format"),
        # Groq tests
        ("groq", "gsk_" + "a" * 52, True, ""),
        ("groq", "gsk_" + "a" * 51, False, "format"),
        ("groq", "gsk_" + "a" * 53, False, "format"),
        # General tests
        (None, "a" * 20, True, ""),
        ("unknown", "a" * 20, True, ""),
        (None, "a" * 19, False, "short"),
        (None, " a" * 20, False, "whitespace"),
        (None, "a" * 20 + " ", False, "whitespace"),
        (None, "a\n" * 20, False, "control"),
    ],
)
def test_validate_api_key(auth_manager, provider, key, expected, error_part):
    is_valid, error = auth_manager.validate_api_key(key, provider=provider)
    assert is_valid == expected
    if not expected:
        assert error_part in error


@pytest.mark.asyncio
@patch("vertice_tui.core.managers.auth_manager.get_client")
async def test_test_api_key_success(mock_get_client):
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client
    auth_manager = AuthenticationManager()

    result = await auth_manager.test_api_key("valid_key", "openai")

    assert result is True
    mock_get_client.assert_called_once_with("openai", "valid_key")
    assert mock_client.generate.called or mock_client.list_models.called


@pytest.mark.asyncio
@patch("vertice_tui.core.managers.auth_manager.get_client")
async def test_test_api_key_auth_error(mock_get_client):
    from vertice_core.core.errors.types import AuthenticationError

    mock_client = AsyncMock()
    mock_client.generate.side_effect = AuthenticationError("test auth error")
    mock_client.list_models.side_effect = AuthenticationError("test auth error")
    mock_get_client.return_value = mock_client
    auth_manager = AuthenticationManager()

    result = await auth_manager.test_api_key("invalid_key", "openai")

    assert result is False


@pytest.mark.asyncio
@patch("vertice_tui.core.managers.auth_manager.get_client")
async def test_test_api_key_other_exception(mock_get_client):
    mock_client = AsyncMock()
    mock_client.generate.side_effect = Exception("test error")
    mock_client.list_models.side_effect = Exception("test error")
    mock_get_client.return_value = mock_client
    auth_manager = AuthenticationManager()

    result = await auth_manager.test_api_key("any_key", "openai")

    assert result is False

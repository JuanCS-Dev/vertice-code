
import sys
from unittest.mock import MagicMock, Mock, patch
import pytest

# Mock only the problematic protobuf-related modules
# This is a targeted workaround for a known environment issue.
MOCK_MODULES = [
    'core',
    'core.resilience',
    'core.protocols',
    'core.protocols.proto',
    'google.protobuf',
    'vertice_cli.core.providers.resilience',
    'vertice_cli.core.providers.maximus_config',
    'vertice_cli.core.providers.maximus_provider'
]
for mod in MOCK_MODULES:
    sys.modules[mod] = MagicMock()


from vertice_cli.core.providers.vertice_router import VerticeRouter, LLMProvider
from vertice_cli.core.types import ModelInfo

class MockProvider(LLMProvider):
    def __init__(self, model_info):
        self._model_info = model_info

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> ModelInfo:
        return self._model_info

    async def generate(self, messages, **kwargs):
        return "response"

    async def stream_generate(self, messages, **kwargs):
        yield "response"

    async def stream_chat(self, messages, **kwargs):
        yield "response"

@pytest.fixture
def router() -> VerticeRouter:
    r = VerticeRouter()
    r._initialized = False
    r._providers = {}
    r._status = {}
    return r

def test_route_with_invalid_schema_raises_value_error(router: VerticeRouter):
    """
    Tests that router.route() raises a ValueError when a provider's model_info
    is missing the required 'model' key.
    """
    invalid_model_info = {"provider": "mock", "cost_tier": "free", "speed_tier": "fast"}
    mock_provider = MockProvider(invalid_model_info)

    router._providers = {"mock-provider": mock_provider}
    router._status = {"mock-provider": Mock(can_use=lambda: True)}
    router._initialized = True

    router.PROVIDER_PRIORITY = {"mock-provider": 1}
    router.COMPLEXITY_ROUTING = {"moderate": ["mock-provider"]}
    router.SPEED_ROUTING = {"normal": ["mock-provider"]}

    with pytest.raises(ValueError, match="Provider 'mock-provider' returned invalid model info: missing 'model' key."):
        router.route()

def test_route_with_valid_schema_succeeds(router: VerticeRouter):
    """
    Tests that router.route() succeeds when a provider's model_info
    conforms to the schema.
    """
    valid_model_info = ModelInfo(model="test-model", provider="mock", cost_tier="free", speed_tier="fast")
    mock_provider = MockProvider(valid_model_info)

    router._providers = {"mock-provider": mock_provider}
    router._status = {"mock-provider": Mock(can_use=lambda: True)}
    router._initialized = True

    router.PROVIDER_PRIORITY = {"mock-provider": 1}
    router.COMPLEXITY_ROUTING = {"moderate": ["mock-provider"]}
    router.SPEED_ROUTING = {"normal": ["mock-provider"]}

    decision = router.route()

    assert decision is not None
    assert decision.provider_name == "mock-provider"
    assert decision.model_name == "test-model"

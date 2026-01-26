import pytest
import os
import json
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
import importlib.util


# Dinamicamente carrega o app do gateway para contornar o hífen no path
def load_gateway_app():
    repo_root = Path(__file__).resolve().parents[2]
    app_path = repo_root / "apps" / "agent-gateway" / "app" / "main.py"
    module_name = "gateway_main"
    spec = importlib.util.spec_from_file_location(module_name, str(app_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # Registra no sys.modules para dataclasses
    spec.loader.exec_module(module)
    return module


gateway_module = load_gateway_app()
app = gateway_module.app


@pytest.fixture
def mock_engines_config(tmp_path):
    config = {
        "engines": {
            "coder": {
                "engine_id": "projects/p/locations/l/reasoningEngines/123",
                "project": "vertice-ai",
                "location": "us-central1",
            }
        },
        "updated_at": "2026-01-25T00:00:00Z",
    }
    config_file = tmp_path / "engines.json"
    config_file.write_text(json.dumps(config))
    return config_file


@pytest.mark.asyncio
async def test_gateway_routes_to_vertex_when_enabled(mock_engines_config):
    """Valida se o gateway chama o adaptador Vertex quando a flag está ativa."""

    # 1. Setup do ambiente e mocks
    with patch("gateway_main.ENGINES_CONFIG_PATH", mock_engines_config), patch(
        "gateway_main._vertex_enabled", return_value=True
    ), patch("gateway_main.stream_vertex_agent_engine_adk_events") as mock_stream:
        # Simula o stream vindo do Vertex
        async def mock_events(**kwargs):
            yield {"type": "delta", "text": "Hello from Vertex"}
            yield {"type": "final", "text": "Done", "metadata": {}}

        mock_stream.side_effect = mock_events

        # 2. Executa a requisição via TestClient (FastAPI)
        client = TestClient(app)
        response = client.get("/agui/stream?prompt=test&agent=coder")

        # 3. Validações
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        mock_stream.assert_called_once()
        call_kwargs = mock_stream.call_args.kwargs
        assert call_kwargs["spec"].engine_id == "projects/p/locations/l/reasoningEngines/123"
        assert call_kwargs["prompt"] == "test"


@pytest.mark.asyncio
async def test_gateway_error_on_missing_engine_config(mock_engines_config):
    """Garante que o gateway retorna erro se o agente solicitado não estiver no engines.json."""

    with patch("gateway_main.ENGINES_CONFIG_PATH", mock_engines_config), patch(
        "gateway_main._vertex_enabled", return_value=True
    ):
        client = TestClient(app)
        response = client.get("/agui/stream?prompt=test&agent=architect")

        content = response.text
        assert "event: error" in content
        assert "engine not configured for agent='architect'" in content

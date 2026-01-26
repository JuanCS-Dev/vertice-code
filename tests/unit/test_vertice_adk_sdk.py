import pytest
from vertice_core.adk.base import VerticeAgent
from vertice_core.adk.tools import vertice_tool
from typing import Dict, Any
from collections.abc import Mapping

from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_vertex_ai_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="Mocked response")
    return provider


class SecurityAgent(VerticeAgent):
    """Exemplo de agente criado via SDK."""

    @property
    def system_prompt(self):
        return "You are a security auditor."

    @vertice_tool
    def scan_file(self, filename: str) -> str:
        """Scan a file for vulnerabilities."""
        return f"Scan complete for {filename}: No issues found."

    async def query(self, *, input: str | Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        prompt = input if isinstance(input, str) else input.get("prompt", "")
        output = await self._generate_response(prompt)
        return {"output": output}


@pytest.mark.asyncio
async def test_sdk_agent_compliance(mock_vertex_ai_provider):
    """Valida se um agente criado com o SDK segue o contrato de 2026."""
    agent = SecurityAgent()
    agent._provider = mock_vertex_ai_provider

    # 1. Valida o contrato de query
    resp = await agent.query(input="Audite este código")
    assert "output" in resp

    # 2. Valida os requisitos
    reqs = agent.get_requirements()
    assert "vertice-core" in reqs
    assert "google-genai==1.2.0" in reqs

    # 3. Valida a identidade
    assert agent.system_prompt == "You are a security auditor."

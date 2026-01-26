import json

import pytest
from aiohttp import web

from vertice_core.prometheus.mcp_server.config import MCPServerConfig
from vertice_core.prometheus.mcp_server.server import PrometheusMCPServer
from vertice_core.prometheus.mcp_server.transport import MCPHTTPServer


class _DummyRequest:
    def __init__(self, payload: dict, *, content_type: str = "application/json", headers: dict | None = None):
        self._payload = payload
        self.content_type = content_type
        self.headers = headers or {}

    async def json(self) -> dict:
        return self._payload


@pytest.mark.asyncio
async def test_mcp_server_health_initialize_tools_list_and_status():
    config = MCPServerConfig(host="127.0.0.1", port=3000, enable_execution_tools=False)
    mcp_server = PrometheusMCPServer(config)
    http_server = MCPHTTPServer(mcp_server, config)

    await mcp_server.start()

    try:
        health_response = await http_server.handle_health_check(object())
        assert isinstance(health_response, web.Response)
        assert health_response.status == 200
        health_payload = json.loads(health_response.body.decode("utf-8"))
        assert health_payload["status"] == "healthy"

        initialize_request = {"jsonrpc": "2.0", "id": "1", "method": "initialize", "params": {}}
        initialize_response = await http_server.handle_mcp_request(_DummyRequest(initialize_request))
        assert initialize_response.status == 200
        initialize_payload = json.loads(initialize_response.body.decode("utf-8"))
        assert initialize_payload["id"] == "1"
        assert initialize_payload["result"]["protocolVersion"] == "2024-11-05"

        tools_list_request = {"jsonrpc": "2.0", "id": "2", "method": "tools/list", "params": {}}
        tools_list_response = await http_server.handle_mcp_request(_DummyRequest(tools_list_request))
        assert tools_list_response.status == 200
        tools_list_payload = json.loads(tools_list_response.body.decode("utf-8"))
        tools = tools_list_payload["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) >= 1

        status_response = await http_server.handle_status(object())
        assert status_response.status == 200
        status_payload = json.loads(status_response.body.decode("utf-8"))
        assert "http" in status_payload
        assert status_payload["http"]["uptime_seconds"] >= 0
    finally:
        await mcp_server.stop()

"""
Vertice MCP Client Implementation

Generated with ❤️ by Vertex AI Codey
For seamless integration with the collective AI ecosystem.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any

from vertice_mcp.types import (
    MCPClientConfig,
    AgentTask,
    AgentResponse,
    Skill,
    MCPError,
    AuthenticationError,
    PermissionError,
    NetworkError,
    ValidationError,
    RateLimitError,
    ServerError,
)


class MCPClient:
    """
    Synchronous MCP Client for Vertice Collective AI.

    Generated with ❤️ by AI for human-AI collaboration.
    """

    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self._session = None

    def __enter__(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            asyncio.run(self._session.close())

    def submit_task(self, task: AgentTask) -> AgentResponse:
        """Submit a task to the MCP collective."""

        async def _submit():
            return await self._async_submit_task(task)

        return asyncio.run(_submit())

    async def _async_submit_task(self, task: AgentTask) -> AgentResponse:
        """Async implementation of task submission."""
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with' or '__enter__'")

        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/submit",
            "params": task.to_dict(),
            "id": task.id,
        }

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        async with self._session.post(
            f"{self.config.endpoint}/mcp", json=payload, headers=headers
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return AgentResponse.from_dict(result["result"])

    def get_skills(self) -> List[Skill]:
        """Retrieve available skills from the collective."""

        async def _get():
            return await self._async_get_skills()

        return asyncio.run(_get())

    async def _async_get_skills(self) -> List[Skill]:
        """Async implementation of skills retrieval."""
        if not self._session:
            raise RuntimeError("Client not initialized")

        payload = {"jsonrpc": "2.0", "method": "skills/list", "params": {}, "id": "skills-list"}

        async with self._session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return [Skill.from_dict(s) for s in result["result"]["skills"]]

    def share_skill(self, skill: Skill) -> bool:
        """Share a skill with the collective."""

        async def _share():
            return await self._async_share_skill(skill)

        return asyncio.run(_share())

    async def _async_share_skill(self, skill: Skill) -> bool:
        """Async implementation of skill sharing."""
        if not self._session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "skills/share",
            "params": {"skill": skill.to_dict()},
            "id": "skill-share",
        }

        async with self._session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]["success"]

    def learn_skill(
        self, name: str, description: str, procedure_steps: List[str], category: str = "general"
    ) -> bool:
        """Learn a new skill and register it with the collective."""

        async def _learn():
            return await self._async_learn_skill(name, description, procedure_steps, category)

        return asyncio.run(_learn())

    async def _async_learn_skill(
        self, name: str, description: str, procedure_steps: List[str], category: str = "general"
    ) -> bool:
        """Async implementation of skill learning."""
        if not self._session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "prometheus_learn_skill",
                "arguments": {
                    "name": name,
                    "description": description,
                    "procedure_steps": procedure_steps,
                    "category": category,
                },
            },
            "id": f"learn-skill-{name}",
        }

        async with self._session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]["success"]

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Retrieve information about a specific skill."""

        async def _get():
            return await self._async_get_skill(skill_name)

        return asyncio.run(_get())

    async def _async_get_skill(self, skill_name: str) -> Optional[Skill]:
        """Async implementation of skill retrieval."""
        if not self._session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "prometheus_get_skill", "arguments": {"skill_name": skill_name}},
            "id": f"get-skill-{skill_name}",
        }

        async with self._session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            skill_data = result["result"]

            if skill_data.get("found", False):
                return Skill.from_dict(skill_data["skill"])

            return None

    def get_status(self) -> Dict[str, Any]:
        """Get MCP server status."""

        async def _get():
            return await self._async_get_status()

        return asyncio.run(_get())

    async def _async_get_status(self) -> Dict[str, Any]:
        """Async implementation of status retrieval."""
        if not self._session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "prometheus/status",
            "params": {},
            "id": "status-check",
        }

        async with self._session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]

    async def _handle_error_response(self, response: aiohttp.ClientResponse):
        """Handle error responses from the server."""
        try:
            error_data = await response.json()
            error = error_data.get("error", {})

            error_code = error.get("code")
            error_message = error.get("message", f"HTTP {response.status}")

            if response.status == 401:
                raise AuthenticationError(error_message, error_code)
            elif response.status == 403:
                raise PermissionError(error_message, error_code)
            elif response.status == 429:
                raise RateLimitError(error_message, error_code)
            elif response.status == 400:
                raise ValidationError(error_message, error_code)
            elif response.status >= 500:
                raise ServerError(error_message, error_code)
            else:
                raise MCPError(error_message, error_code)

        except aiohttp.ClientError:
            raise NetworkError(f"Network error: HTTP {response.status}")

    def close(self):
        """Close the client session."""
        if self._session:
            asyncio.run(self._session.close())
            self._session = None


class AsyncMCPClient:
    """
    Asynchronous MCP Client for Vertice Collective AI.

    For applications that need async operations throughout.
    """

    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def submit_task(self, task: AgentTask) -> AgentResponse:
        """Submit a task asynchronously."""
        return await self._async_submit_task(task)

    async def get_skills(self) -> List[Skill]:
        """Get skills asynchronously."""
        return await self._async_get_skills()

    async def share_skill(self, skill: Skill) -> bool:
        """Share skill asynchronously."""
        return await self._async_share_skill(skill)

    async def learn_skill(
        self, name: str, description: str, procedure_steps: List[str], category: str = "general"
    ) -> bool:
        """Learn skill asynchronously."""
        return await self._async_learn_skill(name, description, procedure_steps, category)

    async def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get skill asynchronously."""
        return await self._async_get_skill(skill_name)

    async def get_status(self) -> Dict[str, Any]:
        """Get status asynchronously."""
        return await self._async_get_status()

    # Reuse the implementation from MCPClient but with self.session
    async def _async_submit_task(self, task: AgentTask) -> AgentResponse:
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with'")

        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/submit",
            "params": task.to_dict(),
            "id": task.id,
        }

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        async with self.session.post(
            f"{self.config.endpoint}/mcp", json=payload, headers=headers
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return AgentResponse.from_dict(result["result"])

    async def _async_get_skills(self) -> List[Skill]:
        if not self.session:
            raise RuntimeError("Client not initialized")

        payload = {"jsonrpc": "2.0", "method": "skills/list", "params": {}, "id": "skills-list"}

        async with self.session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return [Skill.from_dict(s) for s in result["result"]["skills"]]

    async def _async_share_skill(self, skill: Skill) -> bool:
        if not self.session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "skills/share",
            "params": {"skill": skill.to_dict()},
            "id": "skill-share",
        }

        async with self.session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]["success"]

    async def _async_learn_skill(
        self, name: str, description: str, procedure_steps: List[str], category: str = "general"
    ) -> bool:
        if not self.session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "prometheus_learn_skill",
                "arguments": {
                    "name": name,
                    "description": description,
                    "procedure_steps": procedure_steps,
                    "category": category,
                },
            },
            "id": f"learn-skill-{name}",
        }

        async with self.session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]["success"]

    async def _async_get_skill(self, skill_name: str) -> Optional[Skill]:
        if not self.session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "prometheus_get_skill", "arguments": {"skill_name": skill_name}},
            "id": f"get-skill-{skill_name}",
        }

        async with self.session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            skill_data = result["result"]

            if skill_data.get("found", False):
                return Skill.from_dict(skill_data["skill"])

            return None

    async def _async_get_status(self) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("Client not initialized")

        payload = {
            "jsonrpc": "2.0",
            "method": "prometheus/status",
            "params": {},
            "id": "status-check",
        }

        async with self.session.post(
            f"{self.config.endpoint}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                await self._handle_error_response(response)

            result = await response.json()
            return result["result"]

    async def _handle_error_response(self, response: aiohttp.ClientResponse):
        """Handle error responses."""
        try:
            error_data = await response.json()
            error = error_data.get("error", {})

            error_code = error.get("code")
            error_message = error.get("message", f"HTTP {response.status}")

            if response.status == 401:
                raise AuthenticationError(error_message, error_code)
            elif response.status == 403:
                raise PermissionError(error_message, error_code)
            elif response.status == 429:
                raise RateLimitError(error_message, error_code)
            elif response.status == 400:
                raise ValidationError(error_message, error_code)
            elif response.status >= 500:
                raise ServerError(error_message, error_code)
            else:
                raise MCPError(error_message, error_code)

        except aiohttp.ClientError:
            raise NetworkError(f"Network error: HTTP {response.status}")

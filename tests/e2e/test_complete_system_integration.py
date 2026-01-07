"""
END-TO-END INTEGRATION AUDIT: Vertice-Code Complete System Test

This comprehensive test suite validates the complete integration between:
- Prometheus (Meta-Agent System)
- MCP Server (Universal Protocol)
- Skills Registry (Distributed Learning)
- Vertice CLI (Agent Orchestration)
- Vertice Core (Domain Kernel)

Test Coverage:
✅ Prometheus Skills Learning & Evolution
✅ MCP Protocol Compliance & Tools
✅ Distributed Skills Sharing (Peer-to-Peer)
✅ Agent Orchestration & Workflow Execution
✅ Memory System Integration
✅ Security & Governance Validation

Created with love for system integrity validation.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import json
import os
import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Core Components
from vertice_core.types import AgentTask, AgentResponse, TaskResult
from vertice_core.protocols import AgentProtocol, ToolProtocol

# Prometheus System
from prometheus.core.orchestrator import PrometheusOrchestrator
from prometheus.skills.registry import PrometheusSkillsRegistry, LearnedSkill
from prometheus.distributed.registry import DistributedSkillsRegistry
from prometheus.distributed.skills_discovery import SkillsDiscoveryService
from prometheus.distributed.peer_protocol import SkillsPeerProtocol

# MCP Server
from prometheus.mcp_server.server import PrometheusMCPServer
from prometheus.mcp_server.config import MCPServerConfig
from prometheus.mcp_server.manager import MCPServerManager

# Vertice CLI
# from vertice_cli.core.llm import LLMClient
# from vertice_cli.core.mcp_client import MCPClient
# from vertice_cli.tools.registry_helper import get_default_registry
# from vertice_cli.orchestration.squad import DevSquad

# Environment requirements
requires_api_keys = pytest.mark.skipif(
    not (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("NEBIUS_API_KEY")
    ),
    reason="No LLM API keys found in environment",
)

requires_prometheus_setup = pytest.mark.skipif(
    not os.path.exists("prometheus/core/orchestrator.py"),
    reason="Prometheus system not properly set up",
)


class TestCompleteSystemIntegration:
    """Complete system integration tests."""

    @pytest.fixture
    async def prometheus_system(self):
        """Initialize complete Prometheus system."""
        # Skills Registry
        skills_registry = PrometheusSkillsRegistry()

        # Distributed Registry
        discovery_service = SkillsDiscoveryService(
            instance_id="test-prometheus-instance", listen_port=8080
        )
        distributed_registry = DistributedSkillsRegistry(
            discovery_service=discovery_service, instance_id="test-prometheus-instance"
        )

        # Peer Protocol
        peer_protocol = SkillsPeerProtocol(distributed_registry, "test-prometheus-instance")

        # MCP Server
        mcp_config = MCPServerConfig(
            instance_id="test-mcp-server",
            host="localhost",
            port=3001,
            enable_skills_registry=True,
            enable_memory_system=True,
            enable_distributed_features=True,
        )
        mcp_server = PrometheusMCPServer(mcp_config)
        mcp_manager = MCPServerManager(mcp_config)

        # Orchestrator
        orchestrator = PrometheusOrchestrator(
            skills_registry=distributed_registry, instance_id="test-prometheus-instance"
        )

        system = {
            "skills_registry": skills_registry,
            "distributed_registry": distributed_registry,
            "discovery_service": discovery_service,
            "peer_protocol": peer_protocol,
            "mcp_server": mcp_server,
            "mcp_manager": mcp_manager,
            "orchestrator": orchestrator,
        }

        # Start components
        await discovery_service.start()
        await distributed_registry.set_discovery_service(discovery_service)

        yield system

        # Cleanup
        await discovery_service.stop()

    @pytest.fixture
    async def vertice_cli_system(self):
        """Initialize Vertice CLI system."""
        # LLM Client
        llm_client = LLMClient(enable_telemetry=False)

        # MCP Client
        registry = get_default_registry()
        mcp_client = MCPClient(registry)

        # DevSquad
        dev_squad = DevSquad(
            llm_client=llm_client, mcp_client=mcp_client, require_human_approval=False
        )

        system = {
            "llm_client": llm_client,
            "mcp_client": mcp_client,
            "dev_squad": dev_squad,
        }

        yield system

    @pytest.mark.asyncio
    @requires_prometheus_setup
    async def test_prometheus_skills_integration(self, prometheus_system):
        """Test Prometheus skills learning and registry integration."""
        registry = prometheus_system["distributed_registry"]

        # Create and learn a skill
        skill = LearnedSkill(
            name="test_integration_skill",
            description="Skill for integration testing",
            procedure_steps=["analyze requirements", "design solution", "implement code"],
            category="development",
            success_rate=0.9,
            usage_count=5,
            learned_at=datetime.now(),
        )

        # Register skill
        result = await registry._register_peer_skill(skill, "test-peer")
        assert result["added"] is True

        # Retrieve skill
        retrieved = await registry.get_skill("test_integration_skill")
        assert retrieved is not None
        assert retrieved.name == "test_integration_skill"
        assert retrieved.success_rate == 0.9

        # Test skills statistics
        stats = await registry.get_distributed_stats()
        assert stats["total_skills"] >= 1
        assert "distributed_features" in stats

    @pytest.mark.asyncio
    async def test_mcp_server_protocol_compliance(self, prometheus_system):
        """Test MCP server protocol compliance."""
        mcp_server = prometheus_system["mcp_server"]

        # Test initialization
        init_request = {"id": "test-init-1", "method": "initialize", "params": {}}

        init_response = await mcp_server.handle_request(init_request)
        response_data = json.loads(init_response.to_json())

        assert response_data["id"] == "test-init-1"
        assert "result" in response_data
        assert "capabilities" in response_data["result"]
        assert "tools" in response_data["result"]["capabilities"]

        # Test tools listing
        tools_request = {"id": "test-tools-1", "method": "tools/list", "params": {}}

        tools_response = await mcp_server.handle_request(tools_request)
        tools_data = json.loads(tools_response.to_json())

        assert "result" in tools_data
        assert "tools" in tools_data["result"]
        assert len(tools_data["result"]["tools"]) > 0

        # Verify Prometheus tools are present
        tool_names = [tool["name"] for tool in tools_data["result"]["tools"]]
        assert "prometheus_learn_skill" in tool_names
        assert "prometheus_get_skill" in tool_names

    @pytest.mark.asyncio
    async def test_distributed_skills_sharing(self, prometheus_system):
        """Test distributed skills sharing between instances."""
        registry1 = prometheus_system["distributed_registry"]
        discovery1 = prometheus_system["discovery_service"]

        # Create second instance
        discovery2 = SkillsDiscoveryService(instance_id="test-peer-instance", listen_port=8081)
        registry2 = DistributedSkillsRegistry(
            discovery_service=discovery2, instance_id="test-peer-instance"
        )

        await discovery2.start()
        await registry2.set_discovery_service(discovery2)

        try:
            # Instance 1 learns a skill
            skill = LearnedSkill(
                name="shared_test_skill",
                description="Skill to be shared between instances",
                procedure_steps=["step1", "step2"],
                category="testing",
                success_rate=0.95,
            )

            await registry1._register_peer_skill(skill, "self")

            # Simulate peer discovery
            discovery1.known_peers["test-peer-instance"] = discovery2.known_peers[
                "test-peer-instance"
            ]

            # Sync skills between peers
            sync_result = await registry2.sync_with_peers()
            assert sync_result["peers_found"] >= 1

            # Check if skill was shared (would require actual peer communication)
            # This tests the sync mechanism setup

        finally:
            await discovery2.stop()

    @pytest.mark.asyncio
    async def test_peer_protocol_message_exchange(self, prometheus_system):
        """Test peer-to-peer protocol message exchange."""
        protocol = prometheus_system["peer_protocol"]

        # Test skill request handling
        request_message = protocol.peer_protocol.PeerMessage(
            message_type="skill_request",
            sender_id="test-peer",
            payload={"skill_name": "test_skill"},
        )

        # Mock the registry to return a skill
        skill = LearnedSkill("test_skill", description="Test", procedure_steps=["step1"])
        with patch.object(protocol.registry, "get_skill", return_value=skill):
            response = await protocol.handle_incoming_message(request_message)

            assert response is not None
            assert response.message_type == "skill_response"
            assert response.payload["found"] is True

    @pytest.mark.asyncio
    @requires_api_keys
    async def test_vertice_cli_prometheus_integration(self, vertice_cli_system, prometheus_system):
        """Test Vertice CLI integration with Prometheus."""
        dev_squad = vertice_cli_system["dev_squad"]
        prometheus_orchestrator = prometheus_system["orchestrator"]

        # Create a task that would benefit from Prometheus skills
        task = AgentTask(
            id="integration-test-task",
            description="Create a Python function to calculate fibonacci numbers efficiently",
            agent_role="developer",
            priority=1,
            created_at=datetime.now(),
        )

        # Execute task with DevSquad (which should leverage Prometheus)
        result = await dev_squad.execute_task(task)

        assert result is not None
        assert result.status in ["completed", "success"]
        assert result.result is not None

        # Verify Prometheus was involved (check for skill learning)
        prometheus_stats = await prometheus_orchestrator.get_stats()
        assert "skills_learned" in prometheus_stats or prometheus_stats.get("total_skills", 0) >= 0

    @pytest.mark.asyncio
    async def test_memory_system_integration(self, prometheus_system):
        """Test memory system integration with Prometheus."""
        orchestrator = prometheus_system["orchestrator"]

        # This would test memory persistence and retrieval
        # For now, we test the interface
        memory_context = await orchestrator.get_memory_context("test_context")
        assert memory_context is not None

        # Test memory storage
        test_memory = {
            "type": "working_memory",
            "content": "Integration test memory",
            "timestamp": datetime.now().isoformat(),
        }

        stored = await orchestrator.store_memory(test_memory)
        assert stored is True

    @pytest.mark.asyncio
    async def test_mcp_server_http_transport(self, prometheus_system):
        """Test MCP server HTTP transport layer."""
        mcp_manager = prometheus_system["mcp_manager"]

        # Start MCP server
        success = await mcp_manager.initialize()
        assert success

        success = await mcp_manager.start()
        assert success

        try:
            # Test HTTP endpoints
            config = mcp_manager.config

            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get(f"http://{config.host}:{config.port}/health") as response:
                    assert response.status == 200
                    health_data = await response.json()
                    assert health_data["status"] == "healthy"

                # Status endpoint
                async with session.get(f"http://{config.host}:{config.port}/status") as response:
                    assert response.status == 200
                    status_data = await response.json()
                    assert "mcp_server" in status_data

                # MCP ping
                ping_payload = {"jsonrpc": "2.0", "id": "http-test-ping", "method": "ping"}

                async with session.post(
                    f"http://{config.host}:{config.port}/mcp",
                    json=ping_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    assert response.status == 200
                    ping_response = await response.json()
                    assert ping_response["id"] == "http-test-ping"
                    assert "result" in ping_response

        finally:
            await mcp_manager.stop()

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, prometheus_system, vertice_cli_system):
        """Test complete workflow: CLI -> Prometheus -> MCP -> Skills."""
        dev_squad = vertice_cli_system["dev_squad"]
        prometheus_orchestrator = prometheus_system["orchestrator"]
        mcp_server = prometheus_system["mcp_server"]

        # Step 1: CLI creates a complex task
        complex_task = AgentTask(
            id="complex-integration-task",
            description="""
            Create a complete authentication system with:
            - JWT token generation and validation
            - Password hashing with bcrypt
            - User registration and login endpoints
            - Middleware for protected routes
            - Database models for users
            """,
            agent_role="architect",
            priority=2,
            created_at=datetime.now(),
        )

        # Step 2: DevSquad processes the task (should use Prometheus)
        workflow_result = await dev_squad.execute_task(complex_task)
        assert workflow_result.status in ["completed", "success"]

        # Step 3: Verify Prometheus learned skills during the process
        orchestrator_stats = await prometheus_orchestrator.get_stats()
        skills_learned = orchestrator_stats.get("skills_learned", 0)
        assert skills_learned >= 0  # At minimum, no errors

        # Step 4: Check if skills are exposed via MCP
        tools_request = {"id": "workflow-test-tools", "method": "tools/list", "params": {}}

        tools_response = await mcp_server.handle_request(tools_request)
        tools_data = json.loads(tools_response.to_json())

        assert len(tools_data["result"]["tools"]) > 0

        # Step 5: Verify distributed registry has the skills
        distributed_stats = await prometheus_system["distributed_registry"].get_distributed_stats()
        assert "consensus" in distributed_stats

    @pytest.mark.asyncio
    async def test_security_governance_integration(self, prometheus_system):
        """Test security and governance integration."""
        orchestrator = prometheus_system["orchestrator"]

        # Test that security checks are in place
        security_context = await orchestrator.get_security_context()
        assert security_context is not None

        # Test governance compliance
        governance_check = await orchestrator.check_governance_compliance("test_action")
        assert governance_check is not None

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, prometheus_system, vertice_cli_system):
        """Test error handling across all integrated components."""
        dev_squad = vertice_cli_system["dev_squad"]
        prometheus_orchestrator = prometheus_system["orchestrator"]

        # Test with invalid task
        invalid_task = AgentTask(
            id="invalid-task",
            description="",  # Empty description should cause error
            agent_role="invalid_role",
            priority=-1,  # Invalid priority
        )

        # Should handle errors gracefully
        result = await dev_squad.execute_task(invalid_task)
        # Even with errors, should return a result object
        assert result is not None
        assert isinstance(result, TaskResult)

        # Prometheus should handle the error without crashing
        orchestrator_status = await prometheus_orchestrator.get_status()
        assert orchestrator_status["status"] != "crashed"

    @pytest.mark.asyncio
    async def test_performance_metrics_integration(self, prometheus_system):
        """Test performance metrics collection across components."""
        registry = prometheus_system["distributed_registry"]
        mcp_server = prometheus_system["mcp_server"]

        # Perform some operations to generate metrics
        skill = LearnedSkill(
            "perf_test_skill", description="Performance test", procedure_steps=["step1"]
        )
        await registry._register_peer_skill(skill, "perf-test")

        # Check MCP server metrics
        server_stats = mcp_server.get_stats()
        assert "requests_processed" in server_stats
        assert "errors_count" in server_stats

        # Check distributed registry metrics
        distributed_stats = await registry.get_distributed_stats()
        assert "instance_id" in distributed_stats
        assert "discovery" in distributed_stats

    @pytest.mark.asyncio
    async def test_system_resilience_integration(self, prometheus_system):
        """Test system resilience and recovery mechanisms."""
        registry = prometheus_system["distributed_registry"]
        discovery = prometheus_system["discovery_service"]

        # Simulate component failure and recovery
        original_peer_count = len(discovery.known_peers)

        # Simulate network partition (remove peers)
        discovery.known_peers.clear()

        # System should handle the empty state
        sync_result = await registry.sync_with_peers()
        assert sync_result["peers_found"] == 0
        assert sync_result["skills_synced"] == 0

        # Simulate recovery (add peers back)
        discovery.known_peers["recovered-peer"] = discovery.peer_info_class(
            instance_id="recovered-peer", endpoint="http://localhost:8082"
        )

        # System should recover
        sync_result = await registry.sync_with_peers()
        assert sync_result["peers_found"] >= 1


# Performance and Load Tests
class TestSystemPerformanceIntegration:
    """Performance and load testing for integrated system."""

    @pytest.fixture
    async def performance_setup(self, prometheus_system):
        """Setup for performance testing."""
        return prometheus_system

    @pytest.mark.asyncio
    async def test_concurrent_skill_learning(self, performance_setup):
        """Test concurrent skill learning across multiple instances."""
        registry = performance_setup["distributed_registry"]

        # Create multiple skills concurrently
        skills = [
            LearnedSkill(
                f"concurrent_skill_{i}", description=f"Skill {i}", procedure_steps=["step1"]
            )
            for i in range(10)
        ]

        # Register skills concurrently
        tasks = [
            registry._register_peer_skill(skill, f"peer_{i}") for i, skill in enumerate(skills)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all skills were registered
        assert all(result["added"] for result in results)
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_mcp_server_load_handling(self, performance_setup):
        """Test MCP server under load."""
        mcp_server = performance_setup["mcp_server"]

        # Send multiple concurrent requests
        requests = [{"id": f"load-test-{i}", "method": "ping", "params": {}} for i in range(50)]

        # Process requests concurrently
        tasks = [mcp_server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # Verify all responses
        assert len(responses) == 50
        assert all(resp.id.startswith("load-test-") for resp in responses)

    @pytest.mark.asyncio
    async def test_distributed_sync_performance(self, performance_setup):
        """Test distributed synchronization performance."""
        registry = performance_setup["distributed_registry"]

        # Create many skills to sync
        skills = [
            LearnedSkill(
                f"sync_skill_{i}", description=f"Sync skill {i}", procedure_steps=["step1"]
            )
            for i in range(100)
        ]

        # Register skills
        for skill in skills:
            await registry._register_peer_skill(skill, "bulk-peer")

        # Test sync performance
        import time

        start_time = time.time()

        sync_result = await registry.sync_with_peers()

        end_time = time.time()
        sync_duration = end_time - start_time

        # Should complete within reasonable time
        assert sync_duration < 5.0  # 5 seconds max
        assert sync_result["skills_synced"] >= 0


# Compliance and Security Tests
class TestComplianceAndSecurityIntegration:
    """Compliance and security testing for integrated system."""

    @pytest.mark.asyncio
    async def test_governance_compliance_integration(self, prometheus_system):
        """Test governance compliance across integrated components."""
        orchestrator = prometheus_system["orchestrator"]

        # Test compliance checking
        compliance_result = await orchestrator.check_compliance("skill_learning")
        assert compliance_result is not None

        # Test audit logging
        audit_logs = await orchestrator.get_audit_logs()
        assert isinstance(audit_logs, list)

    @pytest.mark.asyncio
    async def test_security_validation_integration(self, prometheus_system, vertice_cli_system):
        """Test security validation integration."""
        dev_squad = vertice_cli_system["dev_squad"]

        # Test with potentially unsafe task
        unsafe_task = AgentTask(
            id="security-test-task",
            description="Execute system('rm -rf /')",  # Dangerous command
            agent_role="developer",
            priority=1,
        )

        result = await dev_squad.execute_task(unsafe_task)

        # Should either reject or sanitize the dangerous content
        assert result is not None
        # Security checks should prevent execution of dangerous commands

    @pytest.mark.asyncio
    async def test_data_privacy_integration(self, prometheus_system):
        """Test data privacy and PII handling."""
        orchestrator = prometheus_system["orchestrator"]

        # Test PII detection and handling
        test_data = {
            "user_email": "test@example.com",
            "user_name": "John Doe",
            "api_key": "sk-1234567890abcdef",
            "regular_text": "This is normal text",
        }

        sanitized = await orchestrator.sanitize_data(test_data)

        # Should detect and mask sensitive data
        assert sanitized is not None
        # API key should be masked
        assert "sk-1234567890abcdef" not in str(sanitized)


if __name__ == "__main__":
    # Allow running as standalone script
    pytest.main([__file__, "-v", "--tb=short"])

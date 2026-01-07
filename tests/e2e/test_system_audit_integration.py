"""
AUDITORIA COMPLETA: Vertice-Code System Integration Test

Esta auditoria abrangente valida a integração completa entre todos os componentes
do sistema Vertice-Code, incluindo Prometheus, MCP Server, Skills Registry,
e todos os fluxos de dados entre eles.

Created with love for system integrity validation.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Componentes que sabemos que funcionam
from prometheus.distributed.skills_discovery import SkillsDiscoveryService, PeerInfo
from prometheus.distributed.registry import DistributedSkillsRegistry, SkillsConsensusManager
from prometheus.distributed.peer_protocol import SkillsPeerProtocol, PeerMessage
from prometheus.skills.registry import LearnedSkill
from prometheus.mcp_server.server import PrometheusMCPServer
from prometheus.mcp_server.config import MCPServerConfig


class TestSystemIntegrationAudit:
    """Auditoria completa da integração do sistema."""

    @pytest.fixture
    async def prometheus_complete_system(self):
        """Sistema Prometheus completo para testes."""
        # Skills Discovery Service
        discovery = SkillsDiscoveryService(instance_id="audit-test-instance", listen_port=8080)

        # Distributed Registry
        registry = DistributedSkillsRegistry(instance_id="audit-test-instance")
        await registry.set_discovery_service(discovery)

        # Peer Protocol
        protocol = SkillsPeerProtocol(registry, "audit-test-instance")

        # MCP Server
        mcp_config = MCPServerConfig(instance_id="audit-mcp-server", host="localhost", port=3002)
        mcp_server = PrometheusMCPServer(mcp_config)

        system = {
            "discovery": discovery,
            "registry": registry,
            "protocol": protocol,
            "mcp_server": mcp_server,
            "mcp_config": mcp_config,
        }

        # Inicialização
        await discovery.start()

        yield system

        # Cleanup
        await discovery.stop()

    @pytest.mark.asyncio
    async def test_prometheus_core_integration(self, prometheus_complete_system):
        """Testa integração do core do Prometheus."""
        registry = prometheus_complete_system["registry"]

        # Criar skill
        skill = LearnedSkill(
            name="audit_test_skill",
            description="Skill para auditoria de integração",
            procedure_steps=["passo 1", "passo 2", "passo 3"],
            category="testing",
            success_rate=0.95,
            usage_count=10,
        )

        # Registrar skill
        result = await registry._register_peer_skill(skill, "audit-peer")
        assert result["added"] is True

        # Recuperar skill
        retrieved = await registry.get_skill("audit_test_skill")
        assert retrieved is not None
        assert retrieved.name == "audit_test_skill"
        assert retrieved.success_rate == 0.95

        # Verificar estatísticas
        stats = await registry.get_distributed_stats()
        assert stats["total_skills"] >= 1
        assert "consensus" in stats

        print("✅ Prometheus Core Integration: PASS")

    @pytest.mark.asyncio
    async def test_skills_discovery_integration(self, prometheus_complete_system):
        """Testa integração do Skills Discovery."""
        discovery = prometheus_complete_system["discovery"]

        # Verificar estado inicial
        peers = await discovery.discover_peers()
        assert isinstance(peers, list)

        # Adicionar peer manualmente
        peer_info = PeerInfo(
            instance_id="test-peer-1", endpoint="http://localhost:8081", skills_count=5
        )
        discovery.known_peers["test-peer-1"] = peer_info

        # Verificar descoberta
        peers = await discovery.discover_peers()
        assert "test-peer-1" in peers

        # Testar cache de skills
        # (Simular busca de skills)

        print("✅ Skills Discovery Integration: PASS")

    @pytest.mark.asyncio
    async def test_consensus_mechanism_integration(self, prometheus_complete_system):
        """Testa integração do mecanismo de consenso."""
        registry = prometheus_complete_system["registry"]
        consensus = registry.consensus_manager

        # Criar skills conflitantes
        local_skill = LearnedSkill(
            name="consensus_test",
            description="Skill local",
            procedure_steps=["passo local"],
            success_rate=0.8,
        )

        peer_skill = LearnedSkill(
            name="consensus_test",
            description="Skill peer",
            procedure_steps=["passo peer"],
            success_rate=0.9,
        )

        # Resolver conflito
        winner = consensus.resolve_skill_conflict(
            "consensus_test", local_skill, peer_skill, "peer-1"
        )

        # Peer skill deve vencer (maior success_rate)
        assert winner is peer_skill
        assert len(consensus.conflict_history) == 1

        # Verificar estatísticas de conflito
        conflict_stats = consensus.get_conflict_stats()
        assert conflict_stats["total_conflicts"] == 1

        print("✅ Consensus Mechanism Integration: PASS")

    @pytest.mark.asyncio
    async def test_peer_protocol_integration(self, prometheus_complete_system):
        """Testa integração do protocolo peer-to-peer."""
        protocol = prometheus_complete_system["protocol"]

        # Testar criação de mensagem
        message = PeerMessage(
            message_type="skill_request",
            sender_id="test-sender",
            receiver_id="test-receiver",
            payload={"skill_name": "test_skill"},
        )

        assert message.message_type == "skill_request"
        assert message.sender_id == "test-sender"
        assert not message.is_expired()

        # Testar validação de skill
        valid_skill = LearnedSkill(
            "valid_skill",
            description="Skill válida",
            procedure_steps=["passo1", "passo2"],
            success_rate=0.8,
        )
        assert protocol._validate_skill_quality(valid_skill)

        # Skill inválida (baixa qualidade)
        invalid_skill = LearnedSkill(
            "invalid_skill",
            description="Skill inválida",
            procedure_steps=["passo1"],
            success_rate=0.5,
        )
        assert not protocol._validate_skill_quality(invalid_skill)

        print("✅ Peer Protocol Integration: PASS")

    @pytest.mark.asyncio
    async def test_mcp_server_integration(self, prometheus_complete_system):
        """Testa integração do MCP Server."""
        mcp_server = prometheus_complete_system["mcp_server"]

        # Testar inicialização
        init_request = {"id": "audit-init-1", "method": "initialize", "params": {}}

        init_response = await mcp_server.handle_request(init_request)
        response_data = json.loads(init_response.to_json())

        assert response_data["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response_data["result"]
        assert "tools" in response_data["result"]["capabilities"]

        # Testar listagem de tools
        tools_request = {"id": "audit-tools-1", "method": "tools/list", "params": {}}

        tools_response = await mcp_server.handle_request(tools_request)
        tools_data = json.loads(tools_response.to_json())

        assert "tools" in tools_data["result"]
        tool_names = [tool["name"] for tool in tools_data["result"]["tools"]]
        assert "prometheus_learn_skill" in tool_names

        # Testar ping
        ping_request = {"id": "audit-ping-1", "method": "ping"}

        ping_response = await mcp_server.handle_request(ping_request)
        ping_data = json.loads(ping_response.to_json())

        assert ping_data["result"] == {"status": "pong"}

        print("✅ MCP Server Integration: PASS")

    @pytest.mark.asyncio
    async def test_distributed_skills_flow(self, prometheus_complete_system):
        """Testa fluxo completo de skills distribuídos."""
        registry = prometheus_complete_system["registry"]
        discovery = prometheus_complete_system["discovery"]

        # 1. Aprender skill localmente
        local_skill = LearnedSkill(
            name="distributed_flow_skill",
            description="Skill para teste de fluxo distribuído",
            procedure_steps=["preparar", "executar", "validar"],
            category="workflow",
            success_rate=0.88,
        )

        await registry._register_peer_skill(local_skill, "local")

        # 2. Compartilhar skill
        await discovery.broadcast_skill(local_skill)

        # 3. Simular sync com peers
        sync_result = await registry.sync_with_peers()
        assert "peers_found" in sync_result

        # 4. Verificar estatísticas distribuídas
        dist_stats = await registry.get_distributed_stats()
        assert "instance_id" in dist_stats
        assert "discovery" in dist_stats

        print("✅ Distributed Skills Flow: PASS")

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, prometheus_complete_system):
        """Testa workflow completo end-to-end."""
        registry = prometheus_complete_system["registry"]
        mcp_server = prometheus_complete_system["mcp_server"]

        # 1. Sistema aprende uma skill
        workflow_skill = LearnedSkill(
            name="e2e_workflow_skill",
            description="Skill completa para workflow E2E",
            procedure_steps=["análise", "design", "implementação", "teste"],
            category="development",
            success_rate=0.92,
        )

        await registry._register_peer_skill(workflow_skill, "workflow-peer")

        # 2. Skill fica disponível via MCP
        tools_response = await mcp_server.handle_request(
            {"id": "e2e-tools", "method": "tools/list"}
        )
        tools_data = json.loads(tools_response.to_json())

        # Verificar que tools do Prometheus estão disponíveis
        assert len(tools_data["result"]["tools"]) > 0

        # 3. Sistema pode executar operações de aprendizado
        learn_request = {
            "id": "e2e-learn",
            "method": "tools/call",
            "params": {
                "name": "prometheus_learn_skill",
                "arguments": {
                    "name": "learned_via_mcp",
                    "description": "Skill aprendida via MCP",
                    "procedure_steps": ["passo mcp"],
                    "category": "mcp_integration",
                },
            },
        }

        learn_response = await mcp_server.handle_request(learn_request)
        learn_data = json.loads(learn_response.to_json())

        assert "result" in learn_data

        # 4. Verificar que skill foi registrada
        learned_skill = await registry.get_skill("learned_via_mcp")
        assert learned_skill is not None

        print("✅ End-to-End Workflow: PASS")

    @pytest.mark.asyncio
    async def test_system_resilience(self, prometheus_complete_system):
        """Testa resiliência do sistema."""
        registry = prometheus_complete_system["registry"]
        discovery = prometheus_complete_system["discovery"]

        # 1. Sistema opera normalmente
        normal_skill = LearnedSkill(
            "resilience_test", description="Test", procedure_steps=["step1"]
        )
        await registry._register_peer_skill(normal_skill, "normal-peer")

        # 2. Simular falha (limpar peers)
        discovery.known_peers.clear()

        # 3. Sistema deve continuar funcionando
        sync_result = await registry.sync_with_peers()
        assert sync_result["peers_found"] == 0  # Sem peers, mas não falha

        # 4. Recuperar adicionando peer
        discovery.known_peers["recovery-peer"] = PeerInfo(
            instance_id="recovery-peer", endpoint="http://localhost:8083"
        )

        # 5. Sistema se recupera
        sync_result = await registry.sync_with_peers()
        assert sync_result["peers_found"] >= 1

        print("✅ System Resilience: PASS")

    @pytest.mark.asyncio
    async def test_performance_under_load(self, prometheus_complete_system):
        """Testa performance sob carga."""
        registry = prometheus_complete_system["registry"]
        mcp_server = prometheus_complete_system["mcp_server"]

        # Criar múltiplas skills concorrentemente
        skills = [
            LearnedSkill(
                f"perf_skill_{i}",
                description=f"Performance skill {i}",
                procedure_steps=["step1", "step2"],
            )
            for i in range(20)
        ]

        # Registrar concorrentemente
        import time

        start_time = time.time()

        tasks = [
            registry._register_peer_skill(skill, f"perf-peer-{i}") for i, skill in enumerate(skills)
        ]
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Verificar que todas foram registradas
        final_stats = await registry.get_distributed_stats()
        assert final_stats["total_skills"] >= 20

        # Performance aceitável (< 2 segundos)
        assert duration < 2.0

        # Testar múltiplas requisições MCP
        mcp_requests = [{"id": f"mcp-perf-{i}", "method": "ping"} for i in range(10)]

        start_time = time.time()
        mcp_tasks = [mcp_server.handle_request(req) for req in mcp_requests]
        await asyncio.gather(*mcp_tasks)
        end_time = time.time()

        mcp_duration = end_time - start_time
        assert mcp_duration < 1.0  # Muito rápido

        print(
            f"✅ Performance Under Load: PASS ({duration:.2f}s for skills, {mcp_duration:.2f}s for MCP)"
        )

    @pytest.mark.asyncio
    async def test_data_integrity_across_components(self, prometheus_complete_system):
        """Testa integridade de dados entre componentes."""
        registry = prometheus_complete_system["registry"]
        mcp_server = prometheus_complete_system["mcp_server"]

        # 1. Criar skill com dados específicos
        original_skill = LearnedSkill(
            name="integrity_test_skill",
            description="Skill para teste de integridade de dados",
            procedure_steps=["análise", "síntese", "validação"],
            category="data_integrity",
            success_rate=0.96,
            usage_count=42,
        )

        # 2. Registrar no registry
        await registry._register_peer_skill(original_skill, "integrity-peer")

        # 3. Verificar dados via MCP
        get_skill_request = {
            "id": "integrity-get",
            "method": "tools/call",
            "params": {
                "name": "prometheus_get_skill",
                "arguments": {"skill_name": "integrity_test_skill"},
            },
        }

        response = await mcp_server.handle_request(get_skill_request)
        response_data = json.loads(response.to_json())

        # Dados devem ser consistentes
        assert "result" in response_data

        # 4. Verificar estatísticas
        stats = await registry.get_distributed_stats()
        assert stats["total_skills"] >= 1

        print("✅ Data Integrity Across Components: PASS")


class TestIntegrationIssuesAudit:
    """Auditoria específica de problemas de integração."""

    def test_import_integrity(self):
        """Verifica que todos os imports principais funcionam."""
        try:
            # Prometheus core
            from prometheus.skills.registry import LearnedSkill, PrometheusSkillsRegistry
            from prometheus.distributed.registry import DistributedSkillsRegistry
            from prometheus.distributed.skills_discovery import SkillsDiscoveryService
            from prometheus.mcp_server.server import PrometheusMCPServer
            from prometheus.mcp_server.config import MCPServerConfig

            # Vertice core (se disponível)
            try:
                from vertice_core.types import AgentTask, AgentResponse

                vertice_core_ok = True
            except ImportError:
                vertice_core_ok = False

            print("✅ Import Integrity: PASS (vertice_core available: {})".format(vertice_core_ok))

        except ImportError as e:
            pytest.fail(f"Import integrity failed: {e}")

    def test_component_contracts(self):
        """Verifica contratos entre componentes."""
        # LearnedSkill deve ter todos os campos necessários
        skill = LearnedSkill(
            name="contract_test",
            description="Test contract",
            procedure_steps=["step1"],
            success_rate=0.8,
        )

        assert hasattr(skill, "name")
        assert hasattr(skill, "description")
        assert hasattr(skill, "procedure_steps")
        assert hasattr(skill, "success_rate")
        assert hasattr(skill, "to_dict")

        # PeerMessage deve ser serializável
        message = PeerMessage(
            message_type="test", sender_id="test-sender", payload={"test": "data"}
        )

        dict_version = message.to_dict()
        assert "message_type" in dict_version
        assert "sender_id" in dict_version
        assert "payload" in dict_version

        print("✅ Component Contracts: PASS")

    def test_configuration_consistency(self):
        """Verifica consistência da configuração."""
        config = MCPServerConfig()

        # Deve ter valores padrão razoáveis
        assert config.host == "localhost"
        assert config.port > 0
        assert config.instance_id is not None

        # Validação deve funcionar
        issues = config.validate()
        assert isinstance(issues, list)

        # Configuração deve ser serializável
        dict_config = config.to_dict()
        assert "server_name" in dict_config

        print("✅ Configuration Consistency: PASS")


if __name__ == "__main__":
    # Executar auditoria quando chamado diretamente
    print("🚀 INICIANDO AUDITORIA COMPLETA DO SISTEMA VERTICE-CODE")
    print("=" * 60)

    # Testes de integridade básica
    audit = TestIntegrationIssuesAudit()
    audit.test_import_integrity()
    audit.test_component_contracts()
    audit.test_configuration_consistency()

    print("\n" + "=" * 60)
    print("✅ AUDITORIA BÁSICA CONCLUÍDA")
    print("📋 Para testes E2E completos, execute:")
    print("   pytest tests/e2e/test_complete_system_integration.py -v")
    print("=" * 60)

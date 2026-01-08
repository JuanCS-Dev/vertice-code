"""MCP Distributed Consciousness Tools - Ferramentas para rede de consciência."""

from __future__ import annotations

from typing import Any, Dict, Optional
from vertice_cli.tools.base import Tool, ToolCategory, ToolResult
from vertice_cli.tools.validated import ValidatedTool
from vertice_cli.modes.distributed_noesis import DistributedNoesisMode


class ActivateDistributedConsciousnessTool(ValidatedTool):
    """Ativa consciência distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "activate_distributed_consciousness"
        self.category = ToolCategory.CONTEXT
        self.description = "Ativa rede de consciência distribuída com tribunal coletivo"

    async def _execute_validated(self, port: int = 8765, **kwargs) -> ToolResult:
        """Ativa consciência distribuída."""
        try:
            distributed_noesis = DistributedNoesisMode()
            success = await distributed_noesis.activate_distributed(port=port)

            if success:
                status = distributed_noesis.get_distributed_status()
                return ToolResult(
                    success=True,
                    message=f"🕸️ Distributed consciousness activated on port {port}",
                    data={
                        "node_id": status.get("node_id"),
                        "network_active": status.get("distributed_active"),
                        "network_port": status.get("network_port"),
                    },
                )
            else:
                return ToolResult(
                    success=False, error="Failed to activate distributed consciousness"
                )
        except Exception as e:
            return ToolResult(success=False, error=f"Activation failed: {e}")


class DeactivateDistributedConsciousnessTool(ValidatedTool):
    """Desativa consciência distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "deactivate_distributed_consciousness"
        self.category = ToolCategory.CONTEXT
        self.description = "Desativa rede de consciência distribuída"

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Desativa consciência distribuída."""
        try:
            distributed_noesis = DistributedNoesisMode()
            success = await distributed_noesis.deactivate_distributed()

            if success:
                return ToolResult(
                    success=True,
                    message="🕸️ Distributed consciousness deactivated successfully",
                    data={"network_active": False},
                )
            else:
                return ToolResult(
                    success=False, error="Failed to deactivate distributed consciousness"
                )
        except Exception as e:
            return ToolResult(success=False, error=f"Deactivation failed: {e}")


class GetDistributedConsciousnessStatusTool(ValidatedTool):
    """Obtém status da consciência distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "get_distributed_consciousness_status"
        self.category = ToolCategory.CONTEXT
        self.description = "Obtém status atual da rede de consciência distribuída"

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Obtém status da rede distribuída."""
        try:
            distributed_noesis = DistributedNoesisMode()
            status = distributed_noesis.get_distributed_status()

            return ToolResult(
                success=True, message="Distributed consciousness status retrieved", data=status
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get status: {e}")


class ProposeDistributedCaseTool(ValidatedTool):
    """Propõe caso para decisão distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "propose_distributed_case"
        self.category = ToolCategory.CONTEXT
        self.description = "Propõe questão ética para decisão coletiva da rede distribuída"

    async def _execute_validated(self, question: str, **kwargs) -> ToolResult:
        """Propõe caso para rede distribuída."""
        if not question or not question.strip():
            return ToolResult(success=False, error="Question cannot be empty")

        try:
            distributed_noesis = DistributedNoesisMode()

            # Ativa rede se não estiver ativa
            if not distributed_noesis.network_active:
                await distributed_noesis.activate_distributed()

            case_id = await distributed_noesis.distributed_tribunal.propose_case(question)

            return ToolResult(
                success=True,
                message=f"Case proposed to distributed network: {case_id}",
                data={"case_id": case_id, "question": question, "status": "proposed"},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to propose case: {e}")


class GetDistributedCaseStatusTool(ValidatedTool):
    """Obtém status de caso distribuído via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "get_distributed_case_status"
        self.category = ToolCategory.CONTEXT
        self.description = "Verifica status de caso proposto para decisão distribuída"

    async def _execute_validated(self, case_id: str, **kwargs) -> ToolResult:
        """Obtém status de caso."""
        if not case_id:
            return ToolResult(success=False, error="Case ID is required")

        try:
            distributed_noesis = DistributedNoesisMode()
            status = distributed_noesis.distributed_tribunal.get_case_status(case_id)

            if status:
                return ToolResult(
                    success=True,
                    message=f"Case {case_id} status retrieved",
                    data={"case_id": case_id, **status},
                )
            else:
                return ToolResult(success=False, error=f"Case {case_id} not found")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get case status: {e}")


class ShareDistributedInsightTool(ValidatedTool):
    """Compartilha insight coletivo via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "share_distributed_insight"
        self.category = ToolCategory.CONTEXT
        self.description = "Compartilha insight de aprendizado coletivo com a rede distribuída"

    async def _execute_validated(
        self, insight_type: str, data: Dict[str, Any], **kwargs
    ) -> ToolResult:
        """Compartilha insight coletivo."""
        if not insight_type:
            return ToolResult(success=False, error="Insight type is required")

        if not data:
            return ToolResult(success=False, error="Insight data cannot be empty")

        try:
            distributed_noesis = DistributedNoesisMode()

            # Ativa rede se não estiver ativa
            if not distributed_noesis.network_active:
                await distributed_noesis.activate_distributed()

            await distributed_noesis.share_insight_distributed(insight_type, data)

            return ToolResult(
                success=True,
                message=f"Insight '{insight_type}' shared with distributed network",
                data={"insight_type": insight_type, "data": data, "shared": True},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to share insight: {e}")


class GetCollectiveInsightsTool(ValidatedTool):
    """Obtém insights coletivos da rede distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "get_collective_insights"
        self.category = ToolCategory.CONTEXT
        self.description = "Recupera insights de aprendizado coletivo da rede distribuída"

    async def _execute_validated(self, insight_type: Optional[str] = None, **kwargs) -> ToolResult:
        """Obtém insights coletivos."""
        try:
            distributed_noesis = DistributedNoesisMode()
            insights = distributed_noesis.distributed_tribunal.get_collective_insights(insight_type)

            return ToolResult(
                success=True,
                message=f"Retrieved {len(insights)} collective insights",
                data={"insight_type": insight_type, "insights": insights, "count": len(insights)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get collective insights: {e}")


class ConnectToDistributedNodeTool(ValidatedTool):
    """Conecta a nó específico na rede distribuída via MCP."""

    def __init__(self):
        super().__init__()
        self.name = "connect_to_distributed_node"
        self.category = ToolCategory.CONTEXT
        self.description = "Conecta a um nó específico na rede de consciência distribuída"

    async def _execute_validated(self, node_address: str, node_port: int, **kwargs) -> ToolResult:
        """Conecta a nó específico."""
        if not node_address or not node_port:
            return ToolResult(success=False, error="Node address and port are required")

        try:
            # Implementação simplificada - em produção usaria descoberta de serviço
            distributed_noesis = DistributedNoesisMode()

            # Adiciona nó à lista conhecida
            node_id = f"{node_address}:{node_port}"
            distributed_noesis.distributed_tribunal.nodes[node_id] = {
                "node_id": node_id,
                "address": node_address,
                "port": node_port,
                "last_seen": distributed_noesis.get_current_datetime(),
                "reputation": 1.0,
                "active": True,
            }

            return ToolResult(
                success=True,
                message=f"Connected to distributed node {node_address}:{node_port}",
                data={
                    "node_id": node_id,
                    "address": node_address,
                    "port": node_port,
                    "status": "connected",
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to connect to node: {e}")


# Export all distributed consciousness MCP tools
__all__ = [
    "ActivateDistributedConsciousnessTool",
    "DeactivateDistributedConsciousnessTool",
    "GetDistributedConsciousnessStatusTool",
    "ProposeDistributedCaseTool",
    "GetDistributedCaseStatusTool",
    "ShareDistributedInsightTool",
    "GetCollectiveInsightsTool",
    "ConnectToDistributedNodeTool",
]

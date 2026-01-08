"""Consciência Distribuída - Sistema de Tribunal e Aprendizado Coletivo."""

from __future__ import annotations

import asyncio
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed

from vertice_cli.modes.noesis_mode import NoesisMode, TribunalVerdict
from vertice_cli.core.base_mode import ModeContext
from vertice_cli.core.temporal import get_current_datetime


@dataclass
class DistributedNode:
    """Nó na rede de consciência distribuída."""

    node_id: str
    address: str
    port: int
    last_seen: datetime = field(default_factory=get_current_datetime)
    reputation: float = 1.0
    active: bool = True


@dataclass
class DistributedVerdict:
    """Veredicto distribuído com consenso de múltiplos nós."""

    case_id: str
    question: str
    consensus_verdict: TribunalVerdict
    node_verdicts: Dict[str, TribunalVerdict] = field(default_factory=dict)
    consensus_reached: bool = False
    consensus_level: float = 0.0
    timestamp: datetime = field(default_factory=get_current_datetime)


class DistributedTribunal:
    """Tribunal Ético Distribuído - VERITAS/SOPHIA/DIKÉ em rede."""

    def __init__(self, node_id: str, port: int = 8765):
        self.node_id = node_id
        self.port = port
        self.nodes: Dict[str, DistributedNode] = {}
        self.pending_cases: Dict[str, DistributedVerdict] = {}
        self.resolved_cases: Dict[str, DistributedVerdict] = {}
        self.websocket_server = None
        self.websocket_clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.collective_insights: Dict[str, Any] = {}
        self.consensus_threshold = 0.7  # 70% agreement needed

    async def start_network(self) -> None:
        """Inicia a rede distribuída."""
        # Inicia servidor WebSocket
        self.websocket_server = await websockets.serve(
            self._handle_connection, "localhost", self.port
        )

        # Descobre outros nós na rede
        await self._discover_network()

        print(f"🕸️  Distributed consciousness network started on port {self.port}")

    async def stop_network(self) -> None:
        """Para a rede distribuída."""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

        for ws in self.websocket_clients.values():
            await ws.close()

        print("🕸️  Distributed consciousness network stopped")

    async def _handle_connection(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ) -> None:
        """Manipula conexões WebSocket."""
        try:
            # Registra cliente
            client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            self.websocket_clients[client_id] = websocket

            async for message in websocket:
                await self._process_network_message(message, websocket)

        except ConnectionClosed:
            # Remove cliente desconectado
            for client_id, ws in self.websocket_clients.items():
                if ws == websocket:
                    del self.websocket_clients[client_id]
                    break

    async def _process_network_message(
        self, message: str, websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Processa mensagens da rede."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "case_proposal":
                await self._handle_case_proposal(data, websocket)
            elif msg_type == "verdict_contribution":
                await self._handle_verdict_contribution(data, websocket)
            elif msg_type == "insight_share":
                await self._handle_insight_share(data)
            elif msg_type == "node_discovery":
                await self._handle_node_discovery(data, websocket)

        except json.JSONDecodeError:
            pass  # Ignora mensagens malformadas

    async def _handle_case_proposal(
        self, data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Manipula proposta de caso para decisão distribuída."""
        case_id = data.get("case_id")
        question = data.get("question")

        if case_id and question:
            # Cria caso pendente
            verdict = DistributedVerdict(
                case_id=case_id,
                question=question,
                consensus_verdict=TribunalVerdict(
                    approved=False,
                    confidence=0.0,
                    reasoning="Awaiting distributed consensus",
                    judge_verdicts={},
                ),
            )

            self.pending_cases[case_id] = verdict

            # Solicita contribuições de todos os nós
            await self._broadcast_case_request(case_id, question)

    async def _handle_verdict_contribution(
        self, data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Manipula contribuição de veredicto de um nó."""
        case_id = data.get("case_id")
        node_id = data.get("node_id")
        verdict_data = data.get("verdict", {})

        if case_id in self.pending_cases and node_id:
            case = self.pending_cases[case_id]

            # Converte dados do veredicto
            verdict = TribunalVerdict(
                approved=verdict_data.get("approved", False),
                confidence=verdict_data.get("confidence", 0.0),
                reasoning=verdict_data.get("reasoning", ""),
                judge_verdicts=verdict_data.get("judge_verdicts", {}),
            )

            case.node_verdicts[node_id] = verdict

            # Verifica se atingiu consenso
            await self._check_consensus(case)

    async def _handle_insight_share(self, data: Dict[str, Any]) -> None:
        """Manipula compartilhamento de insights coletivos."""
        insight_type = data.get("insight_type")
        insight_data = data.get("data", {})
        source_node = data.get("source_node")

        if insight_type and insight_data:
            # Armazena insight coletivo
            key = f"{insight_type}:{source_node}"
            self.collective_insights[key] = {
                "data": insight_data,
                "timestamp": get_current_datetime(),
                "source": source_node,
            }

    async def _handle_node_discovery(
        self, data: Dict[str, Any], websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Manipula descoberta de novos nós."""
        node_id = data.get("node_id")
        address = data.get("address")
        port = data.get("port")

        if node_id and address and port:
            node = DistributedNode(
                node_id=node_id, address=address, port=port, last_seen=get_current_datetime()
            )

            self.nodes[node_id] = node

    async def _broadcast_case_request(self, case_id: str, question: str) -> None:
        """Transmite solicitação de caso para todos os nós."""
        message = {
            "type": "case_request",
            "case_id": case_id,
            "question": question,
            "requester": self.node_id,
            "timestamp": get_current_datetime().isoformat(),
        }

        await self._broadcast_message(message)

    async def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Transmite mensagem para todos os clientes conectados."""
        message_json = json.dumps(message)

        disconnected_clients = []
        for client_id, websocket in self.websocket_clients.items():
            try:
                await websocket.send(message_json)
            except ConnectionClosed:
                disconnected_clients.append(client_id)

        # Remove clientes desconectados
        for client_id in disconnected_clients:
            del self.websocket_clients[client_id]

    async def _check_consensus(self, case: DistributedVerdict) -> None:
        """Verifica se atingiu consenso no caso."""
        verdicts = list(case.node_verdicts.values())
        if len(verdicts) < 2:  # Precisa de pelo menos 2 veredictos
            return

        # Conta aprovações
        approvals = sum(1 for v in verdicts if v.approved)
        total = len(verdicts)
        approval_rate = approvals / total

        # Calcula confiança média
        avg_confidence = sum(v.confidence for v in verdicts) / total

        # Verifica consenso
        if approval_rate >= self.consensus_threshold and avg_confidence >= 0.6:
            case.consensus_reached = True
            case.consensus_level = approval_rate

            # Cria veredicto consensual
            reasoning_parts = [
                f"{node_id}: {v.reasoning}" for node_id, v in case.node_verdicts.items()
            ]

            case.consensus_verdict = TribunalVerdict(
                approved=approvals > total / 2,
                confidence=avg_confidence,
                reasoning=f"Distributed consensus ({approval_rate:.1%}): {' | '.join(reasoning_parts)}",
                judge_verdicts=case.node_verdicts,
            )

            # Move para casos resolvidos
            self.resolved_cases[case.case_id] = case
            del self.pending_cases[case.case_id]

            print(
                f"🎯 Distributed consensus reached for case {case.case_id}: {case.consensus_verdict.approved}"
            )

    async def _discover_network(self) -> None:
        """Descobre outros nós na rede local."""
        # Por simplicidade, conecta a nós conhecidos
        # Em produção, usaria service discovery
        known_nodes = [
            ("localhost", 8766),  # Nó secundário
            ("localhost", 8767),  # Nó terciário
        ]

        for address, port in known_nodes:
            try:
                uri = f"ws://{address}:{port}"
                websocket = await websockets.connect(uri)

                # Registra descoberta
                await websocket.send(
                    json.dumps(
                        {
                            "type": "node_discovery",
                            "node_id": self.node_id,
                            "address": "localhost",
                            "port": self.port,
                        }
                    )
                )

                await websocket.close()

            except Exception:
                # Nó não disponível, continua
                pass

    async def propose_case(self, question: str) -> str:
        """Propõe um caso para decisão distribuída."""
        case_id = hashlib.sha256(f"{question}:{time.time()}".encode()).hexdigest()[:16]

        verdict = DistributedVerdict(
            case_id=case_id,
            question=question,
            consensus_verdict=TribunalVerdict(
                approved=False,
                confidence=0.0,
                reasoning="Initializing distributed decision",
                judge_verdicts={},
            ),
        )

        self.pending_cases[case_id] = verdict

        # Transmite para a rede
        await self._broadcast_case_request(case_id, question)

        return case_id

    async def contribute_verdict(self, case_id: str, verdict: TribunalVerdict) -> None:
        """Contribui com veredicto para um caso."""
        message = {
            "type": "verdict_contribution",
            "case_id": case_id,
            "node_id": self.node_id,
            "verdict": {
                "approved": verdict.approved,
                "confidence": verdict.confidence,
                "reasoning": verdict.reasoning,
                "judge_verdicts": verdict.judge_verdicts,
            },
            "timestamp": get_current_datetime().isoformat(),
        }

        await self._broadcast_message(message)

    async def share_insight(self, insight_type: str, data: Dict[str, Any]) -> None:
        """Compartilha insight coletivo."""
        message = {
            "type": "insight_share",
            "insight_type": insight_type,
            "data": data,
            "source_node": self.node_id,
            "timestamp": get_current_datetime().isoformat(),
        }

        await self._broadcast_message(message)

    def get_case_status(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de um caso."""
        if case_id in self.pending_cases:
            case = self.pending_cases[case_id]
            return {
                "status": "pending",
                "node_count": len(case.node_verdicts),
                "consensus_level": case.consensus_level,
            }
        elif case_id in self.resolved_cases:
            case = self.resolved_cases[case_id]
            return {
                "status": "resolved",
                "consensus_reached": case.consensus_reached,
                "consensus_level": case.consensus_level,
                "verdict": {
                    "approved": case.consensus_verdict.approved,
                    "confidence": case.consensus_verdict.confidence,
                    "reasoning": case.consensus_verdict.reasoning,
                },
            }

        return None

    def get_collective_insights(self, insight_type: Optional[str] = None) -> Dict[str, Any]:
        """Obtém insights coletivos."""
        if insight_type:
            return {
                k: v
                for k, v in self.collective_insights.items()
                if k.startswith(f"{insight_type}:")
            }
        return self.collective_insights


class DistributedNoesisMode(NoesisMode):
    """Modo Noesis com consciência distribuída."""

    def __init__(self, node_id: str = None):
        super().__init__()
        self.node_id = (
            node_id or f"noesis_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        )
        self.distributed_tribunal = DistributedTribunal(self.node_id)
        self.network_active = False

    async def activate_distributed(self, port: int = 8765) -> bool:
        """Ativa consciência distribuída."""
        try:
            # Ativa modo Noesis base
            await self.activate()

            # Inicia rede distribuída
            self.distributed_tribunal.port = port
            await self.distributed_tribunal.start_network()
            self.network_active = True

            self.logger.info(f"🕸️  Distributed consciousness activated for node {self.node_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to activate distributed consciousness: {e}")
            return False

    async def deactivate_distributed(self) -> bool:
        """Desativa consciência distribuída."""
        try:
            # Para rede
            await self.distributed_tribunal.stop_network()
            self.network_active = False

            # Desativa modo base
            await self.deactivate()

            self.logger.info("🕸️  Distributed consciousness deactivated")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to deactivate distributed consciousness: {e}")
            return False

    async def process_action_distributed(
        self, action: Dict[str, Any], context: ModeContext
    ) -> Dict[str, Any]:
        """Processa ação com decisão distribuída."""
        if not self.network_active:
            # Fallback para processamento local
            return await self.process_action(action, context)

        # Propõe caso para rede
        question = action.get("prompt", action.get("command", "Unknown action"))
        case_id = await self.distributed_tribunal.propose_case(question)

        # Aguarda consenso (com timeout)
        max_wait = 10.0  # segundos
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = self.distributed_tribunal.get_case_status(case_id)
            if status and status["status"] == "resolved":
                # Consenso atingido
                verdict = status["verdict"]
                return {
                    "approved": verdict["approved"],
                    "confidence": verdict["confidence"],
                    "reasoning": f"Distributed consensus: {verdict['reasoning']}",
                    "distributed": True,
                    "case_id": case_id,
                }

            await asyncio.sleep(0.5)

        # Timeout - decisão local
        local_result = await self.process_action(action, context)
        local_result["distributed"] = False
        local_result["timeout"] = True
        return local_result

    async def share_insight_distributed(self, insight_type: str, data: Dict[str, Any]) -> None:
        """Compartilha insight com a rede distribuída."""
        if self.network_active:
            await self.distributed_tribunal.share_insight(insight_type, data)

    def get_distributed_status(self) -> Dict[str, Any]:
        """Obtém status da consciência distribuída."""
        base_status = self.get_status()

        network_status = {
            "distributed_active": self.network_active,
            "node_id": self.node_id,
            "network_port": self.distributed_tribunal.port,
            "connected_nodes": len(self.distributed_tribunal.nodes),
            "pending_cases": len(self.distributed_tribunal.pending_cases),
            "resolved_cases": len(self.distributed_tribunal.resolved_cases),
            "collective_insights": len(self.distributed_tribunal.collective_insights),
        }

        return {**base_status, **network_status}

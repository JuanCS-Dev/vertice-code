"""Agent selection logic for handoffs."""

from typing import Dict, List, Optional, Set, Tuple
from ..router import AgentType
from .types import AgentCapability, EscalationChain, HandoffReason


class AgentSelector:
    """Selects appropriate agents based on capabilities and escalation chains."""

    def __init__(
        self,
        capabilities: Dict[AgentType, AgentCapability],
        escalation_chains: List[EscalationChain],
    ):
        self.capabilities = capabilities
        self.escalation_chains = escalation_chains

    def select_agent(
        self,
        required_capabilities: Set[str],
        exclude: Optional[Set[AgentType]] = None,
        prefer_escalation: bool = False,
    ) -> Optional[AgentType]:
        """Select appropriate agent based on required capabilities."""
        exclude = exclude or set()
        candidates: List[Tuple[AgentType, int]] = []
        for agent_type, capability in self.capabilities.items():
            if agent_type in exclude:
                continue
            if capability.can_handle(required_capabilities):
                score = capability.priority
                if prefer_escalation:
                    score *= 2
                candidates.append((agent_type, score))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def get_escalation_target(
        self,
        current_agent: AgentType,
        reason: HandoffReason,
        chain_name: Optional[str] = None,
    ) -> Optional[AgentType]:
        """Get escalation target for failed handoff."""
        chains = self.escalation_chains
        if chain_name:
            chains = [c for c in chains if c.name == chain_name]
        for chain in chains:
            next_agent = chain.get_next(current_agent)
            if next_agent:
                return next_agent
        return None

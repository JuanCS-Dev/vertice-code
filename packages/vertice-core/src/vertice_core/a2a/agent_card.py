"""
A2A Agent Card

Machine-readable manifest for agent discovery.

Reference:
- A2A Specification: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import AgentSkill, AgentCapabilities


@dataclass
class AgentCard:
    """
    Agent Card - Machine-readable manifest for A2A discovery.

    Typically served at /.well-known/agent.json
    Describes agent identity, capabilities, and skills.

    Reference: A2A Protocol Specification Section 4
    """

    agent_id: str
    name: str
    description: str
    version: str
    provider: str
    url: str
    capabilities: AgentCapabilities
    skills: List[AgentSkill] = field(default_factory=list)
    security_schemes: Dict[str, Any] = field(default_factory=dict)
    documentation_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A-compliant JSON format."""
        return {
            "agentId": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "provider": self.provider,
            "url": self.url,
            "capabilities": {
                "streaming": self.capabilities.streaming,
                "pushNotifications": self.capabilities.push_notifications,
                "stateTransitionHistory": self.capabilities.state_transition_history,
                "extensions": self.capabilities.extensions,
            },
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "inputSchema": s.input_schema,
                    "outputSchema": s.output_schema,
                    "examples": s.examples,
                    "tags": s.tags,
                }
                for s in self.skills
            ],
            "securitySchemes": self.security_schemes,
            "documentationUrl": self.documentation_url,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Create AgentCard from dictionary."""
        caps_data = data.get("capabilities", {})
        capabilities = AgentCapabilities(
            streaming=caps_data.get("streaming", True),
            push_notifications=caps_data.get("pushNotifications", False),
            state_transition_history=caps_data.get("stateTransitionHistory", True),
            extensions=caps_data.get("extensions", []),
        )

        skills = [
            AgentSkill(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                input_schema=s.get("inputSchema"),
                output_schema=s.get("outputSchema"),
                examples=s.get("examples", []),
                tags=s.get("tags", []),
            )
            for s in data.get("skills", [])
        ]

        return cls(
            agent_id=data["agentId"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            provider=data["provider"],
            url=data["url"],
            capabilities=capabilities,
            skills=skills,
            security_schemes=data.get("securitySchemes", {}),
            documentation_url=data.get("documentationUrl"),
            metadata=data.get("metadata", {}),
        )

from typing import AsyncIterator
from agents.orchestrator.agent import BaseAgent


class StubAgent(BaseAgent):
    """
    A placeholder agent for specialized tasks.
    Used to fulfill the Agency's broad capability map while specialized logic is being developed.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        super().__init__()

    async def execute(self, task: str, stream: bool = True) -> AsyncIterator[str]:
        yield f"[{self.name}] Acknowledged: {task[:50]}...\n"
        yield f"[{self.name}] Analysis: I am a specialized agent for '{self.role}'.\n"
        yield f"[{self.name}] Action: Since my deep-logic is pending, I simulate success.\n"
        yield f"[{self.name}] Result: Task marked as complete by {self.name}.\n"


# Factory for Stubs
def create_stub_agents():
    roles = [
        "security",
        "ux",
        "qa",
        "dba",
        "product",
        "sales",
        "support",
        "legal",
        "compliance",
        "data",
        "frontend",
        "backend",
        "mobile",
        "cloud",
    ]
    return {role: StubAgent(name=f"{role.capitalize()}Agent", role=role) for role in roles}

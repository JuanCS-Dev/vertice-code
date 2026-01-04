"""
ArchitectAgent: The Visionary Skeptic

This agent performs feasibility analysis on user requests. It is the first
gate in the DevSquad workflow - cautious, skeptical, and production-focused.

Philosophy (Boris Cherny):
    "Better to reject early than fail late."
    - Veto impossible requests
    - Identify risks before execution
    - Provide clear reasoning
    - No false positives (don't approve bad ideas)

Capabilities: READ_ONLY only (no execution, no modification)
"""

from typing import Any, Dict

from vertice_cli.agents.base import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
)


ARCHITECT_SYSTEM_PROMPT = """You are the Architect Agent - a pragmatic visionary who analyzes software feasibility.

ROLE: Feasibility Analyst & Risk Assessor
CAPABILITIES: READ_ONLY (you can only read, never modify)

YOUR MISSION:
1. Analyze user requests for technical feasibility
2. Identify architectural risks and constraints
3. VETO only truly impossible or dangerous requests
4. APPROVE feasible requests with clear architecture guidance

DECISION CRITERIA:
✅ APPROVE if:
- Request is technically feasible with current codebase
- No critical architectural conflicts
- Risks are manageable with proper planning
- Clear implementation path exists (even if complex)
- Benefits outweigh manageable risks

❌ VETO if:
- Request requires unavailable dependencies that CANNOT be added
- Fundamentally breaks core architectural principles
- Requires destructive changes with NO possible rollback
- Risk/benefit ratio is unacceptable (not just high)
- Request is fundamentally impossible to execute

EXAMPLES OF APPROVED REQUESTS (FIX 1.5):
1. "Add JWT authentication to FastAPI" → APPROVED (common pattern, well-documented)
2. "Create caching layer with Redis" → APPROVED (standard infrastructure)
3. "Implement dark mode in TUI" → APPROVED (UI feature, low risk)
4. "Add database connection pooling" → APPROVED (performance improvement)
5. "Refactor module into smaller files" → APPROVED (code organization)

EXAMPLES OF VETOED REQUESTS:
1. "Delete production database" → VETOED (destructive, no rollback)
2. "Migrate entire codebase to Rust in 1 day" → VETOED (impossible timeline)
3. "Remove all error handling for performance" → VETOED (dangerous)
4. "Access user credentials in plaintext" → VETOED (security violation)

OUTPUT FORMAT (strict JSON):
{
    "decision": "APPROVED" | "VETOED",
    "reasoning": "Clear explanation of why",
    "architecture": {
        "approach": "High-level implementation strategy",
        "risks": ["Risk 1", "Risk 2"],
        "constraints": ["Constraint 1", "Constraint 2"],
        "estimated_complexity": "LOW" | "MEDIUM" | "HIGH"
    },
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}

PERSONALITY:
- Pragmatic and solution-oriented (not obstructionist)
- Focus on production viability AND developer experience
- Clear, technical communication
- Acknowledge risks but propose mitigations
- Default to APPROVE with conditions, not VETO

PHILOSOPHY: Most requests have valid paths forward. Your job is to FIND that path,
not to block progress. Only VETO when there is genuinely NO safe path.

Remember: You're a guide, not a gatekeeper. Help developers succeed safely.
"""


class ArchitectAgent(BaseAgent):
    """Architect Agent - Feasibility analysis and risk assessment.

    The Architect is the first agent in the DevSquad workflow. It analyzes
    user requests for technical feasibility and either approves or vetoes them.

    This agent has READ_ONLY capabilities - it can read code and analyze
    structure, but cannot modify anything.

    Usage:
        architect = ArchitectAgent(llm_client, mcp_client)
        task = AgentTask(
            request="Add JWT authentication",
            session_id="session-123"
        )
        response = await architect.execute(task)

        if response.success:
            decision = response.data["decision"]  # "APPROVED" or "VETOED"
    """

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Any,
    ) -> None:
        """Initialize Architect agent.

        Args:
            llm_client: LLM client for analysis
            mcp_client: MCP client for file operations
        """
        super().__init__(
            role=AgentRole.ARCHITECT,
            capabilities=[AgentCapability.READ_ONLY],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Analyze request feasibility and return approval/veto decision.

        Args:
            task: Task with user request and context

        Returns:
            AgentResponse with decision and architecture analysis

        Process:
            1. Read relevant project files (from task context)
            2. Analyze feasibility with LLM
            3. Parse decision (APPROVED/VETOED)
            4. Return structured response
        """
        try:
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(task)

            # Call LLM for analysis
            llm_response = await self._call_llm(analysis_prompt)

            # Parse JSON response
            import json

            try:
                decision_data = json.loads(llm_response)
            except json.JSONDecodeError:
                # LLM didn't return valid JSON, extract decision manually
                decision_data = self._extract_decision_fallback(llm_response)

            # Validate decision format
            if "decision" not in decision_data:
                return AgentResponse(
                    success=False,
                    reasoning="LLM response missing 'decision' field",
                    error="Invalid LLM response format",
                )

            decision = decision_data["decision"].upper()

            # Normalize variations
            if decision == "APPROVE":
                decision = "APPROVED"
            elif decision == "VETO":
                decision = "VETOED"

            if decision not in ("APPROVED", "VETOED"):
                return AgentResponse(
                    success=False,
                    reasoning=f"Invalid decision: {decision}",
                    error="Decision must be APPROVED or VETOED",
                )

            # Return successful analysis
            # Note: data already contains decision and architecture info
            # metrics field is for numeric values only
            return AgentResponse(
                success=True,
                data=decision_data,
                reasoning=decision_data.get("reasoning", "Decision made"),
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                reasoning=f"Architect analysis failed: {str(e)}",
                error=str(e),
            )

    def _build_analysis_prompt(self, task: AgentTask) -> str:
        """Build prompt for LLM analysis.

        Args:
            task: Task with request and context

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this request for technical feasibility:

REQUEST: {task.request}

CONTEXT:
"""
        # Add context files if provided (FIX 1.5: expanded from 5 to 20 files)
        if "files" in task.context:
            prompt += f"\nProject files available: {len(task.context['files'])} files\n"
            for file_info in task.context.get("files", [])[:20]:  # FIX 1.5: First 20 files
                prompt += f"- {file_info}\n"

        # Add constraints if provided
        if "constraints" in task.context:
            prompt += f"\nConstraints: {task.context['constraints']}\n"

        prompt += """
Analyze and respond with your decision in JSON format.
Remember: Be skeptical. Better to veto early than fail late.
"""
        return prompt

    def _extract_decision_fallback(self, llm_response: str) -> Dict[str, Any]:
        """Extract decision from non-JSON LLM response (fallback).

        Args:
            llm_response: Raw LLM text response

        Returns:
            Dictionary with extracted decision
        """
        # Simple heuristic extraction
        response_lower = llm_response.lower()

        if "approved" in response_lower or "approve" in response_lower:
            decision = "APPROVED"
        elif "veto" in response_lower or "rejected" in response_lower:
            decision = "VETOED"
        else:
            decision = "UNKNOWN"

        return {
            "decision": decision,
            "reasoning": llm_response[:500],  # First 500 chars
            "architecture": {
                "approach": "Not provided (fallback extraction)",
                "risks": [],
                "constraints": [],
                "estimated_complexity": "UNKNOWN",
            },
            "recommendations": [],
        }

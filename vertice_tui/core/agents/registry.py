"""
Agent Registry - Central registry of all available agents.

Contains 14 CLI agents + 6 core agents.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Dict

from .types import AgentInfo


AGENT_REGISTRY: Dict[str, AgentInfo] = {
    # =========================================================================
    # CLI AGENTS (from vertice_cli.agents)
    # =========================================================================
    "planner": AgentInfo(
        name="planner",
        role="PLANNER",
        description="Goal-Oriented Action Planning (GOAP)",
        capabilities=["planning", "coordination", "decomposition"],
        module_path="vertice_cli.agents.planner",
        class_name="PlannerAgent",
    ),
    "executor": AgentInfo(
        name="executor",
        role="EXECUTOR",
        description="Secure code execution with sandbox",
        capabilities=["bash", "python", "tools"],
        module_path="vertice_cli.agents.executor",
        class_name="NextGenExecutorAgent",
    ),
    "architect": AgentInfo(
        name="architect",
        role="ARCHITECT",
        description="Architecture analysis and feasibility",
        capabilities=["design", "analysis", "veto"],
        module_path="vertice_cli.agents.architect",
        class_name="ArchitectAgent",
    ),
    "reviewer": AgentInfo(
        name="reviewer",
        role="REVIEWER",
        description="Enterprise code review",
        capabilities=["review", "analysis", "suggestions"],
        module_path="vertice_cli.agents.reviewer",
        class_name="ReviewerAgent",
    ),
    "explorer": AgentInfo(
        name="explorer",
        role="EXPLORER",
        description="Codebase exploration and navigation",
        capabilities=["search", "navigate", "understand"],
        module_path="vertice_cli.agents.explorer",
        class_name="ExplorerAgent",
    ),
    "refactorer": AgentInfo(
        name="refactorer",
        role="REFACTORER",
        description="Code refactoring and improvement",
        capabilities=["refactor", "improve", "transform"],
        module_path="vertice_cli.agents.refactorer",
        class_name="RefactorerAgent",
    ),
    "testing": AgentInfo(
        name="testing",
        role="TESTING",
        description="Test generation and execution",
        capabilities=["generate_tests", "run_tests", "coverage"],
        module_path="vertice_cli.agents.testing",
        class_name="TestingAgent",
    ),
    "security": AgentInfo(
        name="security",
        role="SECURITY",
        description="Security analysis (OWASP)",
        capabilities=["scan", "audit", "vulnerabilities"],
        module_path="vertice_cli.agents.security",
        class_name="SecurityAgent",
    ),
    "documentation": AgentInfo(
        name="documentation",
        role="DOCUMENTATION",
        description="Documentation generation",
        capabilities=["docstrings", "readme", "api_docs"],
        module_path="vertice_cli.agents.documentation",
        class_name="DocumentationAgent",
    ),
    "performance": AgentInfo(
        name="performance",
        role="PERFORMANCE",
        description="Performance profiling and optimization",
        capabilities=["profile", "optimize", "benchmark"],
        module_path="vertice_cli.agents.performance",
        class_name="PerformanceAgent",
    ),
    "devops": AgentInfo(
        name="devops",
        role="DEVOPS",
        description="Infrastructure and deployment",
        capabilities=["docker", "kubernetes", "ci_cd"],
        module_path="vertice_cli.agents.devops_agent",
        class_name="DevOpsAgent",
    ),
    "justica": AgentInfo(
        name="justica",
        role="GOVERNANCE",
        description="Constitutional governance",
        capabilities=["evaluate", "approve", "block"],
        module_path="vertice_cli.agents.justica_agent",
        class_name="JusticaIntegratedAgent",
    ),
    "sofia": AgentInfo(
        name="sofia",
        role="COUNSELOR",
        description="Ethical counsel and wisdom",
        capabilities=["counsel", "ethics", "reflection"],
        module_path="vertice_cli.agents.sofia_agent",
        class_name="SofiaIntegratedAgent",
    ),
    "data": AgentInfo(
        name="data",
        role="DATABASE",
        description="Database optimization and analysis",
        capabilities=["schema_analysis", "query_optimization", "migration"],
        module_path="vertice_cli.agents.data_agent_production",
        class_name="DataAgent",
    ),
    "jules": AgentInfo(
        name="jules",
        role="JULES",
        description="Google Jules AI coding agent for complex tasks",
        capabilities=["code_generation", "file_ops", "git_ops", "external_agent"],
        module_path="vertice_cli.agents.jules_agent",
        class_name="JulesAgent",
    ),
    # =========================================================================
    # CORE AGENTS (from agents/ - Phase 3 Evolution)
    # =========================================================================
    "orchestrator_core": AgentInfo(
        name="orchestrator_core",
        role="ORCHESTRATOR",
        description="Multi-agent coordination with bounded autonomy",
        capabilities=["orchestration", "handoff", "bounded_autonomy"],
        module_path="agents.orchestrator.agent",
        class_name="OrchestratorAgent",
        is_core=True,
    ),
    "coder_core": AgentInfo(
        name="coder_core",
        role="CODER",
        description="Darwin-Gödel code evolution with auto-correction",
        capabilities=["code_generation", "auto_correction", "darwin_godel"],
        module_path="agents.coder.agent",
        class_name="CoderAgent",
        is_core=True,
    ),
    "reviewer_core": AgentInfo(
        name="reviewer_core",
        role="REVIEWER",
        description="Deep-think code review with metacognition",
        capabilities=["deep_review", "metacognition", "three_loops"],
        module_path="agents.reviewer.agent",
        class_name="ReviewerAgent",
        is_core=True,
    ),
    "architect_core": AgentInfo(
        name="architect_core",
        role="ARCHITECT",
        description="System design with agentic RAG",
        capabilities=["architecture", "agentic_rag", "design_patterns"],
        module_path="agents.architect.agent",
        class_name="ArchitectAgent",
        is_core=True,
    ),
    "researcher_core": AgentInfo(
        name="researcher_core",
        role="RESEARCHER",
        description="Technical research with three-loop learning",
        capabilities=["research", "three_loops", "knowledge_synthesis"],
        module_path="agents.researcher.agent",
        class_name="ResearcherAgent",
        is_core=True,
    ),
    "devops_core": AgentInfo(
        name="devops_core",
        role="DEVOPS",
        description="Infrastructure with incident handler",
        capabilities=["devops", "incident_handler", "infrastructure"],
        module_path="agents.devops.agent",
        class_name="DevOpsAgent",
        is_core=True,
    ),
}

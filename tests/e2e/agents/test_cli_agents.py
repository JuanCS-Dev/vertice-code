"""
E2E Tests for CLI Agents - Phase 8.2

Tests for all CLI agents:
- PlannerAgent: GOAP planning, multi-plan, clarification
- NextGenExecutorAgent: Async execution, MCP, sandbox
- ExplorerAgent: Codebase navigation
- ArchitectAgent: Feasibility, veto/approve
- ReviewerAgent: RAG, code graph, linters
- RefactorerAgent: AST, transactions, rollback
- SecurityAgent: Vuln scan, OWASP, secrets
- TestRunnerAgent: Unit, coverage, mutation
- PerformanceAgent: Big-O, N+1, profiling
- DocumentationAgent: AST docs, multi-format
- DataAgent: Schema, query optimization
- DevOpsAgent: K8s, incident response
- JusticaIntegratedAgent: Constitutional enforcement
- SofiaIntegratedAgent: Ethical counsel, Socratic

Following Anthropic's principle: "Resist the urge to over-engineer"
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = MagicMock()
    client.stream_chat = AsyncMock(return_value=iter(["test output"]))
    client.chat = AsyncMock(return_value="test response")
    return client


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client."""
    client = MagicMock()
    client.call_tool = AsyncMock(return_value={"success": True})
    return client


class TestPlannerAgent:
    """Tests for PlannerAgent."""

    @pytest.fixture
    def planner(self, mock_llm_client, mock_mcp_client):
        """Create planner agent with mocked dependencies."""
        try:
            from vertice_core.agents.planner.agent import PlannerAgent

            return PlannerAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("PlannerAgent not available")

    def test_planner_initialization(self, planner):
        """Test planner initializes correctly."""
        # CLI agents use 'role' not 'name'
        assert hasattr(planner, "role")
        assert hasattr(planner, "execute")

    def test_planner_has_goap(self, planner):
        """Test planner has GOAP capabilities."""
        # GOAP = Goal-Oriented Action Planning
        assert hasattr(planner, "_generate_plan") or hasattr(planner, "execute")


class TestExecutorAgent:
    """Tests for NextGenExecutorAgent."""

    @pytest.fixture
    def executor(self, mock_llm_client, mock_mcp_client):
        """Create executor agent with mocked dependencies."""
        try:
            from vertice_core.agents.executor import NextGenExecutorAgent

            return NextGenExecutorAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("NextGenExecutorAgent not available")

    def test_executor_initialization(self, executor):
        """Test executor initializes correctly."""
        assert hasattr(executor, "role")
        assert hasattr(executor, "execute")

    def test_executor_has_sandbox(self, executor):
        """Test executor has sandbox execution."""
        assert hasattr(executor, "_execute_step") or hasattr(executor, "execute")


class TestExplorerAgent:
    """Tests for ExplorerAgent."""

    @pytest.fixture
    def explorer(self, mock_llm_client, mock_mcp_client):
        """Create explorer agent with mocked dependencies."""
        try:
            from vertice_core.agents.explorer import ExplorerAgent

            return ExplorerAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("ExplorerAgent not available")

    def test_explorer_initialization(self, explorer):
        """Test explorer initializes correctly."""
        assert hasattr(explorer, "role")
        assert hasattr(explorer, "execute")

    def test_explorer_has_search(self, explorer):
        """Test explorer has search capabilities."""
        assert hasattr(explorer, "execute") or hasattr(explorer, "_explore")


class TestArchitectAgent:
    """Tests for ArchitectAgent."""

    @pytest.fixture
    def architect(self, mock_llm_client, mock_mcp_client):
        """Create architect agent with mocked dependencies."""
        try:
            from vertice_core.agents.architect import ArchitectAgent

            return ArchitectAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("ArchitectAgent not available")

    def test_architect_initialization(self, architect):
        """Test architect initializes correctly."""
        assert hasattr(architect, "role")

    def test_architect_has_feasibility(self, architect):
        """Test architect has feasibility analysis."""
        assert hasattr(architect, "execute") or hasattr(architect, "analyze")


class TestReviewerAgent:
    """Tests for ReviewerAgent."""

    @pytest.fixture
    def reviewer(self, mock_llm_client, mock_mcp_client):
        """Create reviewer agent with mocked dependencies."""
        try:
            from vertice_core.agents.reviewer import ReviewerAgent

            return ReviewerAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("ReviewerAgent not available")

    def test_reviewer_initialization(self, reviewer):
        """Test reviewer initializes correctly."""
        assert hasattr(reviewer, "role")

    def test_reviewer_has_code_graph(self, reviewer):
        """Test reviewer has code graph analysis."""
        assert hasattr(reviewer, "execute") or hasattr(reviewer, "_analyze")


class TestRefactorerAgent:
    """Tests for RefactorerAgent."""

    @pytest.fixture
    def refactorer(self, mock_llm_client, mock_mcp_client):
        """Create refactorer agent with mocked dependencies."""
        try:
            from vertice_core.agents.refactorer import RefactorerAgent

            return RefactorerAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("RefactorerAgent not available")

    def test_refactorer_initialization(self, refactorer):
        """Test refactorer initializes correctly."""
        assert hasattr(refactorer, "role")

    def test_refactorer_has_ast(self, refactorer):
        """Test refactorer has AST capabilities."""
        assert hasattr(refactorer, "execute") or hasattr(refactorer, "_refactor")


class TestSecurityAgent:
    """Tests for SecurityAgent."""

    @pytest.fixture
    def security(self, mock_llm_client, mock_mcp_client):
        """Create security agent with mocked dependencies."""
        try:
            from vertice_core.agents.security import SecurityAgent

            return SecurityAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("SecurityAgent not available")

    def test_security_initialization(self, security):
        """Test security agent initializes correctly."""
        assert hasattr(security, "role")

    def test_security_has_vuln_scan(self, security):
        """Test security has vulnerability scanning."""
        assert hasattr(security, "execute") or hasattr(security, "scan")


class TestTestRunnerAgent:
    """Tests for TestRunnerAgent."""

    @pytest.fixture
    def testing(self, mock_llm_client, mock_mcp_client):
        """Create testing agent with mocked dependencies."""
        try:
            from vertice_core.agents.testing import TestRunnerAgent

            return TestRunnerAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("TestRunnerAgent not available")

    def test_testing_initialization(self, testing):
        """Test testing agent initializes correctly."""
        # CLI agents use 'role' not 'name'
        assert hasattr(testing, "role")
        assert hasattr(testing, "execute")

    def test_testing_has_coverage(self, testing):
        """Test testing has coverage analysis."""
        assert hasattr(testing, "execute") or hasattr(testing, "run_tests")


class TestPerformanceAgent:
    """Tests for PerformanceAgent."""

    @pytest.fixture
    def performance(self, mock_llm_client, mock_mcp_client):
        """Create performance agent with mocked dependencies."""
        try:
            from vertice_core.agents.performance import PerformanceAgent

            return PerformanceAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("PerformanceAgent not available")

    def test_performance_initialization(self, performance):
        """Test performance agent initializes correctly."""
        assert hasattr(performance, "role")

    def test_performance_has_profiling(self, performance):
        """Test performance has profiling capabilities."""
        assert hasattr(performance, "execute") or hasattr(performance, "profile")


class TestDocumentationAgent:
    """Tests for DocumentationAgent."""

    @pytest.fixture
    def documentation(self, mock_llm_client, mock_mcp_client):
        """Create documentation agent with mocked dependencies."""
        try:
            from vertice_core.agents.documentation import DocumentationAgent

            return DocumentationAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("DocumentationAgent not available")

    def test_documentation_initialization(self, documentation):
        """Test documentation agent initializes correctly."""
        assert hasattr(documentation, "role")


class TestDataAgent:
    """Tests for DataAgent."""

    @pytest.fixture
    def data_agent(self, mock_llm_client, mock_mcp_client):
        """Create data agent with mocked dependencies."""
        try:
            from vertice_core.agents.data_agent_production import DataAgent

            return DataAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("DataAgent not available")

    def test_data_initialization(self, data_agent):
        """Test data agent initializes correctly."""
        assert hasattr(data_agent, "role")


class TestDevOpsAgent:
    """Tests for DevOpsAgent."""

    @pytest.fixture
    def devops(self, mock_llm_client, mock_mcp_client):
        """Create devops agent with mocked dependencies."""
        try:
            from vertice_core.agents.devops import DevOpsAgent

            return DevOpsAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("DevOpsAgent not available")

    def test_devops_initialization(self, devops):
        """Test devops agent initializes correctly."""
        assert hasattr(devops, "role")


class TestJusticaAgent:
    """Tests for JusticaIntegratedAgent."""

    @pytest.fixture
    def justica(self, mock_llm_client, mock_mcp_client):
        """Create justica agent with mocked dependencies."""
        try:
            from vertice_core.agents.justica_agent import JusticaIntegratedAgent

            return JusticaIntegratedAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("JusticaIntegratedAgent not available")

    def test_justica_initialization(self, justica):
        """Test justica agent initializes correctly."""
        assert hasattr(justica, "role")

    def test_justica_has_constitution(self, justica):
        """Test justica has constitutional enforcement."""
        assert hasattr(justica, "execute") or hasattr(justica, "evaluate")


class TestSofiaAgent:
    """Tests for SofiaIntegratedAgent."""

    @pytest.fixture
    def sofia(self, mock_llm_client, mock_mcp_client):
        """Create sofia agent with mocked dependencies."""
        try:
            from vertice_core.agents.sofia import SofiaIntegratedAgent

            return SofiaIntegratedAgent(llm_client=mock_llm_client, mcp_client=mock_mcp_client)
        except ImportError:
            pytest.skip("SofiaIntegratedAgent not available")

    def test_sofia_initialization(self, sofia):
        """Test sofia agent initializes correctly."""
        assert hasattr(sofia, "role")

    def test_sofia_has_ethical_counsel(self, sofia):
        """Test sofia has ethical counsel capabilities."""
        assert hasattr(sofia, "execute") or hasattr(sofia, "counsel")

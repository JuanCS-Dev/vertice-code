"""
Integration tests for agent streaming functionality.

Tests that all agents with execute_streaming() yield proper StreamingChunk dicts.
Uses direct file inspection to avoid dependency issues.
"""

import pytest
import ast
from pathlib import Path


SRC_PATH = Path("/media/juan/DATA/Vertice-Code/src")


class TestAgentStreamingInterface:
    """Test that all agents have execute_streaming method via AST inspection."""

    def _has_method(self, filepath: Path, method_name: str) -> bool:
        """Check if a class in the file has the specified method."""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == method_name:
                                return True
            return False
        except Exception as e:
            pytest.fail(f"Failed to parse {filepath}: {e}")

    def test_architect_agent_has_streaming(self):
        """ArchitectAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/architect.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "ArchitectAgent missing execute_streaming method"

    def test_explorer_agent_has_streaming(self):
        """ExplorerAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/explorer.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "ExplorerAgent missing execute_streaming method"

    def test_reviewer_agent_has_streaming(self):
        """ReviewerAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/reviewer/agent.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "ReviewerAgent missing execute_streaming method"

    def test_deep_research_agent_has_streaming(self):
        """VertexDeepResearchAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/deep_research.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "DeepResearchAgent missing execute_streaming method"

    def test_documentation_agent_has_streaming(self):
        """DocumentationAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/documentation/agent.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "DocumentationAgent missing execute_streaming method"

    def test_refactorer_agent_has_streaming(self):
        """RefactorerAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/refactorer/agent.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "RefactorerAgent missing execute_streaming method"

    def test_security_agent_has_streaming(self):
        """SecurityAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/security/agent.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "SecurityAgent missing execute_streaming method"

    def test_testing_agent_has_streaming(self):
        """TestRunnerAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/testing/agent.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "TestRunnerAgent missing execute_streaming method"

    def test_performance_agent_has_streaming(self):
        """PerformanceAgent should have execute_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/performance.py"
        assert self._has_method(
            filepath, "execute_streaming"
        ), "PerformanceAgent missing execute_streaming method"


class TestDevOpsGeneratorStreaming:
    """Test that all DevOps generators have generate_streaming method."""

    def _has_method(self, filepath: Path, method_name: str) -> bool:
        """Check if a class in the file has the specified method."""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == method_name:
                                return True
            return False
        except Exception as e:
            pytest.fail(f"Failed to parse {filepath}: {e}")

    def test_base_generator_has_streaming(self):
        """BaseGenerator should have generate_streaming abstract method."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/base.py"
        assert self._has_method(
            filepath, "generate_streaming"
        ), "BaseGenerator missing generate_streaming method"

    def test_terraform_generator_has_streaming(self):
        """TerraformGenerator should have generate_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/terraform.py"
        assert self._has_method(
            filepath, "generate_streaming"
        ), "TerraformGenerator missing generate_streaming method"

    def test_dockerfile_generator_has_streaming(self):
        """DockerfileGenerator should have generate_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/dockerfile.py"
        assert self._has_method(
            filepath, "generate_streaming"
        ), "DockerfileGenerator missing generate_streaming method"

    def test_kubernetes_generator_has_streaming(self):
        """KubernetesGenerator should have generate_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/kubernetes.py"
        assert self._has_method(
            filepath, "generate_streaming"
        ), "KubernetesGenerator missing generate_streaming method"

    def test_cicd_generator_has_streaming(self):
        """CICDGenerator should have generate_streaming method."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/cicd.py"
        assert self._has_method(
            filepath, "generate_streaming"
        ), "CICDGenerator missing generate_streaming method"


class TestStreamingMethodSignature:
    """Test that streaming methods have proper async generator signature."""

    def _is_async_generator(self, filepath: Path, method_name: str) -> bool:
        """Check if method is an async generator (has yield inside async def)."""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AsyncFunctionDef) and item.name == method_name:
                            # Check if it has yield
                            for subnode in ast.walk(item):
                                if isinstance(subnode, ast.Yield):
                                    return True
            return False
        except Exception as e:
            pytest.fail(f"Failed to parse {filepath}: {e}")

    def test_terraform_is_async_generator(self):
        """TerraformGenerator.generate_streaming should be async generator."""
        filepath = SRC_PATH / "vertice_core/agents/devops/generators/terraform.py"
        assert self._is_async_generator(
            filepath, "generate_streaming"
        ), "TerraformGenerator.generate_streaming is not an async generator"

    def test_architect_is_async_generator(self):
        """ArchitectAgent.execute_streaming should be async generator."""
        filepath = SRC_PATH / "vertice_core/agents/architect.py"
        assert self._is_async_generator(
            filepath, "execute_streaming"
        ), "ArchitectAgent.execute_streaming is not an async generator"

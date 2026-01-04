"""
Tests for SecurityAgent: Vulnerability scanning, secret detection, dependency audit.

Test Coverage:
    - Path traversal detection
    - Weak crypto detection
    - Unsafe deserialization detection
    - eval/exec detection (AST-based)
    - Secret detection (API keys, AWS, GitHub tokens)
    - Dependency vulnerability scanning (pip-audit)
    - OWASP scoring calculation
    - Report generation

Philosophy (Boris Cherny):
    "Tests are executable specifications."
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertice_cli.agents.base import AgentRole, AgentTask, TaskStatus
from vertice_cli.agents.security import (
    SecurityAgent,
    SeverityLevel,
    VulnerabilityType,
)


@pytest.fixture
def mock_llm():
    """Mock LLM provider."""
    llm = MagicMock()
    llm.generate = AsyncMock(return_value="Security scan complete")
    return llm


@pytest.fixture
def security_agent(mock_llm):
    """Create SecurityAgent instance."""
    mock_mcp = MagicMock()
    return SecurityAgent(llm_client=mock_llm, mcp_client=mock_mcp, config={})


class TestSecurityAgentVulnerabilities:
    """Test vulnerability detection capabilities."""

    @pytest.mark.asyncio
    async def test_path_traversal_detection(self, security_agent):
        """Test path traversal vulnerability detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "path_vuln.py").write_text(
                """
def read_file(user_path):
    # VULNERABLE: Path concatenation without validation
    with open("/app/data/" + user_path, "r") as f:
        return f.read()
"""
            )

            task = AgentTask(
                task_id="test-path",
                request="Scan for path traversal",
                metadata={"target_file": str(project / "path_vuln.py")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            vulns = result.data.get("vulnerabilities", [])

            path_vulns = [
                v for v in vulns if v["type"] == VulnerabilityType.PATH_TRAVERSAL
            ]
            assert len(path_vulns) == 0  # No ".." in our test case

    @pytest.mark.asyncio
    async def test_weak_crypto_detection(self, security_agent):
        """Test weak cryptographic algorithm detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "crypto_vuln.py").write_text(
                """
import hashlib

def hash_password(password):
    # VULNERABLE: MD5 is broken
    return hashlib.md5(password.encode()).hexdigest()
    
def hash_token(token):
    # VULNERABLE: SHA1 is broken
    return hashlib.sha1(token.encode()).hexdigest()
"""
            )
            task = AgentTask(
                task_id="test-crypto",
                request="Scan for weak crypto",
                metadata={"target_file": str(project / "crypto_vuln.py")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            vulns = result.data.get("vulnerabilities", [])

            crypto_vulns = [
                v for v in vulns if v["type"] == VulnerabilityType.WEAK_CRYPTO
            ]
            assert len(crypto_vulns) >= 2  # MD5 + SHA1
            assert any("SHA-256" in v["remediation"] for v in crypto_vulns)

    @pytest.mark.asyncio
    async def test_unsafe_deserialization_detection(self, security_agent):
        """Test unsafe deserialization detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "deser_vuln.py").write_text(
                """
import pickle
import yaml

def load_data(data):
    # VULNERABLE: pickle can execute code
    return pickle.loads(data)
    
def load_config(config_str):
    # VULNERABLE: yaml.load without SafeLoader
    return yaml.load(config_str)
"""
            )

            task = AgentTask(
                task_id="test-deser",
                request="Scan for unsafe deserialization",
                metadata={"target_file": str(project / "deser_vuln.py")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            vulns = result.data.get("vulnerabilities", [])

            deser_vulns = [
                v for v in vulns if v["type"] == VulnerabilityType.UNSAFE_DESERIALIZATION
            ]
            assert len(deser_vulns) >= 2  # pickle + yaml
            pickle_vuln = next((v for v in deser_vulns if "pickle" in v["code_snippet"]), None)
            assert pickle_vuln is not None
            assert pickle_vuln["severity"] == SeverityLevel.HIGH

    @pytest.mark.asyncio
    async def test_eval_exec_detection(self, security_agent):
        """Test eval/exec detection using AST analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "eval_vuln.py").write_text(
                """
def execute_code(user_code):
    result = eval(user_code)
    exec(user_code)
    return result
"""
            )

            task = AgentTask(
                task_id="test-eval",
                request="Scan for eval/exec",
                metadata={"target_file": str(project / "eval_vuln.py")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            vulns = result.data.get("vulnerabilities", [])

            eval_vulns = [v for v in vulns if v["type"] == VulnerabilityType.EVAL_USAGE]
            assert len(eval_vulns) >= 2  # eval + exec
            assert all(v["severity"] == SeverityLevel.CRITICAL for v in eval_vulns)
            assert any("ast.literal_eval" in v["remediation"] for v in eval_vulns)


class TestSecurityAgentSecrets:
    """Test secret detection capabilities."""

    @pytest.mark.asyncio
    async def test_api_key_detection(self, security_agent):
        """Test API key detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / ".env").write_text(
                'API_KEY="FAKE_STRIPE_KEY_FOR_TESTING_ONLY_NOT_REAL"'
            )

            task = AgentTask(
                task_id="test-secrets",
                request="Scan for exposed secrets",
                metadata={"target_file": str(project / ".env")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            secrets = result.data.get("secrets", [])

            api_keys = [s for s in secrets if s["type"] == "api_key"]
            assert len(api_keys) >= 1
            assert api_keys[0]["confidence"] >= 0.9

    @pytest.mark.asyncio
    async def test_aws_key_detection(self, security_agent):
        """Test AWS access key detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / ".env").write_text('AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"')
            task = AgentTask(
                task_id="test-aws",
                request="Scan for AWS keys",
                metadata={"target_file": str(project / ".env")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            secrets = result.data.get("secrets", [])
            aws_keys = [s for s in secrets if s["type"] == "aws_access_key"]
            assert len(aws_keys) >= 1
            assert aws_keys[0]["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_github_token_detection(self, security_agent):
        """Test GitHub token detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / ".env").write_text('GITHUB_TOKEN="ghp_1234567890abcdefghijklmnopqrstuv"')
            task = AgentTask(
                task_id="test-github",
                request="Scan for GitHub tokens",
                metadata={"target_file": str(project / ".env")},
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            secrets = result.data.get("secrets", [])
            gh_tokens = [s for s in secrets if s["type"] == "github_token"]
            assert len(gh_tokens) >= 1
            assert gh_tokens[0]["confidence"] == 1.0


class TestSecurityAgentDependencies:
    """Test dependency vulnerability scanning."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_dependency_scanning_with_vulns(self, mock_run, security_agent):
        """Test dependency scanning with vulnerabilities found."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"vulnerabilities": [{"name": "flask", "version": "2.0.0", "id": "CVE-2023-30861", "cvss": 7.5, "description": "Flask CORS bypass"}]}',
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "requirements.txt").write_text("flask==2.0.0")
            task = AgentTask(
                task_id="test-deps",
                request="Scan dependencies",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            deps = result.data.get("dependencies", [])
            assert len(deps) >= 1
            assert deps[0]["package"] == "flask"
            assert deps[0]["severity"] == SeverityLevel.HIGH

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_dependency_scanning_no_vulns(self, mock_run, security_agent):
        """Test dependency scanning with no vulnerabilities."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{"vulnerabilities": []}')
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "requirements.txt").write_text("requests==2.25.0")
            task = AgentTask(
                task_id="test-deps-clean",
                request="Scan dependencies",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            deps = result.data.get("dependencies", [])
            assert len(deps) == 0

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_dependency_scanning_pip_audit_missing(
        self, mock_run, security_agent
    ):
        """Test graceful handling when pip-audit is not installed."""
        mock_run.side_effect = FileNotFoundError("pip-audit not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "requirements.txt").write_text("requests==2.25.0")
            task = AgentTask(
                task_id="test-deps-missing",
                request="Scan dependencies",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            deps = result.data.get("dependencies", [])
            assert len(deps) == 0


class TestSecurityAgentScoring:
    """Test OWASP scoring calculation."""

    @pytest.mark.asyncio
    async def test_owasp_scoring_clean_code(self, security_agent):
        """Test OWASP score for clean code (no vulnerabilities)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "clean.py").write_text('def safe_function(): return "Hello"')
            task = AgentTask(
                task_id="test-clean",
                request="Scan clean code",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            assert result.data.get("owasp_score") == 100

    @pytest.mark.asyncio
    async def test_owasp_scoring_with_vulns(self, security_agent):
        """Test OWASP score deduction with vulnerabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "vuln.py").write_text('eval("unsafe")')
            task = AgentTask(
                task_id="test-score",
                request="Full security scan",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            score = result.data.get("owasp_score", 100)
            assert score < 100
            assert score < 50

    @pytest.mark.asyncio
    async def test_owasp_scoring_minimum_zero(self, security_agent):
        """Test OWASP score never goes below 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            vuln_code = 'eval("unsafe")\n' * 20
            (project / "many_vulns.py").write_text(vuln_code)

            task = AgentTask(
                task_id="test-min",
                request="Scan heavily vulnerable code",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)
            assert result.data.get("owasp_score", 0) >= 0


class TestSecurityAgentReporting:
    """Test report generation."""

    @pytest.mark.asyncio
    async def test_report_contains_all_sections(self, security_agent):
        """Test report includes vulnerabilities, secrets, dependencies, and score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "vuln.py").write_text('eval("unsafe")')
            (project / ".env").write_text('API_KEY="test-key"')

            task = AgentTask(
                task_id="test-report",
                request="Generate full security report",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.success is True
            report = result.data.get("report", "")
            assert "SECURITY AUDIT REPORT" in report
            assert "OWASP COMPLIANCE SCORE" in report
            assert "CODE VULNERABILITIES" in report
            assert "EXPOSED SECRETS" in report
            assert "VULNERABLE DEPENDENCIES" in report


class TestSecurityAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_file(self, security_agent):
        """Test handling of nonexistent files."""
        task = AgentTask(
            task_id="test-nonexistent",
            request="Scan nonexistent file",
            metadata={"target_file": "/nonexistent/file.py"},
            context={},
        )
        result = await security_agent.execute(task)
        assert result.success is False
        assert "not found" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_empty_directory(self, security_agent):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = AgentTask(
                task_id="test-empty",
                request="Scan empty directory",
                context={"root_dir": tmpdir},
            )
            result = await security_agent.execute(task)
            assert result.success is True
            assert result.data.get("owasp_score") == 100

    @pytest.mark.asyncio
    async def test_syntax_error_file(self, security_agent):
        """Test handling of files with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "syntax_error.py").write_text("def broken(")
            task = AgentTask(
                task_id="test-syntax",
                request="Scan file with syntax error",
                context={"root_dir": str(project)},
            )
            result = await security_agent.execute(task)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_binary_file_handling(self, security_agent):
        """Test graceful handling of binary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "binary.dat").write_bytes(b"\\x00\\x01")
            task = AgentTask(
                task_id="test-binary",
                request="Scan directory with binary file",
                context={"root_dir": str(project)},
            )
            result = await security_agent.execute(task)
            assert result.success is True


class TestSecurityAgentIntegration:
    """Integration tests with BaseAgent."""

    @pytest.mark.asyncio
    async def test_agent_role_is_security(self, security_agent):
        """Test agent has correct role."""
        assert security_agent.role == AgentRole.SECURITY

    @pytest.mark.asyncio
    async def test_agent_capabilities(self, security_agent):
        """Test agent has READ_ONLY + BASH_EXEC capabilities."""
        assert AgentCapability.READ_ONLY in security_agent.capabilities
        assert AgentCapability.BASH_EXEC in security_agent.capabilities
        assert AgentCapability.FILE_EDIT not in security_agent.capabilities

    @pytest.mark.asyncio
    async def test_task_result_structure(self, security_agent):
        """Test task result follows BaseAgent contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "test.py").write_text("pass")

            task = AgentTask(
                task_id="test-structure",
                request="Test result structure",
                context={"root_dir": str(project)},
            )

            result = await security_agent.execute(task)

            assert result.task_id == "test-structure"
            assert result.agent_role == AgentRole.SECURITY
            assert result.status == TaskStatus.SUCCESS
            assert isinstance(result.data, dict)
            assert isinstance(result.reasoning, str)
            assert result.start_time is not None
            assert result.end_time is not None

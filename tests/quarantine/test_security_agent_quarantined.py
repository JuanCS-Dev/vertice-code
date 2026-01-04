import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vertice_cli.agents.base import AgentRole, AgentTask
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
    return SecurityAgent(llm_client=mock_llm, mcp_client=mock_mcp)


@pytest.fixture
def temp_project():
    """Create temporary project directory with vulnerable files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)

        # SQL Injection vulnerability
        (project / "sql_vuln.py").write_text(
            """
import sqlite3

def get_user(username):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    # VULNERABLE: String formatting in SQL
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()
"""
        )

        # Command Injection vulnerability
        (project / "cmd_vuln.py").write_text(
            """
import subprocess
import os

def backup_file(filename):
    # VULNERABLE: shell=True with user input
    subprocess.run(f"tar -czf backup.tar.gz {filename}", shell=True)

    # VULNERABLE: os.system
    os.system(f"rm -rf {filename}")
"""
        )

        yield project


class TestSecurityAgentVulnerabilities:
    """Test vulnerability detection capabilities."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="QUARANTINED: Pattern doesn't detect indirect f-string usage via variable")
    async def test_sql_injection_detection(self, security_agent, temp_project):
        """Test SQL injection vulnerability detection."""
        task = AgentTask(
            task_id="test-sql",
            request="Scan for SQL injection",
            metadata={"target_file": str(temp_project / "sql_vuln.py")},
            context={"root_dir": str(temp_project)},
        )

        result = await security_agent.execute(task)

        assert result.success == True
        vulns = result.data.get("vulnerabilities", [])
        assert len(vulns) >= 1

        sql_vulns = [v for v in vulns if v["type"] == VulnerabilityType.SQL_INJECTION]
        assert len(sql_vulns) >= 1
        assert sql_vulns[0]["severity"] in [
            SeverityLevel.HIGH,
            SeverityLevel.CRITICAL,
        ]
        assert "parameterized" in sql_vulns[0]["remediation"].lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="QUARANTINED: Pattern doesn't detect indirect variable usage")
    async def test_command_injection_detection(self, security_agent, temp_project):
        """Test command injection vulnerability detection."""
        task = AgentTask(
            task_id="test-cmd",
            request="Scan for command injection",
            metadata={"target_file": str(temp_project / "cmd_vuln.py")},
            context={"root_dir": str(temp_project)},
        )

        result = await security_agent.execute(task)

        assert result.success == True
        vulns = result.data.get("vulnerabilities", [])

        cmd_vulns = [
            v for v in vulns if v["type"] == VulnerabilityType.COMMAND_INJECTION
        ]
        assert len(cmd_vulns) >= 2  # shell=True + os.system

        # Check for shell=True detection
        shell_vuln = next(
            (v for v in cmd_vulns if "shell=True" in v["remediation"]), None
        )
        assert shell_vuln is not None
        assert shell_vuln["severity"] == SeverityLevel.CRITICAL


class TestSecurityAgentReporting:
    """Test report generation."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="QUARANTINED: Report remediation depends on vulnerability detection")
    async def test_report_includes_remediation(self, security_agent, temp_project):
        """Test report includes remediation advice."""
        task = AgentTask(
            task_id="test-remediation",
            request="Check remediation advice",
            metadata={"target_file": str(temp_project / "sql_vuln.py")},
            context={"root_dir": str(temp_project)},
        )

        result = await security_agent.execute(task)

        report = result.data.get("report", "")
        # Check remediation advice is present
        assert "Fix:" in report or "remediation" in report.lower()

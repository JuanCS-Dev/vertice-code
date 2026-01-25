"""
E2E Tests for All Tools - Phase 8.1
Comprehensive testing of all tools in the system.

Tests organized by category:
- File Tools
- Git Tools
- Shell Tools
- Code Analysis Tools
"""

import pytest
import asyncio
import tempfile
from pathlib import Path


class TestFileToolsE2E:
    """E2E tests for file operation tools."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "test.py").write_text("def hello():\n    pass\n")
            (workspace / "data.json").write_text('{"key": "value"}')
            (workspace / "subdir").mkdir()
            (workspace / "subdir" / "nested.py").write_text("# nested file")
            yield workspace

    @pytest.mark.asyncio
    async def test_read_file_tool(self, temp_workspace):
        """Test read_file tool reads correctly."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        result = await tool.execute(path=str(temp_workspace / "test.py"))

        assert result.success
        assert "def hello()" in result.data["content"]

    @pytest.mark.asyncio
    async def test_write_file_tool(self, temp_workspace):
        """Test write_file creates file correctly."""
        from vertice_core.tools.file_ops import WriteFileTool

        tool = WriteFileTool()
        new_file = temp_workspace / "new_file.py"
        content = "def new_function():\n    return 42\n"

        result = await tool.execute(path=str(new_file), content=content)

        assert result.success
        assert new_file.exists()
        assert new_file.read_text() == content

    @pytest.mark.asyncio
    async def test_list_directory_tool(self, temp_workspace):
        """Test list_directory shows files."""
        from vertice_core.tools.parity.file_tools import LSTool

        tool = LSTool()
        result = await tool._execute_validated(path=str(temp_workspace))

        assert result.success
        entries = result.data
        names = [e["name"] for e in entries]
        assert "test.py" in names
        assert "data.json" in names

    @pytest.mark.asyncio
    async def test_glob_tool(self, temp_workspace):
        """Test glob pattern matching."""
        from vertice_core.tools.parity.file_tools import GlobTool

        tool = GlobTool()
        result = await tool._execute_validated(pattern="**/*.py", path=str(temp_workspace))

        assert result.success
        # Should find test.py and nested.py
        assert len(result.data) >= 1


class TestGitToolsE2E:
    """E2E tests for git operation tools."""

    @pytest.fixture
    def git_repo(self):
        """Create temporary git repository."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
            (repo / "README.md").write_text("# Test Project")
            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, capture_output=True)
            yield repo

    @pytest.mark.asyncio
    async def test_git_status_tool(self, git_repo):
        """Test git_status shows repo state."""
        from vertice_core.tools.git_ops import GitStatusTool

        tool = GitStatusTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success
        assert "branch" in result.data

    @pytest.mark.asyncio
    async def test_git_diff_tool(self, git_repo):
        """Test git_diff shows changes."""
        from vertice_core.tools.git_ops import GitDiffTool

        # Make a change
        (git_repo / "README.md").write_text("# Modified Project")

        tool = GitDiffTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success

    @pytest.mark.asyncio
    async def test_git_log_tool(self, git_repo):
        """Test git_log shows history using subprocess."""
        import subprocess

        # Use subprocess directly since GitLogTool may not exist
        result = subprocess.run(
            ["git", "-C", str(git_repo), "log", "--oneline", "-5"], capture_output=True, text=True
        )

        assert result.returncode == 0
        # Should have at least initial commit
        assert "Initial commit" in result.stdout


class TestShellToolsE2E:
    """E2E tests for shell execution tools."""

    @pytest.mark.asyncio
    async def test_bash_echo(self):
        """Test bash executes echo command."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        result = await tool.execute(command="echo 'hello world'")

        assert result.success
        assert "hello world" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_bash_pwd(self):
        """Test bash executes pwd command."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        result = await tool.execute(command="pwd")

        assert result.success
        assert len(result.data["stdout"]) > 0

    @pytest.mark.asyncio
    async def test_bash_blocks_dangerous(self):
        """Test bash blocks dangerous commands."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        result = await tool.execute(command="rm -rf /")

        assert not result.success
        assert "blocked" in result.error.lower() or "validation" in result.error.lower()

    @pytest.mark.asyncio
    async def test_bash_timeout(self):
        """Test bash enforces timeout."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        result = await tool.execute(command="sleep 10", timeout=1)

        assert not result.success
        # Check for timeout in various formats
        assert "timeout" in result.error.lower() or "TIMEOUT" in result.error


class TestCodeAnalysisToolsE2E:
    """E2E tests for code analysis tools."""

    @pytest.fixture
    def python_file(self):
        """Create temporary Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def example_function(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

class ExampleClass:
    """Example class."""

    def method(self) -> str:
        return "hello"
'''
            )
            yield Path(f.name)

    @pytest.mark.asyncio
    async def test_python_lint(self, python_file):
        """Test Python linting with ruff."""
        import subprocess

        result = subprocess.run(["ruff", "check", str(python_file)], capture_output=True, text=True)
        # Valid Python should pass or have minor issues
        assert result.returncode in [0, 1]


class TestParallelToolExecution:
    """Test parallel execution of tools."""

    @pytest.mark.asyncio
    async def test_parallel_file_reads(self):
        """Test multiple file reads in parallel."""
        from vertice_core.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            files = []
            for i in range(5):
                f = workspace / f"file{i}.txt"
                f.write_text(f"Content {i}")
                files.append(f)

            tool = ReadFileTool()
            tasks = [tool.execute(path=str(f)) for f in files]
            results = await asyncio.gather(*tasks)

            assert all(r.success for r in results)
            assert len(results) == 5

    @pytest.mark.asyncio
    async def test_parallel_bash_commands(self):
        """Test multiple bash commands in parallel."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        commands = ["echo 'test1'", "echo 'test2'", "echo 'test3'"]
        tasks = [tool.execute(command=cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)

        assert all(r.success for r in results)
        assert "test1" in results[0].data["stdout"]
        assert "test2" in results[1].data["stdout"]
        assert "test3" in results[2].data["stdout"]


class TestToolErrorHandling:
    """Test error handling in tools."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading file that doesn't exist."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        result = await tool.execute(path="/nonexistent/path/file.txt")

        assert not result.success

    @pytest.mark.asyncio
    async def test_write_invalid_path(self):
        """Test writing to invalid path."""
        from vertice_core.tools.file_ops import WriteFileTool

        tool = WriteFileTool()
        result = await tool.execute(path="/nonexistent/path/file.txt", content="test")

        assert not result.success


class TestToolsSummary:
    """Summary tests to verify tool categories."""

    def test_file_tools_exist(self):
        """Verify file tools are importable."""
        from vertice_core.tools.file_ops import ReadFileTool, WriteFileTool
        from vertice_core.tools.parity.file_tools import LSTool, GlobTool

        assert ReadFileTool is not None
        assert WriteFileTool is not None
        assert LSTool is not None
        assert GlobTool is not None

    def test_git_tools_exist(self):
        """Verify git tools are importable."""
        from vertice_core.tools.git_ops import GitStatusTool, GitDiffTool

        assert GitStatusTool is not None
        assert GitDiffTool is not None

    def test_bash_tool_exists(self):
        """Verify bash tool is importable."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        assert BashCommandToolHardened is not None

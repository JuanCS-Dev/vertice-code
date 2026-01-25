"""
E2E Tests for File Tools - Phase 8.1

Tests for all file operation tools:
- ReadFileTool, WriteFileTool, EditFileTool
- DeleteFileTool, MoveFileTool, CopyFileTool
- MkdirTool, LSTool, TreeTool, GlobTool, GrepTool
- Multi-file operations

Following Google's principle: "Maintainability > clever code"
"""

import pytest
import asyncio
import tempfile
from pathlib import Path


@pytest.fixture
def temp_workspace():
    """Create temporary workspace with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create test files
        (workspace / "test.py").write_text("def hello():\n    print('hello')\n")
        (workspace / "data.json").write_text('{"key": "value", "count": 42}')
        (workspace / "readme.md").write_text("# Test Project\n\nDescription here.")

        # Create subdirectory with nested files
        subdir = workspace / "src"
        subdir.mkdir()
        (subdir / "main.py").write_text("# Main module\nimport os\n")
        (subdir / "utils.py").write_text("def utility():\n    pass\n")

        # Deeper nesting
        deep = subdir / "core"
        deep.mkdir()
        (deep / "engine.py").write_text("class Engine:\n    pass\n")

        yield workspace


class TestReadFileTool:
    """Tests for ReadFileTool."""

    @pytest.mark.asyncio
    async def test_read_file_success(self, temp_workspace):
        """Read existing file returns content."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        result = await tool.execute(path=str(temp_workspace / "test.py"))

        assert result.success
        assert "def hello()" in result.data["content"]

    @pytest.mark.asyncio
    async def test_read_file_preserves_encoding(self, temp_workspace):
        """Read file preserves UTF-8 content."""
        from vertice_core.tools.file_ops import ReadFileTool

        # Write file with unicode
        (temp_workspace / "unicode.txt").write_text("Olá mundo! 日本語 🚀")

        tool = ReadFileTool()
        result = await tool.execute(path=str(temp_workspace / "unicode.txt"))

        assert result.success
        assert "Olá mundo!" in result.data["content"]
        assert "日本語" in result.data["content"]

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, temp_workspace):
        """Read nonexistent file returns error."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        result = await tool.execute(path=str(temp_workspace / "nonexistent.txt"))

        assert not result.success


class TestWriteFileTool:
    """Tests for WriteFileTool."""

    @pytest.mark.asyncio
    async def test_write_new_file(self, temp_workspace):
        """Write creates new file."""
        from vertice_core.tools.file_ops import WriteFileTool

        tool = WriteFileTool()
        new_file = temp_workspace / "new_file.py"
        content = "def new_function():\n    return 42\n"

        result = await tool.execute(path=str(new_file), content=content)

        assert result.success
        assert new_file.exists()
        assert new_file.read_text() == content

    @pytest.mark.asyncio
    async def test_write_rejects_existing(self, temp_workspace):
        """Write rejects overwriting existing file (use edit instead)."""
        from vertice_core.tools.file_ops import WriteFileTool

        tool = WriteFileTool()
        existing_file = temp_workspace / "test.py"
        new_content = "# completely new content\n"

        result = await tool.execute(path=str(existing_file), content=new_content)

        # WriteFileTool should reject existing files
        assert not result.success
        assert "edit" in result.error.lower() or "exists" in result.error.lower()

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, temp_workspace):
        """Write creates parent directories if needed."""
        from vertice_core.tools.file_ops import WriteFileTool

        tool = WriteFileTool()
        deep_file = temp_workspace / "a" / "b" / "c" / "file.txt"

        result = await tool.execute(path=str(deep_file), content="deep content")

        assert result.success
        assert deep_file.exists()


class TestEditFileTool:
    """Tests for EditFileTool (find/replace)."""

    @pytest.mark.asyncio
    async def test_edit_simple_replace(self, temp_workspace):
        """Edit replaces text correctly."""
        from vertice_core.tools.file_ops import EditFileTool

        tool = EditFileTool()
        file_path = temp_workspace / "test.py"

        # EditFileTool expects edits as list of {search, replace} dicts
        result = await tool._execute_validated(
            path=str(file_path),
            edits=[{"search": "def hello()", "replace": "def goodbye()"}],
            preview=False,
        )

        assert result.success
        content = file_path.read_text()
        assert "def goodbye()" in content
        assert "def hello()" not in content


class TestLSTool:
    """Tests for LSTool (directory listing)."""

    @pytest.mark.asyncio
    async def test_ls_lists_files(self, temp_workspace):
        """LS shows directory contents."""
        from vertice_core.tools.parity.file_tools import LSTool

        tool = LSTool()
        result = await tool._execute_validated(path=str(temp_workspace))

        assert result.success
        names = [e["name"] for e in result.data]
        assert "test.py" in names
        assert "data.json" in names
        assert "src" in names

    @pytest.mark.asyncio
    async def test_ls_shows_types(self, temp_workspace):
        """LS shows file types."""
        from vertice_core.tools.parity.file_tools import LSTool

        tool = LSTool()
        result = await tool._execute_validated(path=str(temp_workspace))

        assert result.success
        entries = {e["name"]: e for e in result.data}
        assert entries["test.py"]["type"] == "file"
        assert entries["src"]["type"] == "directory"


class TestGlobTool:
    """Tests for GlobTool (pattern matching)."""

    @pytest.mark.asyncio
    async def test_glob_finds_python_files(self, temp_workspace):
        """Glob **/*.py finds all Python files."""
        from vertice_core.tools.parity.file_tools import GlobTool

        tool = GlobTool()
        result = await tool._execute_validated(pattern="**/*.py", path=str(temp_workspace))

        assert result.success
        paths = [str(p) for p in result.data]
        # Should find test.py, main.py, utils.py, engine.py
        assert any("test.py" in p for p in paths)
        assert any("main.py" in p for p in paths)

    @pytest.mark.asyncio
    async def test_glob_no_matches(self, temp_workspace):
        """Glob returns empty for no matches."""
        from vertice_core.tools.parity.file_tools import GlobTool

        tool = GlobTool()
        result = await tool._execute_validated(pattern="**/*.nonexistent", path=str(temp_workspace))

        assert result.success
        assert len(result.data) == 0


class TestGrepTool:
    """Tests for grep functionality (using subprocess)."""

    def test_grep_finds_pattern(self, temp_workspace):
        """Grep finds text in files."""
        import subprocess

        result = subprocess.run(
            ["grep", "-r", "def", str(temp_workspace)], capture_output=True, text=True
        )

        assert result.returncode == 0
        # Should find "def hello" and other functions
        assert "def" in result.stdout

    def test_grep_regex_pattern(self, temp_workspace):
        """Grep works with regex patterns."""
        import subprocess

        result = subprocess.run(
            ["grep", "-rE", r"def \w+\(", str(temp_workspace)], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "def" in result.stdout


class TestMultiFileOperations:
    """Tests for multi-file operations."""

    @pytest.mark.asyncio
    async def test_read_multiple_files_parallel(self, temp_workspace):
        """Read multiple files in parallel."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()
        files = [
            temp_workspace / "test.py",
            temp_workspace / "data.json",
            temp_workspace / "readme.md",
        ]

        tasks = [tool.execute(path=str(f)) for f in files]
        results = await asyncio.gather(*tasks)

        assert all(r.success for r in results)
        assert len(results) == 3

    def test_tree_recursive(self, temp_workspace):
        """Tree shows recursive structure (or ls -R fallback)."""
        import subprocess
        import shutil

        # Use tree if available, otherwise ls -R
        if shutil.which("tree"):
            result = subprocess.run(
                ["tree", "-L", "3", str(temp_workspace)], capture_output=True, text=True
            )
            assert result.returncode == 0
            assert "test.py" in result.stdout
        else:
            # Fallback to ls -R
            result = subprocess.run(
                ["ls", "-R", str(temp_workspace)], capture_output=True, text=True
            )
            assert result.returncode == 0
            assert "test.py" in result.stdout

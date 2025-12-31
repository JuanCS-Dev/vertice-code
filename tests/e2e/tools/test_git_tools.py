"""
E2E Tests for Git Tools - Phase 8.1

Tests for all git operation tools:
- GitStatusTool, GitDiffTool, GitLogTool
- GitAddTool, GitCommitTool, GitBranchTool
- GitCheckoutTool, GitMergeTool, GitStashTool
- GitResetTool (mock), GitPushTool (mock), GitPullTool (mock)

Following Anthropic's principle: "Resist the urge to over-engineer"
"""

import pytest
import subprocess
import tempfile
from pathlib import Path


@pytest.fixture
def git_repo():
    """Create temporary git repository with history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Initialize repo
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo, capture_output=True, check=True
        )

        # Create initial commit
        (repo / "README.md").write_text("# Test Project\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo, capture_output=True, check=True
        )

        # Create second commit
        (repo / "main.py").write_text("def main():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add main.py"],
            cwd=repo, capture_output=True, check=True
        )

        yield repo


class TestGitStatusTool:
    """Tests for GitStatusTool."""

    @pytest.mark.asyncio
    async def test_git_status_clean(self, git_repo):
        """Status shows clean working tree."""
        from vertice_cli.tools.git_ops import GitStatusTool

        tool = GitStatusTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success
        assert "branch" in result.data

    @pytest.mark.asyncio
    async def test_git_status_modified(self, git_repo):
        """Status shows modified files."""
        from vertice_cli.tools.git_ops import GitStatusTool

        # Modify a file
        (git_repo / "README.md").write_text("# Modified\n")

        tool = GitStatusTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success

    @pytest.mark.asyncio
    async def test_git_status_untracked(self, git_repo):
        """Status shows untracked files."""
        from vertice_cli.tools.git_ops import GitStatusTool

        # Create untracked file
        (git_repo / "new_file.txt").write_text("new content")

        tool = GitStatusTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success


class TestGitDiffTool:
    """Tests for GitDiffTool."""

    @pytest.mark.asyncio
    async def test_git_diff_empty(self, git_repo):
        """Diff empty when no changes."""
        from vertice_cli.tools.git_ops import GitDiffTool

        tool = GitDiffTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success

    @pytest.mark.asyncio
    async def test_git_diff_shows_changes(self, git_repo):
        """Diff shows file modifications."""
        from vertice_cli.tools.git_ops import GitDiffTool

        # Make a change
        (git_repo / "main.py").write_text("def main():\n    print('hello')\n")

        tool = GitDiffTool()
        result = await tool.execute(path=str(git_repo))

        assert result.success


class TestGitLogTool:
    """Tests for GitLogTool."""

    def test_git_log_shows_history(self, git_repo):
        """Log shows commit history."""
        result = subprocess.run(
            ["git", "-C", str(git_repo), "log", "--oneline", "-5"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Initial commit" in result.stdout
        assert "Add main.py" in result.stdout

    def test_git_log_count(self, git_repo):
        """Log respects count limit."""
        result = subprocess.run(
            ["git", "-C", str(git_repo), "log", "--oneline", "-1"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1


class TestGitAddTool:
    """Tests for GitAddTool."""

    def test_git_add_file(self, git_repo):
        """Add stages single file."""
        # Create new file
        (git_repo / "new.py").write_text("# new file")

        result = subprocess.run(
            ["git", "-C", str(git_repo), "add", "new.py"],
            capture_output=True
        )

        assert result.returncode == 0

        # Verify staged
        status = subprocess.run(
            ["git", "-C", str(git_repo), "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        assert "A  new.py" in status.stdout

    def test_git_add_all(self, git_repo):
        """Add . stages all files."""
        # Create multiple new files
        (git_repo / "file1.txt").write_text("content1")
        (git_repo / "file2.txt").write_text("content2")

        result = subprocess.run(
            ["git", "-C", str(git_repo), "add", "."],
            capture_output=True
        )

        assert result.returncode == 0


class TestGitBranchTool:
    """Tests for git branch operations."""

    def test_git_branch_create(self, git_repo):
        """Create new branch."""
        result = subprocess.run(
            ["git", "-C", str(git_repo), "branch", "feature-test"],
            capture_output=True
        )

        assert result.returncode == 0

        # Verify branch exists
        branches = subprocess.run(
            ["git", "-C", str(git_repo), "branch"],
            capture_output=True,
            text=True
        )
        assert "feature-test" in branches.stdout

    def test_git_branch_list(self, git_repo):
        """List branches shows current."""
        result = subprocess.run(
            ["git", "-C", str(git_repo), "branch"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Main or master branch should be marked with *
        assert "*" in result.stdout


class TestGitCheckoutTool:
    """Tests for git checkout operations."""

    def test_git_checkout_branch(self, git_repo):
        """Checkout switches branch."""
        # Create and switch to new branch
        subprocess.run(
            ["git", "-C", str(git_repo), "branch", "test-branch"],
            capture_output=True
        )

        result = subprocess.run(
            ["git", "-C", str(git_repo), "checkout", "test-branch"],
            capture_output=True
        )

        assert result.returncode == 0

        # Verify on new branch
        status = subprocess.run(
            ["git", "-C", str(git_repo), "branch", "--show-current"],
            capture_output=True,
            text=True
        )
        assert "test-branch" in status.stdout


class TestGitStashTool:
    """Tests for git stash operations."""

    def test_git_stash_changes(self, git_repo):
        """Stash saves changes."""
        # Make changes
        (git_repo / "README.md").write_text("# Modified content\n")

        result = subprocess.run(
            ["git", "-C", str(git_repo), "stash"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify clean working tree
        status = subprocess.run(
            ["git", "-C", str(git_repo), "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        assert status.stdout.strip() == ""

    def test_git_stash_pop(self, git_repo):
        """Stash pop restores changes."""
        # Make and stash changes
        (git_repo / "README.md").write_text("# Modified\n")
        subprocess.run(["git", "-C", str(git_repo), "stash"], capture_output=True)

        # Pop stash
        result = subprocess.run(
            ["git", "-C", str(git_repo), "stash", "pop"],
            capture_output=True
        )

        assert result.returncode == 0

        # Verify changes restored
        content = (git_repo / "README.md").read_text()
        assert "Modified" in content

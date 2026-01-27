"""
Git Safety Module for MCP Server
Git command validation and security protocols

This module provides comprehensive safety validation for git operations
including branch protection, dangerous command detection, and secure execution.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class GitSafetyConfig:
    """Configuration for git safety protocols."""

    def __init__(self):
        self.protected_branches = ["main", "master", "develop", "production", "release"]
        self.dangerous_flags = ["--force", "-f", "--hard", "--no-verify", "--no-gpg-sign", "-i"]
        self.dangerous_commands = [
            "config",
            "push --force",
            "push -f",
            "reset --hard",
            "clean -fd",
            "checkout -f",
            "rebase -i",
            "filter-branch",
            "gc --prune",
        ]
        self.max_commit_message = 1_000_000

    def is_branch_protected(self, branch: str) -> bool:
        """Check if a branch is protected."""
        return branch.lower() in [b.lower() for b in self.protected_branches]


# Global safety configuration
_safety_config = GitSafetyConfig()


def validate_git_command(command: str) -> Tuple[bool, str]:
    """Validate a git command against safety protocols."""
    cmd_lower = command.lower()

    # Check dangerous commands
    for dangerous in _safety_config.dangerous_commands:
        if dangerous in cmd_lower:
            return False, f"Dangerous git command detected: {dangerous}"

    # Check dangerous flags
    for flag in _safety_config.dangerous_flags:
        if flag in command:
            return False, f"Dangerous git flag detected: {flag}"

    # Check commit message length (basic validation)
    if "commit" in cmd_lower and "-m" in command:
        # Extract message after -m
        parts = command.split("-m", 1)
        if len(parts) > 1:
            message = parts[1].strip().strip('"').strip("'")
            if len(message) > _safety_config.max_commit_message:
                return (
                    False,
                    f"Commit message too long: {len(message)} chars (max {_safety_config.max_commit_message})",
                )

    return True, "Command validated successfully"


def get_current_branch(path: str = ".") -> str:
    """Get current git branch."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except Exception as e:
        return "unknown"


def is_repo_clean(path: str = ".") -> bool:
    """Check if git repository is clean (no uncommitted changes)."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and not result.stdout.strip()
    except Exception as e:
        return False


def run_git_command(
    command: List[str], path: str = ".", timeout: int = 30
) -> Tuple[bool, str, str]:
    """
    Run a git command safely.

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        import subprocess

        # Validate command first
        cmd_str = " ".join(command)
        valid, reason = validate_git_command(cmd_str)
        if not valid:
            return False, "", reason

        logger.info(f"Running git command: {' '.join(command)}")

        result = subprocess.run(command, cwd=path, capture_output=True, text=True, timeout=timeout)

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", f"Git command timed out after {timeout}s"
    except Exception as e:
        logger.error(f"Git command error: {e}")
        return False, "", str(e)

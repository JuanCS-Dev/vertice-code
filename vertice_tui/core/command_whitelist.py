"""
Command Whitelist - Approved commands for safe execution.

Security-first command definitions for SafeCommandExecutor.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Dict, FrozenSet


class CommandCategory(Enum):
    """Categories of allowed commands."""
    TESTING = "testing"
    LINTING = "linting"
    GIT = "git"
    FILE_SYSTEM = "file_system"
    PACKAGE = "package"
    SYSTEM_INFO = "system_info"


@dataclass(frozen=True)
class AllowedCommand:
    """
    Immutable definition of an allowed command.

    Attributes:
        name: Human-readable name for the command
        base_command: The executable (e.g., "pytest", "git")
        allowed_args: Frozenset of allowed argument patterns
        category: Command category for organization
        timeout_seconds: Maximum execution time
        description: What this command does
    """
    name: str
    base_command: str
    allowed_args: FrozenSet[str]
    category: CommandCategory
    timeout_seconds: int = 60
    description: str = ""


# Whitelist of allowed commands - IMMUTABLE
ALLOWED_COMMANDS: Dict[str, AllowedCommand] = {
    # Testing
    "pytest": AllowedCommand(
        name="pytest",
        base_command="pytest",
        allowed_args=frozenset({"-v", "-vv", "-x", "-s", "--tb=short", "--tb=long",
                                "--cov", "--cov-report=html", "--cov-report=xml",
                                "-k", "-m", "--lf", "--ff", "-n", "auto"}),
        category=CommandCategory.TESTING,
        timeout_seconds=300,
        description="Run pytest tests"
    ),
    "python -m pytest": AllowedCommand(
        name="python pytest",
        base_command="python",
        allowed_args=frozenset({"-m", "pytest", "-v", "-vv", "-x", "-s"}),
        category=CommandCategory.TESTING,
        timeout_seconds=300,
        description="Run pytest via python -m"
    ),

    # Linting
    "ruff check": AllowedCommand(
        name="ruff check",
        base_command="ruff",
        allowed_args=frozenset({"check", ".", "--fix", "--unsafe-fixes",
                                "--show-fixes", "--diff"}),
        category=CommandCategory.LINTING,
        timeout_seconds=120,
        description="Run ruff linter"
    ),
    "ruff format": AllowedCommand(
        name="ruff format",
        base_command="ruff",
        allowed_args=frozenset({"format", ".", "--check", "--diff"}),
        category=CommandCategory.LINTING,
        timeout_seconds=120,
        description="Run ruff formatter"
    ),
    "mypy": AllowedCommand(
        name="mypy",
        base_command="mypy",
        allowed_args=frozenset({".", "--strict", "--ignore-missing-imports",
                                "--show-error-codes", "--pretty"}),
        category=CommandCategory.LINTING,
        timeout_seconds=180,
        description="Run mypy type checker"
    ),
    "black": AllowedCommand(
        name="black",
        base_command="black",
        allowed_args=frozenset({".", "--check", "--diff", "--line-length", "100"}),
        category=CommandCategory.LINTING,
        timeout_seconds=120,
        description="Run black formatter"
    ),
    "bandit": AllowedCommand(
        name="bandit",
        base_command="bandit",
        allowed_args=frozenset({"-r", ".", "-c", "pyproject.toml", "-ll", "-ii"}),
        category=CommandCategory.LINTING,
        timeout_seconds=120,
        description="Run bandit security scanner"
    ),

    # Git (read-only operations)
    "git status": AllowedCommand(
        name="git status",
        base_command="git",
        allowed_args=frozenset({"status", "-s", "--short", "--branch"}),
        category=CommandCategory.GIT,
        timeout_seconds=30,
        description="Show git status"
    ),
    "git diff": AllowedCommand(
        name="git diff",
        base_command="git",
        allowed_args=frozenset({"diff", "--staged", "--cached", "--name-only",
                                "--stat", "HEAD", "HEAD~1"}),
        category=CommandCategory.GIT,
        timeout_seconds=60,
        description="Show git diff"
    ),
    "git log": AllowedCommand(
        name="git log",
        base_command="git",
        allowed_args=frozenset({"log", "--oneline", "-n", "10", "20", "5",
                                "--graph", "--all", "--decorate"}),
        category=CommandCategory.GIT,
        timeout_seconds=30,
        description="Show git log"
    ),
    "git branch": AllowedCommand(
        name="git branch",
        base_command="git",
        allowed_args=frozenset({"branch", "-a", "-v", "--list"}),
        category=CommandCategory.GIT,
        timeout_seconds=30,
        description="List git branches"
    ),

    # File system (read-only)
    "ls": AllowedCommand(
        name="ls",
        base_command="ls",
        allowed_args=frozenset({"-la", "-l", "-a", "-lh", "-R", "."}),
        category=CommandCategory.FILE_SYSTEM,
        timeout_seconds=30,
        description="List directory contents"
    ),
    "tree": AllowedCommand(
        name="tree",
        base_command="tree",
        allowed_args=frozenset({"-L", "1", "2", "3", "-d", "-I", "__pycache__"}),
        category=CommandCategory.FILE_SYSTEM,
        timeout_seconds=30,
        description="Show directory tree"
    ),
    "wc": AllowedCommand(
        name="wc",
        base_command="wc",
        allowed_args=frozenset({"-l", "-w", "-c"}),
        category=CommandCategory.FILE_SYSTEM,
        timeout_seconds=30,
        description="Count lines/words/chars"
    ),
    "du": AllowedCommand(
        name="du",
        base_command="du",
        allowed_args=frozenset({"-sh", "-h", "--max-depth=1", "."}),
        category=CommandCategory.FILE_SYSTEM,
        timeout_seconds=30,
        description="Show disk usage"
    ),

    # Package management (read-only)
    "pip list": AllowedCommand(
        name="pip list",
        base_command="pip",
        allowed_args=frozenset({"list", "--outdated", "--format=columns"}),
        category=CommandCategory.PACKAGE,
        timeout_seconds=60,
        description="List installed packages"
    ),
    "pip show": AllowedCommand(
        name="pip show",
        base_command="pip",
        allowed_args=frozenset({"show"}),
        category=CommandCategory.PACKAGE,
        timeout_seconds=30,
        description="Show package info"
    ),

    # System info
    "python --version": AllowedCommand(
        name="python version",
        base_command="python",
        allowed_args=frozenset({"--version", "-V"}),
        category=CommandCategory.SYSTEM_INFO,
        timeout_seconds=10,
        description="Show Python version"
    ),
    "uname": AllowedCommand(
        name="uname",
        base_command="uname",
        allowed_args=frozenset({"-a", "-s", "-r", "-m"}),
        category=CommandCategory.SYSTEM_INFO,
        timeout_seconds=10,
        description="Show system info"
    ),
    "pwd": AllowedCommand(
        name="pwd",
        base_command="pwd",
        allowed_args=frozenset(),
        category=CommandCategory.SYSTEM_INFO,
        timeout_seconds=10,
        description="Print working directory"
    ),
    "whoami": AllowedCommand(
        name="whoami",
        base_command="whoami",
        allowed_args=frozenset(),
        category=CommandCategory.SYSTEM_INFO,
        timeout_seconds=10,
        description="Show current user"
    ),
}


# Dangerous patterns that should NEVER execute
DANGEROUS_PATTERNS: FrozenSet[str] = frozenset({
    "rm ",
    "rmdir",
    "chmod",
    "chown",
    "sudo",
    "su ",
    "dd ",
    "mkfs",
    "fdisk",
    "kill",
    "pkill",
    "killall",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "eval",
    "exec",
    "source",
    "> /",
    ">> /",
    "| sh",
    "| bash",
    "| zsh",
    "curl | ",
    "wget | ",
    "$(",
    "`",
    "${",
    "&&",
    "||",
    ";",
    "\n",
    "\\n",
})

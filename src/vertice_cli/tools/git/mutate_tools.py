"""
Git Mutate Tools - Write Operations with Safety
================================================

Contains:
- GitCommitTool: Create commits with HEREDOC support
- GitPRCreateTool: Create GitHub PRs via gh CLI
- GitPushTool: Push changes to remote
- GitCheckoutTool: Checkout branches/commits
- GitBranchTool: Create/delete branches

All tools in this module modify the repository and include safety checks.

Author: JuanCS Dev
Date: 2025-11-27
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any, Dict, List

from vertice_cli.tools.base import Tool, ToolCategory, ToolResult
from vertice_cli.tools.git.safety import validate_commit_message
from vertice_cli.tools.git.inspect_tools import run_git_command

logger = logging.getLogger(__name__)


# =============================================================================
# GIT COMMIT TOOL
# =============================================================================


class GitCommitTool(Tool):
    """
    Create git commits with Claude Code conventions.

    Features:
    - Validates changes before commit
    - Adds Juan-Dev-Code signature
    - Respects safety protocols
    - Supports pre-commit hooks
    - Uses HEREDOC-style message passing for proper multi-line support
    """

    SIGNATURE = """

Generated with Juan-Dev-Code

Co-Authored-By: Juan-Dev-Code <noreply@juancs.dev>"""

    def __init__(self):
        super().__init__()
        self.name = "git_commit"
        self.category = ToolCategory.GIT
        self.description = "Create a git commit with Claude Code conventions"
        self.requires_approval = True
        self.parameters = {
            "message": {
                "type": "string",
                "description": "Commit message (without signature)",
                "required": True,
            },
            "files": {
                "type": "array",
                "description": "Files to stage (default: all modified)",
                "required": False,
            },
            "amend": {
                "type": "boolean",
                "description": "Amend previous commit (requires explicit permission)",
                "required": False,
            },
            "add_signature": {
                "type": "boolean",
                "description": "Add Juan-Dev-Code signature (default: True)",
                "required": False,
            },
        }

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Create git commit with HEREDOC support."""
        message = kwargs.get("message", "")
        files = kwargs.get("files", [])
        amend = kwargs.get("amend", False)
        add_signature = kwargs.get("add_signature", True)

        if not message:
            return ToolResult(success=False, error="Commit message is required")

        is_valid, reason = validate_commit_message(message)
        if not is_valid:
            return ToolResult(success=False, error=reason)

        try:
            if amend:
                author_check = await self._check_authorship()
                if not author_check["safe_to_amend"]:
                    return ToolResult(
                        success=False, error=f"Cannot amend: {author_check['reason']}"
                    )

            stage_result = await self._stage_files(files)
            if not stage_result.success:
                return stage_result

            diff_result = await run_git_command("diff", "--cached", "--quiet")
            if diff_result.success:
                return ToolResult(success=False, error="No changes staged for commit")

            full_message = self._build_commit_message(message, add_signature)
            commit_result = await self._run_git_commit_heredoc(full_message, amend)

            if not commit_result.success:
                if commit_result.error and "pre-commit" in commit_result.error.lower():
                    return ToolResult(
                        success=False,
                        error="Pre-commit hook modified files. Review changes and retry.",
                        data={"hook_triggered": True},
                    )
                return ToolResult(success=False, error=commit_result.error)

            hash_result = await run_git_command("rev-parse", "--short", "HEAD")
            commit_hash = hash_result.data.strip() if hash_result.success else "unknown"

            return ToolResult(
                success=True,
                data={
                    "commit": commit_hash,
                    "message": message[:100],
                    "amended": amend,
                    "files_committed": len(files) if files else "all staged",
                },
                metadata={"hash": commit_hash},
            )

        except Exception as e:
            logger.error(f"GitCommit error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _stage_files(self, files: List[str]) -> ToolResult:
        """Stage files for commit."""
        if files:
            for file in files:
                if ".." in file or file.startswith("/"):
                    return ToolResult(success=False, error=f"Invalid file path: {file}")
                stage_result = await run_git_command("add", file)
                if not stage_result.success:
                    return ToolResult(
                        success=False, error=f"Failed to stage {file}: {stage_result.error}"
                    )
        else:
            stage_result = await run_git_command("add", "-A")
            if not stage_result.success:
                return ToolResult(success=False, error=f"Failed to stage: {stage_result.error}")
        return ToolResult(success=True, data="Files staged")

    async def _run_git_commit_heredoc(self, message: str, amend: bool = False) -> ToolResult:
        try:
            args = ["git", "commit", "-F", "-"]
            if amend:
                args.append("--amend")

            result = subprocess.run(
                args,
                input=message,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return ToolResult(
                success=result.returncode == 0,
                data=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Git commit timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _check_authorship(self) -> Dict[str, Any]:
        result = await run_git_command("log", "-1", "--format=%an %ae")
        if not result.success:
            return {"safe_to_amend": False, "reason": "Could not check authorship"}
        author = result.data.strip()

        status_result = await run_git_command("status", "-sb")
        if status_result.success and "ahead" not in status_result.data:
            return {"safe_to_amend": False, "reason": "Commit may already be pushed"}

        if "claude" in author.lower() or "juan" in author.lower() or "noreply@" in author.lower():
            return {"safe_to_amend": True, "reason": "Tool-authored commit"}

        return {
            "safe_to_amend": True,
            "reason": f"Unpushed commit by {author}",
            "warning": "Amending another developer's commit",
        }

    def _build_commit_message(self, message: str, add_signature: bool) -> str:
        if not add_signature:
            return message
        return message + self.SIGNATURE


# =============================================================================
# GIT PUSH TOOL
# =============================================================================


class GitPushTool(Tool):
    """Push changes to remote repository."""

    def __init__(self):
        super().__init__()
        self.name = "git_push"
        self.category = ToolCategory.GIT
        self.description = "Push changes to remote repository"
        self.requires_approval = True
        self.parameters = {
            "remote": {
                "type": "string",
                "description": "Remote name (default: origin)",
                "required": False,
            },
            "branch": {
                "type": "string",
                "description": "Branch name (default: current)",
                "required": False,
            },
            "force": {
                "type": "boolean",
                "description": "Force push (requires admin approval)",
                "required": False,
            },
        }

    async def _execute_validated(self, **kwargs) -> ToolResult:
        remote = kwargs.get("remote", "origin")
        branch = kwargs.get("branch")
        force = kwargs.get("force", False)

        if not branch:
            # Get current branch
            res = await run_git_command("rev-parse", "--abbrev-ref", "HEAD")
            if not res.success:
                return ToolResult(success=False, error="Could not determine current branch")
            branch = res.data.strip()

        cmd = ["push", remote, branch]
        if force:
            cmd.append("--force")

        result = await run_git_command(*cmd)
        if not result.success:
            return result

        return ToolResult(
            success=True,
            data=f"Pushed {branch} to {remote}",
            metadata={"remote": remote, "branch": branch},
        )


# =============================================================================
# GIT CHECKOUT TOOL
# =============================================================================


class GitCheckoutTool(Tool):
    """Switch branches or checkout commits."""

    def __init__(self):
        super().__init__()
        self.name = "git_checkout"
        self.category = ToolCategory.GIT
        self.description = "Switch branches or restore working tree files"
        self.requires_approval = True
        self.parameters = {
            "target": {
                "type": "string",
                "description": "Branch name, commit hash, or file path",
                "required": True,
            },
            "create_branch": {
                "type": "boolean",
                "description": "Create new branch (-b)",
                "required": False,
            },
        }

    async def _execute_validated(self, **kwargs) -> ToolResult:
        target = kwargs.get("target")
        create = kwargs.get("create_branch", False)

        if not target:
            return ToolResult(success=False, error="Target required")

        cmd = ["checkout"]
        if create:
            cmd.append("-b")
        cmd.append(target)

        result = await run_git_command(*cmd)
        if not result.success:
            return result

        return ToolResult(
            success=True,
            data=f"Checked out {target}",
            metadata={"target": target, "new_branch": create},
        )


# =============================================================================
# GIT BRANCH TOOL
# =============================================================================


class GitBranchTool(Tool):
    """Manage branches (list, create, delete)."""

    def __init__(self):
        super().__init__()
        self.name = "git_branch"
        self.category = ToolCategory.GIT
        self.description = "List, create, or delete branches"
        self.requires_approval = True
        self.parameters = {
            "action": {
                "type": "string",
                "description": "Action: list, create, delete",
                "enum": ["list", "create", "delete"],
                "required": True,
            },
            "name": {
                "type": "string",
                "description": "Branch name (required for create/delete)",
                "required": False,
            },
        }

    async def _execute_validated(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "list")
        name = kwargs.get("name")

        if action == "list":
            res = await run_git_command("branch", "--list")
            return res

        if not name:
            return ToolResult(success=False, error="Branch name required for create/delete")

        if action == "create":
            res = await run_git_command("branch", name)
            if res.success:
                return ToolResult(success=True, data=f"Created branch {name}")
            return res

        if action == "delete":
            # Safety check: prevent deleting main/master
            if name in ["main", "master", "dev"]:
                return ToolResult(success=False, error=f"Cannot delete protected branch: {name}")

            res = await run_git_command("branch", "-D", name)
            if res.success:
                return ToolResult(success=True, data=f"Deleted branch {name}")
            return res

        return ToolResult(success=False, error=f"Unknown action: {action}")


# =============================================================================
# PR CREATE TOOL
# =============================================================================


class GitPRCreateTool(Tool):
    """
    Create GitHub Pull Request using gh CLI.
    """

    SIGNATURE = "\n\nGenerated with Juan-Dev-Code"

    def __init__(self):
        super().__init__()
        self.name = "git_pr_create"
        self.category = ToolCategory.GIT
        self.description = "Create a GitHub Pull Request"
        self.requires_approval = True
        self.parameters = {
            "title": {"type": "string", "description": "PR title", "required": True},
            "body": {
                "type": "string",
                "description": "PR description (markdown)",
                "required": False,
            },
            "base": {
                "type": "string",
                "description": "Base branch (default: main)",
                "required": False,
            },
            "draft": {"type": "boolean", "description": "Create as draft PR", "required": False},
        }

    async def _execute_validated(self, **kwargs) -> ToolResult:
        """Create PR using gh CLI."""
        title = kwargs.get("title", "")
        body = kwargs.get("body", "")
        base = kwargs.get("base", "main")
        draft = kwargs.get("draft", False)

        if not title:
            return ToolResult(success=False, error="PR title is required")

        if len(title) > 256:
            return ToolResult(success=False, error="PR title too long (max 256 chars)")

        gh_check = await self._check_gh_cli()
        if not gh_check.success:
            return gh_check

        try:
            full_body = self._build_pr_body(body)
            args = [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body-file",
                "-",
                "--base",
                base,
            ]
            if draft:
                args.append("--draft")

            result = subprocess.run(
                args, input=full_body, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                return ToolResult(success=False, error=result.stderr)

            pr_url = result.stdout.strip()

            return ToolResult(
                success=True,
                data={
                    "url": pr_url,
                    "title": title,
                    "base": base,
                    "draft": draft,
                },
                metadata={"created": True},
            )

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="PR creation timed out")
        except Exception as e:
            logger.error(f"GitPRCreate error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _check_gh_cli(self) -> ToolResult:
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, timeout=10)
            if result.returncode != 0:
                return ToolResult(success=False, error="GitHub CLI (gh) not working properly")
            auth_result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=10)
            if auth_result.returncode != 0:
                return ToolResult(
                    success=False, error="GitHub CLI not authenticated. Run: gh auth login"
                )
            return ToolResult(success=True, data="gh CLI ready")
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error="GitHub CLI (gh) not found. Install from: https://cli.github.com",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _build_pr_body(self, body: str) -> str:
        if not body:
            return f"## Summary\n\n_No description provided._\n{self.SIGNATURE}"
        return body + self.SIGNATURE


def get_git_mutate_tools() -> List[Tool]:
    """Get all write git tools."""
    return [
        GitCommitTool(),
        GitPushTool(),
        GitCheckoutTool(),
        GitBranchTool(),
        GitPRCreateTool(),
    ]


__all__ = [
    "GitCommitTool",
    "GitPRCreateTool",
    "GitPushTool",
    "GitCheckoutTool",
    "GitBranchTool",
    "get_git_mutate_tools",
]

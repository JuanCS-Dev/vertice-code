#!/usr/bin/env python3
"""
GITHUB INTEGRATION REAL TESTS
============================

Testes reais usando GitHub CLI para validar integração completa.
"""

import asyncio
import subprocess
import json
import time
from pathlib import Path


class GitHubIntegrationTester:
    """Test GitHub integration using real CLI."""

    def __init__(self):
        self.test_repo = "vertice-code-test-2026"
        self.results = {"total_tests": 0, "passed": 0, "failed": 0, "details": []}

    def test_result(self, name: str, success: bool, details: str = ""):
        """Log test result."""
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
            status = "✅"
        else:
            self.results["failed"] += 1
            status = "❌"

        self.results["details"].append({"test": name, "status": status, "details": details})

        print(f"{status} {name}: {details}")

    def run_gh_command(self, cmd: list, description: str = "") -> tuple[bool, str]:
        """Run GitHub CLI command and return success status and output."""
        try:
            result = subprocess.run(["gh"] + cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            if description:
                print(f"  📋 {description}: {'✅' if success else '❌'}")
            return success, output.strip()
        except Exception as e:
            print(f"  💥 Command failed: {e}")
            return False, str(e)

    async def test_github_cli_auth(self):
        """Test GitHub CLI authentication."""
        success, output = self.run_gh_command(["auth", "status"], "Checking auth status")

        if success and "Logged in" in output:
            # Extract username
            for line in output.split("\n"):
                if "account" in line and "(" in line:
                    username = line.split("(")[1].split(")")[0]
                    self.test_result("GitHub CLI Auth", True, f"Authenticated as {username}")
                    return True

        self.test_result("GitHub CLI Auth", False, "Not authenticated or command failed")
        return False

    async def test_repo_creation(self):
        """Test repository creation."""
        success, output = self.run_gh_command(
            [
                "repo",
                "create",
                self.test_repo,
                "--public",
                "--description",
                "Test repo for Vertice-Code WebApp Evolution 2026",
            ],
            "Creating test repository",
        )

        if success or "already exists" in output:
            self.test_result("Repository Creation", True, f"Repo {self.test_repo} ready")
            return True
        else:
            self.test_result("Repository Creation", False, f"Failed: {output}")
            return False

    async def test_repo_operations(self):
        """Test basic repository operations."""
        # Test repo info
        success, output = self.run_gh_command(["repo", "view", self.test_repo], "Getting repo info")

        if success:
            self.test_result("Repository Info", True, "Repo info retrieved")
        else:
            self.test_result("Repository Info", False, f"Failed: {output}")
            return

        # Create a test file
        test_file = "test_integration.md"
        with open(test_file, "w") as f:
            f.write("# Vertice-Code Integration Test\n\nThis file tests GitHub integration.\n")

        # Add, commit and push
        success1, _ = self.run_gh_command(["add", test_file], "Staging file")
        success2, _ = self.run_gh_command(
            ["commit", "-m", "Add integration test file"], "Committing file"
        )
        success3, _ = self.run_gh_command(["push"], "Pushing to remote")

        if success1 and success2 and success3:
            self.test_result("Git Operations", True, "File committed and pushed")
        else:
            self.test_result("Git Operations", False, "Git operations failed")

        # Cleanup local file
        Path(test_file).unlink(missing_ok=True)

    async def test_webhook_simulation(self):
        """Simulate webhook payload and test processing."""
        # Create a mock push webhook payload
        webhook_payload = {
            "ref": "refs/heads/main",
            "before": "0000000000000000000000000000000000000000",
            "after": "abc123def456",
            "repository": {
                "id": 123456,
                "name": self.test_repo,
                "full_name": f"JuanCS-Dev/{self.test_repo}",
                "html_url": f"https://github.com/JuanCS-Dev/{self.test_repo}",
                "owner": {"login": "JuanCS-Dev"},
                "private": False,
            },
            "pusher": {"name": "JuanCS-Dev", "email": "test@example.com"},
            "commits": [
                {
                    "id": "abc123def456",
                    "message": "Add integration test file\n\nThis commit tests the webhook integration.",
                    "author": {"name": "JuanCS-Dev", "email": "test@example.com"},
                    "url": f"https://github.com/JuanCS-Dev/{self.test_repo}/commit/abc123def456",
                    "timestamp": "2026-01-09T15:00:00Z",
                }
            ],
        }

        # Test webhook processing logic (without actual HTTP)
        try:
            # Import webhook models
            from app.api.v1.webhooks import GitHubPushPayload, GitHubPRPayload

            # Validate payload structure
            push_data = GitHubPushPayload(**webhook_payload)
            self.test_result("Webhook Payload Validation", True, "Push payload validated")

            # Test PR payload structure
            pr_payload = {
                "action": "opened",
                "number": 1,
                "pull_request": {
                    "id": 123,
                    "number": 1,
                    "title": "Test PR",
                    "body": "This is a test PR",
                    "state": "open",
                    "merged": False,
                    "head": {"ref": "feature-branch"},
                    "base": {"ref": "main"},
                },
                "repository": webhook_payload["repository"],
                "sender": webhook_payload["pusher"],
            }

            pr_data = GitHubPRPayload(**pr_payload)
            self.test_result("PR Payload Validation", True, "PR payload validated")

        except Exception as e:
            self.test_result("Webhook Payload Validation", False, f"Validation failed: {e}")

    async def test_agent_functionality(self):
        """Test GitHub agent functionality."""
        try:
            from vertice_core.github_agent import GitHubAgent

            agent = GitHubAgent()
            self.test_result("GitHub Agent Creation", True, "Agent instantiated")

            # Test push analysis
            push_analysis = await agent.analyze_push(
                repo_full_name=f"JuanCS-Dev/{self.test_repo}",
                commits=[
                    {
                        "id": "test123",
                        "message": "Fix bug in authentication",
                        "author": {"name": "Test Author"},
                    }
                ],
                branch="main",
            )

            if "findings" in push_analysis and "recommendations" in push_analysis:
                self.test_result(
                    "Push Analysis",
                    True,
                    f"Analysis complete: {len(push_analysis['findings'])} findings",
                )
            else:
                self.test_result("Push Analysis", False, "Analysis structure incorrect")

            # Test PR review
            pr_review = await agent.review_pull_request(
                repo_full_name=f"JuanCS-Dev/{self.test_repo}",
                pr_number=1,
                title="Add new feature",
                body="This PR adds a new feature with proper tests and documentation.",
                author="contributor",
            )

            if "approved" in pr_review and "comments" in pr_review:
                self.test_result(
                    "PR Review",
                    True,
                    f"Review complete: {'Approved' if pr_review['approved'] else 'Changes requested'}",
                )
            else:
                self.test_result("PR Review", False, "Review structure incorrect")

        except Exception as e:
            self.test_result("GitHub Agent Functionality", False, f"Agent test failed: {e}")

    async def cleanup_test_repo(self):
        """Clean up test repository."""
        success, output = self.run_gh_command(
            ["repo", "delete", self.test_repo, "--yes"], "Cleaning up test repository"
        )

        if success:
            self.test_result("Test Cleanup", True, f"Repository {self.test_repo} deleted")
        else:
            self.test_result("Test Cleanup", False, f"Cleanup failed: {output}")

    async def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 GITHUB INTEGRATION REAL TESTS")
        print("=" * 50)

        # Core tests
        if not await self.test_github_cli_auth():
            print("❌ Cannot proceed without GitHub CLI auth")
            return self.results

        await self.test_repo_creation()
        await self.test_repo_operations()
        await self.test_webhook_simulation()
        await self.test_agent_functionality()

        # Cleanup
        await self.cleanup_test_repo()

        # Final report
        print("\n" + "=" * 50)
        print("🎯 GITHUB INTEGRATION TEST REPORT")
        print("=" * 50)

        success_rate = (
            (self.results["passed"] / self.results["total_tests"]) * 100
            if self.results["total_tests"] > 0
            else 0
        )

        print(f"📊 Tests Executed: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(".1f")

        print(
            f"\n🏆 RESULTADO: {'EXCELENTE' if success_rate >= 95 else 'BOM' if success_rate >= 80 else 'NECESSITA ATENÇÃO'}"
        )

        # Detailed breakdown
        print("\n📋 BREAKDOWN:")
        for result in self.results["details"]:
            print(f"   {result['status']} {result['test']}: {result['details']}")

        # Save report
        report_file = "github_integration_real_test_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return self.results


if __name__ == "__main__":
    tester = GitHubIntegrationTester()
    asyncio.run(tester.run_all_tests())

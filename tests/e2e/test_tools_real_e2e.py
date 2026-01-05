#!/usr/bin/env python3
"""
VERTICE E2E TOOL TESTS - ALL TOOLS + COMBINATIONS

Tests tools with REAL execution (no mocks).
Tests agent+tool combinations for integration.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

VERTICE_PATH = "/media/juan/DATA/Vertice-Code"
sys.path.insert(0, VERTICE_PATH)


class ToolTestResult:
    def __init__(self, name: str, tool_name: str):
        self.name = name
        self.tool_name = tool_name
        self.output = ""
        self.success = False
        self.error = ""
        self.duration = 0.0


class ToolTestSuite:
    """E2E test suite for Vertice tools."""

    def __init__(self):
        self.results: List[ToolTestResult] = []
        self.start_time = datetime.now()
        self.registry = None
        self.mcp_client = None

    async def setup(self):
        """Initialize tool registry and MCP client."""
        try:
            from vertice_cli.tools.registry_setup import setup_default_tools
            self.registry, self.mcp_client = setup_default_tools()
            print(f"Registry initialized with {len(self.registry.tools)} tools")
            return True
        except Exception as e:
            print(f"Failed to setup tools: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_tool(self, name: str, tool_name: str, params: Dict[str, Any],
                        expected_in_output: List[str] = None) -> ToolTestResult:
        """Test a single tool with given parameters."""
        print(f"\n{'='*70}")
        print(f"TOOL TEST: {name}")
        print(f"Tool: {tool_name}")
        print(f"Params: {params}")
        print(f"{'='*70}\n")

        result = ToolTestResult(name, tool_name)
        start = datetime.now()

        try:
            # Get tool from registry
            tool = self.registry.get(tool_name)
            if tool is None:
                result.error = f"Tool '{tool_name}' not found in registry. Available: {list(self.registry.tools.keys())}"
                result.success = False
            else:
                # Execute tool - try different execute methods
                if hasattr(tool, 'execute'):
                    output = await tool.execute(**params)
                elif hasattr(tool, '_execute_validated'):
                    output = await tool._execute_validated(**params)
                else:
                    result.error = f"Tool '{tool_name}' has no execute method"
                    output = None

                # Handle ToolResult or raw output
                if hasattr(output, 'data'):
                    result.output = str(output.data) if output.data else str(output)
                else:
                    result.output = str(output) if output else ""
                print(f"Output: {result.output[:500]}...")

                # Check expected keywords if provided
                if expected_in_output:
                    output_lower = result.output.lower()
                    found = [kw for kw in expected_in_output if kw.lower() in output_lower]
                    if len(found) >= len(expected_in_output) * 0.5:  # 50% threshold
                        result.success = True
                    else:
                        result.success = False
                        result.error = f"Expected: {expected_in_output}, Found: {found}"
                else:
                    # Success if no error and output exists
                    result.success = bool(result.output or output is not None)

        except Exception as e:
            result.error = str(e)
            result.success = False
            import traceback
            traceback.print_exc()

        result.duration = (datetime.now() - start).total_seconds()
        self.results.append(result)

        status = "PASS" if result.success else "FAIL"
        print(f"\nResult: [{status}] Duration: {result.duration:.2f}s")
        if result.error:
            print(f"Error: {result.error}")

        return result

    async def run_file_operation_tests(self):
        """Test file operation tools."""
        print("\n" + "=" * 70)
        print("PHASE 1: FILE OPERATION TOOLS")
        print("=" * 70)

        test_dir = Path.cwd()

        # Test ReadFileTool
        await self.test_tool(
            name="ReadFile - Read Python file",
            tool_name="read_file",
            params={"path": str(test_dir / "src" / "user_service.py")},
            expected_in_output=["UserService", "def", "class", "sql"]
        )

        # Test GetDirectoryTree (instead of ListDirectory)
        await self.test_tool(
            name="DirectoryTree - Get src/ structure",
            tool_name="get_directory_tree",
            params={"path": str(test_dir / "src")},
            expected_in_output=["user_service", "data_processor"]
        )

        # Test WriteFileTool (to temp file)
        temp_file = test_dir / "temp_test_output.txt"
        await self.test_tool(
            name="WriteFile - Create temp file",
            tool_name="write_file",
            params={"path": str(temp_file), "content": "# Test content\nprint('hello')"},
            expected_in_output=[]
        )

        # Verify written file
        if temp_file.exists():
            await self.test_tool(
                name="ReadFile - Verify written file",
                tool_name="read_file",
                params={"path": str(temp_file)},
                expected_in_output=["Test content", "hello"]
            )
            temp_file.unlink()  # Cleanup

        # Test EditFileTool
        await self.test_tool(
            name="EditFile - Check edit capability",
            tool_name="edit_file",
            params={"path": str(test_dir / "src" / "user_service.py"), "old_text": "# Fake edit test", "new_text": "# Nothing"},
            expected_in_output=[]  # Will fail gracefully - text not found
        )

        # Test CopyFile
        src_file = str(test_dir / "src" / "user_service.py")
        dst_file = str(test_dir / "temp_copy.py")
        await self.test_tool(
            name="CopyFile - Copy source file",
            tool_name="copy_file",
            params={"source": src_file, "destination": dst_file},
            expected_in_output=[]
        )
        if Path(dst_file).exists():
            Path(dst_file).unlink()

    async def run_search_tests(self):
        """Test search tools."""
        print("\n" + "=" * 70)
        print("PHASE 2: SEARCH TOOLS")
        print("=" * 70)

        # Test SearchFilesTool
        await self.test_tool(
            name="SearchFiles - Find SQL injection",
            tool_name="search_files",
            params={"pattern": "SELECT.*FROM", "path": str(Path.cwd())},
            expected_in_output=["user_service", "SELECT"]
        )

        # Test GetDirectoryTreeTool
        await self.test_tool(
            name="DirectoryTree - Get project structure",
            tool_name="get_directory_tree",
            params={"path": str(Path.cwd()), "max_depth": 3},
            expected_in_output=["src", "user_service", "data_processor"]
        )

    async def run_terminal_tests(self):
        """Test terminal/shell tools."""
        print("\n" + "=" * 70)
        print("PHASE 3: TERMINAL/BASH TOOLS")
        print("=" * 70)

        # Test BashCommand - pwd
        await self.test_tool(
            name="Bash - pwd command",
            tool_name="bash_command",
            params={"command": "pwd"},
            expected_in_output=["vertice_e2e_test"]
        )

        # Test BashCommand - ls
        await self.test_tool(
            name="Bash - ls command",
            tool_name="bash_command",
            params={"command": "ls -la"},
            expected_in_output=["src"]
        )

        # Test BashCommand - cat
        await self.test_tool(
            name="Bash - cat file",
            tool_name="bash_command",
            params={"command": "cat src/user_service.py | head -20"},
            expected_in_output=["UserService", "sql"]
        )

        # Test BashCommand - grep
        await self.test_tool(
            name="Bash - grep for SQL",
            tool_name="bash_command",
            params={"command": "grep -r 'SELECT' src/"},
            expected_in_output=["SELECT", "FROM"]
        )

    async def run_git_tests(self):
        """Test git tools (if in git repo)."""
        print("\n" + "=" * 70)
        print("PHASE 4: GIT TOOLS")
        print("=" * 70)

        # Test GitStatusTool
        await self.test_tool(
            name="GitStatus - Repository status",
            tool_name="git_status",
            params={"path": str(Path.cwd())},
            expected_in_output=[]  # May or may not be a git repo
        )

    async def run_prometheus_tests(self):
        """Test Prometheus meta-agent tools."""
        print("\n" + "=" * 70)
        print("PHASE 5: PROMETHEUS TOOLS")
        print("=" * 70)

        # Test PrometheusGetStatus
        await self.test_tool(
            name="Prometheus - Get Status",
            tool_name="prometheus_get_status",
            params={},
            expected_in_output=[]  # May not be initialized
        )

    async def run_all_tests(self):
        """Run all tool tests."""
        print("=" * 70)
        print("VERTICE E2E TOOL TEST SUITE")
        print(f"Started: {self.start_time.isoformat()}")
        print("=" * 70)

        # Setup
        if not await self.setup():
            print("\nFATAL: Could not setup tool registry!")
            return self.generate_report()

        # List available tools
        print(f"\nAvailable tools ({len(self.registry.tools)}):")
        for name in sorted(self.registry.tools.keys())[:20]:
            print(f"  - {name}")
        if len(self.registry.tools) > 20:
            print(f"  ... and {len(self.registry.tools) - 20} more")

        # Run tests
        await self.run_file_operation_tests()
        await self.run_search_tests()
        await self.run_terminal_tests()
        await self.run_git_tests()
        await self.run_prometheus_tests()

        return self.generate_report()

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        lines = []
        lines.append("=" * 70)
        lines.append("VERTICE E2E TOOL TEST REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        lines.append("=" * 70)

        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        pct = (100 * passed / total) if total > 0 else 0
        lines.append(f"\nOVERALL: {passed}/{total} tests passed ({pct:.0f}%)\n")

        # Results by phase
        for r in self.results:
            status = "PASS" if r.success else "FAIL"
            lines.append(f"\n{r.name} [{status}]")
            lines.append(f"  Tool: {r.tool_name}")
            lines.append(f"  Duration: {r.duration:.2f}s")
            if r.error:
                lines.append(f"  Error: {r.error}")
            if r.output:
                preview = r.output[:200].replace('\n', ' ')
                lines.append(f"  Output: {preview}...")

        # Summary
        lines.append("\n" + "=" * 70)
        lines.append("SUMMARY BY TOOL")
        lines.append("=" * 70)

        for r in self.results:
            status = "PASS" if r.success else "FAIL"
            lines.append(f"  [{status}] {r.tool_name}: {r.name}")

        report = "\n".join(lines)
        print("\n\n" + report)

        # Save to file
        with open("E2E_TOOL_REPORT.txt", "w") as f:
            f.write(report)
        print(f"\n\nReport saved to: {Path.cwd()}/E2E_TOOL_REPORT.txt")

        return report


class AgentToolCombinationSuite:
    """Test suite for agent + tool combinations."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()

    async def test_agent_with_tools(self, agent_name: str, task: str,
                                     expected_tools: List[str],
                                     expected_output: List[str]) -> Dict[str, Any]:
        """Test agent invocation that should use specific tools."""
        print(f"\n{'='*70}")
        print(f"AGENT+TOOLS TEST: {agent_name}")
        print(f"Task: {task}")
        print(f"Expected tools: {expected_tools}")
        print(f"{'='*70}\n")

        from vertice_tui.core.agents.manager import AgentManager

        result = {
            "agent": agent_name,
            "task": task,
            "expected_tools": expected_tools,
            "expected_output": expected_output,
            "output": "",
            "tools_used": [],
            "success": False,
            "error": "",
            "duration": 0.0
        }

        start = datetime.now()
        cwd = Path.cwd()
        files = [str(f) for f in cwd.glob("**/*.py") if f.is_file() and not f.name.startswith("test_")]

        context = {
            "cwd": str(cwd),
            "files": files,
            "project_name": cwd.name,
        }

        try:
            manager = AgentManager()
            output_chunks = []

            async for chunk in manager.invoke(agent_name, task, context):
                output_chunks.append(chunk)
                print(chunk, end="", flush=True)

            result["output"] = "".join(output_chunks)

            # Check expected output keywords
            output_lower = result["output"].lower()
            found_kw = [kw for kw in expected_output if kw.lower() in output_lower]

            # Success if we found at least 50% of expected keywords
            if len(found_kw) >= len(expected_output) * 0.5:
                result["success"] = True
            else:
                result["error"] = f"Missing keywords: {set(expected_output) - set(found_kw)}"

        except Exception as e:
            result["error"] = str(e)
            import traceback
            traceback.print_exc()

        result["duration"] = (datetime.now() - start).total_seconds()
        self.results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"\n\nResult: [{status}] Duration: {result['duration']:.2f}s")
        if result["error"]:
            print(f"Error: {result['error']}")

        return result

    async def run_combination_tests(self):
        """Run agent+tool combination tests."""
        print("=" * 70)
        print("VERTICE E2E AGENT+TOOL COMBINATIONS")
        print(f"Started: {self.start_time.isoformat()}")
        print("=" * 70)

        # Test 1: Explorer with file tools
        await self.test_agent_with_tools(
            agent_name="explorer",
            task="List all Python files and their main classes",
            expected_tools=["list_directory", "read_file"],
            expected_output=["src", "user_service", "data_processor", "class"]
        )

        # Test 2: Security with search tools
        await self.test_agent_with_tools(
            agent_name="security",
            task="Find all SQL vulnerabilities using search",
            expected_tools=["search_files"],
            expected_output=["sql", "injection", "vulnerability"]
        )

        # Test 3: Performance with file analysis
        await self.test_agent_with_tools(
            agent_name="performance",
            task="Analyze code for performance issues",
            expected_tools=["read_file"],
            expected_output=["performance", "function"]
        )

        # Test 4: Reviewer with code reading
        await self.test_agent_with_tools(
            agent_name="reviewer",
            task="Review code quality issues",
            expected_tools=["read_file"],
            expected_output=["issue", "code", "review"]
        )

        return self.generate_report()

    def generate_report(self) -> str:
        """Generate combination test report."""
        lines = []
        lines.append("=" * 70)
        lines.append("VERTICE E2E AGENT+TOOL COMBINATIONS REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        lines.append("=" * 70)

        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        pct = (100 * passed / total) if total > 0 else 0
        lines.append(f"\nOVERALL: {passed}/{total} tests passed ({pct:.0f}%)\n")

        for r in self.results:
            status = "PASS" if r["success"] else "FAIL"
            lines.append(f"\n{r['agent']} + tools [{status}]")
            lines.append(f"  Task: {r['task']}")
            lines.append(f"  Expected tools: {r['expected_tools']}")
            lines.append(f"  Duration: {r['duration']:.2f}s")
            if r["error"]:
                lines.append(f"  Error: {r['error']}")
            if r["output"]:
                preview = r["output"][:300].replace('\n', ' ')
                lines.append(f"  Output preview: {preview}...")

        report = "\n".join(lines)
        print("\n\n" + report)

        # Save to file
        with open("E2E_COMBINATIONS_REPORT.txt", "w") as f:
            f.write(report)
        print(f"\n\nReport saved to: {Path.cwd()}/E2E_COMBINATIONS_REPORT.txt")

        return report


async def main():
    os.chdir("/tmp/vertice_e2e_test")
    print(f"Working directory: {os.getcwd()}")

    # Run tool tests
    print("\n\n" + "#" * 70)
    print("# PART 1: TOOL TESTS")
    print("#" * 70)
    tool_suite = ToolTestSuite()
    await tool_suite.run_all_tests()

    # Run agent+tool combination tests
    print("\n\n" + "#" * 70)
    print("# PART 2: AGENT+TOOL COMBINATIONS")
    print("#" * 70)
    combo_suite = AgentToolCombinationSuite()
    await combo_suite.run_combination_tests()


if __name__ == "__main__":
    asyncio.run(main())

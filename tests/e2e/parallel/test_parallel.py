"""
E2E Tests for Parallel Execution - Phase 8.4
Testing parallel execution of tools and agents.

Patterns tested:
- Parallel tool execution
- Parallel agent invocation
- Concurrent file operations
- Race condition handling
"""

import pytest
import asyncio
import tempfile
from pathlib import Path


class TestParallelToolExecution:
    """Test parallel execution of tools."""

    @pytest.mark.asyncio
    async def test_parallel_file_reads(self):
        """Test multiple file reads in parallel."""
        from vertice_core.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create multiple files
            files = []
            for i in range(10):
                f = workspace / f"file{i}.txt"
                f.write_text(f"Content of file {i}")
                files.append(f)

            tool = ReadFileTool()

            # Execute reads in parallel
            tasks = [tool.execute(path=str(f)) for f in files]
            results = await asyncio.gather(*tasks)

            assert all(r.success for r in results)
            assert len(results) == 10

            # Verify content matches
            for i, result in enumerate(results):
                assert f"Content of file {i}" in result.data["content"]

    @pytest.mark.asyncio
    async def test_parallel_file_writes(self):
        """Test multiple file writes in parallel."""
        from vertice_core.tools.file_ops import WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tool = WriteFileTool()

            # Execute writes in parallel
            tasks = []
            for i in range(10):
                path = str(workspace / f"output{i}.txt")
                content = f"Output content {i}"
                tasks.append(tool.execute(path=path, content=content))

            results = await asyncio.gather(*tasks)

            assert all(r.success for r in results)

            # Verify files exist and have correct content
            for i in range(10):
                f = workspace / f"output{i}.txt"
                assert f.exists()
                assert f.read_text() == f"Output content {i}"

    @pytest.mark.asyncio
    async def test_parallel_bash_commands(self):
        """Test multiple bash commands in parallel."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        commands = [
            "echo 'test1'",
            "echo 'test2'",
            "echo 'test3'",
            "pwd",
            "whoami",
        ]

        tasks = [tool.execute(command=cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)

        assert all(r.success for r in results)
        assert "test1" in results[0].data["stdout"]
        assert "test2" in results[1].data["stdout"]
        assert "test3" in results[2].data["stdout"]

    @pytest.mark.asyncio
    async def test_parallel_mixed_success_failure(self):
        """Test parallel execution with mixed success/failure."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create some files
            existing = workspace / "existing.txt"
            existing.write_text("I exist")

            tasks = [
                tool.execute(path=str(existing)),
                tool.execute(path="/nonexistent/file.txt"),
                tool.execute(path=str(existing)),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # First and third should succeed
            assert results[0].success
            assert not results[1].success
            assert results[2].success


class TestParallelAgentInvocation:
    """Test parallel agent invocations."""

    @pytest.mark.asyncio
    async def test_parallel_agent_status(self):
        """Test getting status from multiple agents in parallel."""
        from agents import coder, reviewer, architect, researcher, devops

        async def get_status(agent):
            return agent.get_status()

        tasks = [
            get_status(coder),
            get_status(reviewer),
            get_status(architect),
            get_status(researcher),
            get_status(devops),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all("name" in r for r in results)

        names = [r["name"] for r in results]
        assert "coder" in names
        assert "reviewer" in names
        assert "architect" in names
        assert "researcher" in names
        assert "devops" in names

    @pytest.mark.asyncio
    async def test_parallel_orchestrator_planning(self):
        """Test multiple orchestrators planning in parallel."""
        from agents import OrchestratorAgent

        orchestrators = [OrchestratorAgent() for _ in range(5)]

        requests = [
            "Write code for authentication",
            "Review security module",
            "Design API architecture",
            "Deploy to production",
            "Research best practices",
        ]

        tasks = [o.plan(r) for o, r in zip(orchestrators, requests)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(len(r) >= 1 for r in results)

    @pytest.mark.asyncio
    async def test_parallel_task_routing(self):
        """Test routing multiple tasks in parallel."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity

        orchestrator = OrchestratorAgent()

        tasks = [
            Task(id=f"route-{i}", description=desc, complexity=TaskComplexity.SIMPLE)
            for i, desc in enumerate(
                [
                    "Write code for API",
                    "Review security issues",
                    "Design architecture",
                    "Deploy to kubernetes",
                    "Research documentation",
                ]
            )
        ]

        routing_tasks = [orchestrator.route(t) for t in tasks]
        results = await asyncio.gather(*routing_tasks)

        assert len(results) == 5
        assert all(r is not None for r in results)


class TestConcurrencyPatterns:
    """Test various concurrency patterns."""

    @pytest.mark.asyncio
    async def test_semaphore_limited_concurrency(self):
        """Test limited concurrency with semaphore."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent

        async def limited_execute(cmd):
            async with semaphore:
                return await tool.execute(command=cmd)

        commands = [f"echo 'task{i}'" for i in range(10)]
        tasks = [limited_execute(cmd) for cmd in commands]

        results = await asyncio.gather(*tasks)
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in parallel execution."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        async def with_timeout(cmd, timeout=5):
            try:
                return await asyncio.wait_for(tool.execute(command=cmd), timeout=timeout)
            except asyncio.TimeoutError:
                return None

        commands = [
            "echo 'fast'",
            "echo 'also fast'",
        ]

        tasks = [with_timeout(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)

        # Fast commands should complete
        assert results[0] is not None and results[0].success
        assert results[1] is not None and results[1].success


class TestParallelPerformance:
    """Test parallel execution performance."""

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self):
        """Test that parallel is faster than sequential."""
        import time
        from vertice_core.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create test files
            for i in range(5):
                (workspace / f"perf{i}.txt").write_text(f"Content {i}")

            tool = ReadFileTool()
            files = [str(workspace / f"perf{i}.txt") for i in range(5)]

            # Sequential execution
            start_seq = time.time()
            for f in files:
                await tool.execute(path=f)
            seq_time = time.time() - start_seq

            # Parallel execution
            start_par = time.time()
            tasks = [tool.execute(path=f) for f in files]
            await asyncio.gather(*tasks)
            par_time = time.time() - start_par

            # Parallel should be faster (or at least not slower by much)
            # Allow some tolerance for overhead
            assert par_time <= seq_time * 1.5  # 50% tolerance


class TestRaceConditions:
    """Test race condition handling."""

    @pytest.mark.asyncio
    async def test_concurrent_writes_to_different_files(self):
        """Test concurrent writes to different files (should be safe)."""
        from vertice_core.tools.file_ops import WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tool = WriteFileTool()

            # Write to different files concurrently
            tasks = [
                tool.execute(path=str(workspace / f"unique{i}.txt"), content=f"Data {i}")
                for i in range(20)
            ]

            results = await asyncio.gather(*tasks)
            assert all(r.success for r in results)

            # Verify all files have correct content
            for i in range(20):
                content = (workspace / f"unique{i}.txt").read_text()
                assert content == f"Data {i}"

    @pytest.mark.asyncio
    async def test_concurrent_reads_same_file(self):
        """Test concurrent reads of the same file (should be safe)."""
        from vertice_core.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            test_file = workspace / "shared.txt"
            test_file.write_text("Shared content")

            tool = ReadFileTool()

            # Read same file concurrently
            tasks = [tool.execute(path=str(test_file)) for _ in range(10)]
            results = await asyncio.gather(*tasks)

            assert all(r.success for r in results)
            assert all("Shared content" in r.data["content"] for r in results)


class TestParallelErrorHandling:
    """Test error handling in parallel execution."""

    @pytest.mark.asyncio
    async def test_gather_with_return_exceptions(self):
        """Test gather with return_exceptions for graceful failure handling."""
        from vertice_core.tools.file_ops import ReadFileTool

        tool = ReadFileTool()

        tasks = [
            tool.execute(path="/nonexistent1.txt"),
            tool.execute(path="/nonexistent2.txt"),
            tool.execute(path="/nonexistent3.txt"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should fail but not raise
        assert len(results) == 3
        for r in results:
            if not isinstance(r, Exception):
                assert not r.success

    @pytest.mark.asyncio
    async def test_partial_failure_continues(self):
        """Test that partial failures don't stop other tasks."""
        from vertice_core.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        commands = [
            "echo 'success1'",
            "rm -rf /",  # This will be blocked
            "echo 'success2'",
        ]

        tasks = [tool.execute(command=cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # First and third should succeed
        assert results[0].success
        assert not results[1].success  # Blocked
        assert results[2].success


class TestAgentParallelCoordination:
    """Test parallel coordination between agents."""

    @pytest.mark.asyncio
    async def test_multiple_orchestrators_independent(self):
        """Test multiple independent orchestrator instances."""
        from agents import OrchestratorAgent

        # Create independent orchestrators
        o1 = OrchestratorAgent()
        o2 = OrchestratorAgent()
        o3 = OrchestratorAgent()

        # Execute in parallel
        tasks = [
            o1.plan("Task for o1"),
            o2.plan("Task for o2"),
            o3.plan("Task for o3"),
        ]

        results = await asyncio.gather(*tasks)

        # Each should have independent results
        assert len(results) == 3
        assert len(o1.handoffs) == 0
        assert len(o2.handoffs) == 0
        assert len(o3.handoffs) == 0

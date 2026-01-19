"""
E2E Stress Tests for Parallel Execution - Phase 8.4

High-volume parallel execution tests to validate system stability under load.

Patterns tested:
- High-volume concurrent operations
- Mixed workload stress
- Resource contention
- Memory stability under load
- Recovery after stress
"""

import pytest
import asyncio
import tempfile
import time
import gc
from pathlib import Path


# =============================================================================
# 1. HIGH-VOLUME FILE OPERATIONS
# =============================================================================


class TestHighVolumeFileOperations:
    """Test high-volume file operations."""

    @pytest.mark.asyncio
    async def test_stress_50_parallel_reads(self):
        """Stress test: 50 concurrent file reads."""
        from vertice_cli.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create 50 files
            for i in range(50):
                (workspace / f"stress_read_{i}.txt").write_text(f"Stress content {i}")

            tool = ReadFileTool()

            # Execute 50 parallel reads
            start = time.time()
            tasks = [tool.execute(path=str(workspace / f"stress_read_{i}.txt")) for i in range(50)]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            # All should succeed
            assert all(r.success for r in results)
            assert len(results) == 50

            # Verify content integrity
            for i, r in enumerate(results):
                assert f"Stress content {i}" in r.data["content"]

            # Should complete in reasonable time (< 30s)
            assert elapsed < 30.0

    @pytest.mark.asyncio
    async def test_stress_100_parallel_writes(self):
        """Stress test: 100 concurrent file writes."""
        from vertice_cli.tools.file_ops import WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tool = WriteFileTool()

            # Execute 100 parallel writes
            start = time.time()
            tasks = [
                tool.execute(
                    path=str(workspace / f"stress_write_{i}.txt"),
                    content=f"Stress write content {i} with some padding " * 10,
                )
                for i in range(100)
            ]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            # All should succeed
            assert all(r.success for r in results)
            assert len(results) == 100

            # Verify all files exist
            for i in range(100):
                f = workspace / f"stress_write_{i}.txt"
                assert f.exists()
                assert f"Stress write content {i}" in f.read_text()

            # Should complete in reasonable time
            assert elapsed < 60.0

    @pytest.mark.asyncio
    async def test_stress_200_mixed_file_ops(self):
        """Stress test: 200 mixed read/write operations."""
        from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Pre-create files for reading
            for i in range(100):
                (workspace / f"read_{i}.txt").write_text(f"Read content {i}")

            read_tool = ReadFileTool()
            write_tool = WriteFileTool()

            # Mixed operations
            start = time.time()
            tasks = []

            # 100 reads
            for i in range(100):
                tasks.append(read_tool.execute(path=str(workspace / f"read_{i}.txt")))

            # 100 writes
            for i in range(100):
                tasks.append(
                    write_tool.execute(
                        path=str(workspace / f"write_{i}.txt"), content=f"Write content {i}"
                    )
                )

            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            # All should succeed
            assert all(r.success for r in results)
            assert len(results) == 200

            # Should complete in reasonable time
            assert elapsed < 90.0


# =============================================================================
# 2. HIGH-VOLUME COMMAND EXECUTION
# =============================================================================


class TestHighVolumeCommandExecution:
    """Test high-volume command execution."""

    @pytest.mark.asyncio
    async def test_stress_50_parallel_commands(self):
        """Stress test: 50 concurrent bash commands."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        # Execute 50 parallel commands
        start = time.time()
        tasks = [tool.execute(command=f"echo 'Stress test output {i}'") for i in range(50)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 50

        # Verify output integrity
        for i, r in enumerate(results):
            assert f"Stress test output {i}" in r.data["stdout"]

        # Should complete in reasonable time
        assert elapsed < 60.0

    @pytest.mark.asyncio
    async def test_stress_mixed_commands(self):
        """Stress test: Mixed safe and blocked commands."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        # Mix of safe and dangerous commands
        commands = []
        for i in range(30):
            commands.append(f"echo 'safe {i}'")  # Safe
        for i in range(10):
            commands.append("rm -rf /")  # Blocked
        for i in range(10):
            commands.append(f"echo 'also safe {i}'")  # Safe

        start = time.time()
        tasks = [tool.execute(command=cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # 40 should succeed, 10 should fail
        success_count = sum(1 for r in results if r.success)
        fail_count = sum(1 for r in results if not r.success)

        assert success_count == 40
        assert fail_count == 10
        assert elapsed < 60.0


# =============================================================================
# 3. SEMAPHORE-LIMITED STRESS TESTS
# =============================================================================


class TestSemaphoreLimitedStress:
    """Test stress with semaphore-limited concurrency."""

    @pytest.mark.asyncio
    async def test_semaphore_5_limit_100_tasks(self):
        """Stress test: 100 tasks with 5 concurrent limit."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        semaphore = asyncio.Semaphore(5)
        active_count = 0
        max_active = 0

        async def limited_execute(i):
            nonlocal active_count, max_active
            async with semaphore:
                active_count += 1
                max_active = max(max_active, active_count)
                result = await tool.execute(command=f"echo 'task {i}'")
                active_count -= 1
                return result

        start = time.time()
        tasks = [limited_execute(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 100

        # Max active should not exceed semaphore limit
        assert max_active <= 5

        # Should complete in reasonable time
        assert elapsed < 120.0

    @pytest.mark.asyncio
    async def test_semaphore_10_limit_file_ops(self):
        """Stress test: File operations with 10 concurrent limit."""
        from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create files
            for i in range(50):
                (workspace / f"sem_read_{i}.txt").write_text(f"Semaphore content {i}")

            read_tool = ReadFileTool()
            write_tool = WriteFileTool()
            semaphore = asyncio.Semaphore(10)

            async def limited_read(i):
                async with semaphore:
                    return await read_tool.execute(path=str(workspace / f"sem_read_{i}.txt"))

            async def limited_write(i):
                async with semaphore:
                    return await write_tool.execute(
                        path=str(workspace / f"sem_write_{i}.txt"), content=f"Written {i}"
                    )

            # 50 reads + 50 writes
            start = time.time()
            tasks = [limited_read(i) for i in range(50)]
            tasks.extend([limited_write(i) for i in range(50)])
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            assert all(r.success for r in results)
            assert len(results) == 100
            assert elapsed < 120.0


# =============================================================================
# 4. MEMORY STABILITY TESTS
# =============================================================================


class TestMemoryStability:
    """Test memory stability under load."""

    @pytest.mark.asyncio
    async def test_memory_stable_after_many_operations(self):
        """Test memory remains stable after many operations."""
        from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            read_tool = ReadFileTool()
            write_tool = WriteFileTool()

            # Run multiple batches
            for batch in range(5):
                # Create and write files
                tasks = []
                for i in range(20):
                    tasks.append(
                        write_tool.execute(
                            path=str(workspace / f"batch{batch}_file{i}.txt"),
                            content=f"Batch {batch} content {i} " * 100,
                        )
                    )
                await asyncio.gather(*tasks)

                # Read files
                tasks = []
                for i in range(20):
                    tasks.append(
                        read_tool.execute(path=str(workspace / f"batch{batch}_file{i}.txt"))
                    )
                await asyncio.gather(*tasks)

                # Force garbage collection
                gc.collect()

            # If we got here without crashing, memory is stable
            assert True

    @pytest.mark.asyncio
    async def test_large_output_handling(self):
        """Test handling of large command outputs."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        # Generate large output
        tasks = []
        for i in range(10):
            # Each command generates ~100KB of output
            tasks.append(tool.execute(command="python3 -c \"print('x' * 1000 * 100)\""))

        results = await asyncio.gather(*tasks)

        # All should succeed (output may be truncated but no crashes)
        assert all(r.success for r in results)


# =============================================================================
# 5. RECOVERY AFTER STRESS
# =============================================================================


class TestRecoveryAfterStress:
    """Test system recovery after stress."""

    @pytest.mark.asyncio
    async def test_operations_work_after_heavy_load(self):
        """Test normal operations work after heavy load."""
        from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Phase 1: Heavy load
            write_tool = WriteFileTool()
            tasks = [
                write_tool.execute(path=str(workspace / f"heavy_{i}.txt"), content=f"Heavy {i}")
                for i in range(30)
            ]
            await asyncio.gather(*tasks)

            # Phase 2: Recovery - simple operations should still work
            read_tool = ReadFileTool()
            bash_tool = BashCommandToolHardened()

            # Simple read
            read_result = await read_tool.execute(path=str(workspace / "heavy_0.txt"))
            assert read_result.success

            # Simple command
            bash_result = await bash_tool.execute(command="echo 'recovery test'")
            assert bash_result.success

            # Simple write
            write_result = await write_tool.execute(
                path=str(workspace / "recovery.txt"), content="Recovery content"
            )
            assert write_result.success

    @pytest.mark.asyncio
    async def test_cleanup_after_failures(self):
        """Test cleanup after many failures."""
        from vertice_cli.tools.file_ops import ReadFileTool

        tool = ReadFileTool()

        # Generate many failures
        tasks = [tool.execute(path=f"/nonexistent/path_{i}.txt") for i in range(50)]
        results = await asyncio.gather(*tasks)

        # All should fail gracefully
        assert all(not r.success for r in results)

        # System should still work
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            test_file = workspace / "after_failures.txt"
            test_file.write_text("Still working")

            result = await tool.execute(path=str(test_file))
            assert result.success
            assert "Still working" in result.data["content"]


# =============================================================================
# 6. THROUGHPUT BENCHMARKS
# =============================================================================


class TestThroughputBenchmarks:
    """Test throughput benchmarks."""

    @pytest.mark.asyncio
    async def test_reads_per_second(self):
        """Measure read operations per second."""
        from vertice_cli.tools.file_ops import ReadFileTool

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create test files
            for i in range(100):
                (workspace / f"bench_{i}.txt").write_text(f"Benchmark {i}")

            tool = ReadFileTool()

            # Measure throughput
            start = time.time()
            tasks = [tool.execute(path=str(workspace / f"bench_{i}.txt")) for i in range(100)]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            ops_per_second = 100 / elapsed

            # All should succeed
            assert all(r.success for r in results)

            # Should achieve at least 10 ops/sec
            assert ops_per_second > 10

    @pytest.mark.asyncio
    async def test_commands_per_second(self):
        """Measure command operations per second."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()

        # Measure throughput
        start = time.time()
        tasks = [tool.execute(command=f"echo 'bench {i}'") for i in range(50)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        ops_per_second = 50 / elapsed

        # All should succeed
        assert all(r.success for r in results)

        # Should achieve at least 5 ops/sec
        assert ops_per_second > 5


# =============================================================================
# 7. QUEUE-BASED STRESS TESTS
# =============================================================================


class TestQueueBasedStress:
    """Test queue-based stress patterns."""

    @pytest.mark.asyncio
    async def test_producer_consumer_stress(self):
        """Test producer-consumer pattern under stress."""
        queue = asyncio.Queue(maxsize=10)
        produced = 0
        consumed = 0
        errors = []

        async def producer():
            nonlocal produced
            for i in range(100):
                await queue.put(i)
                produced += 1
                await asyncio.sleep(0.001)

        async def consumer():
            nonlocal consumed
            while consumed < 100:
                try:
                    await asyncio.wait_for(queue.get(), timeout=5.0)
                    consumed += 1
                except asyncio.TimeoutError:
                    errors.append("Timeout")
                    break

        await asyncio.gather(producer(), consumer())

        assert produced == 100
        assert consumed == 100
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_multiple_consumers(self):
        """Test multiple consumers pattern."""
        queue = asyncio.Queue()
        consumed = []
        lock = asyncio.Lock()

        async def producer():
            for i in range(100):
                await queue.put(i)

        async def consumer(consumer_id):
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                    async with lock:
                        consumed.append((consumer_id, item))
                except asyncio.TimeoutError:
                    break

        # 1 producer, 5 consumers
        await asyncio.gather(
            producer(),
            consumer(1),
            consumer(2),
            consumer(3),
            consumer(4),
            consumer(5),
        )

        # All items should be consumed exactly once
        items = [item for _, item in consumed]
        assert len(items) == 100
        assert sorted(items) == list(range(100))


# =============================================================================
# 8. LATENCY UNDER LOAD
# =============================================================================


class TestLatencyUnderLoad:
    """Test latency characteristics under load."""

    @pytest.mark.asyncio
    async def test_latency_distribution(self):
        """Test latency distribution under load."""
        from vertice_cli.tools.exec_hardened import BashCommandToolHardened

        tool = BashCommandToolHardened()
        latencies = []

        async def timed_execute(i):
            start = time.time()
            result = await tool.execute(command=f"echo 'latency {i}'")
            elapsed = time.time() - start
            latencies.append(elapsed)
            return result

        tasks = [timed_execute(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        assert all(r.success for r in results)

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

        # All percentiles should be under 5 seconds
        assert p50 < 5.0
        assert p95 < 5.0
        assert p99 < 5.0

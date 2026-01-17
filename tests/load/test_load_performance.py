"""
Load and Stress Testing for Vertice-Code System.

Tests system performance under various load conditions:
- Concurrent user simulations
- Memory usage monitoring
- Response time validation
- Resource utilization tracking
- System stability under stress
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    test_name: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    throughput_rps: float  # requests per second


class LoadTester:
    """Load testing framework for Vertice-Code components."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def run_concurrent_simulation(
        self,
        num_concurrent_users: int = 10,
        requests_per_user: int = 5,
        test_duration_seconds: int = 60,
    ) -> LoadTestResult:
        """
        Run concurrent user simulation test.

        Args:
            num_concurrent_users: Number of simulated concurrent users
            requests_per_user: Number of requests per user
            test_duration_seconds: Maximum test duration

        Returns:
            LoadTestResult with comprehensive metrics
        """
        print(
            f"🚀 Starting concurrent simulation: {num_concurrent_users} users, {requests_per_user} requests each"
        )

        start_time = time.time()
        all_response_times: List[float] = []
        successful_requests = 0
        failed_requests = 0

        async def simulate_user(user_id: int) -> List[float]:
            """Simulate a single user making requests."""
            user_response_times = []

            for request_id in range(requests_per_user):
                request_start = time.time()

                try:
                    # Simulate a system operation (replace with actual system calls)
                    await self._simulate_system_operation(user_id, request_id)
                    response_time = time.time() - request_start
                    user_response_times.append(response_time)

                except Exception as e:
                    failed_requests += 1
                    print(f"❌ User {user_id} request {request_id} failed: {e}")

            return user_response_times

        # Start all user simulations
        tasks = [simulate_user(i) for i in range(num_concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for result in results:
            if isinstance(result, list):
                all_response_times.extend(result)
                successful_requests += len(result)
            else:
                failed_requests += num_concurrent_users  # All requests from this user failed

        total_requests = successful_requests + failed_requests
        end_time = time.time()
        actual_duration = end_time - start_time

        # Calculate metrics
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[
                18
            ]  # 95th percentile
            p99_response_time = statistics.quantiles(all_response_times, n=100)[
                98
            ]  # 99th percentile
        else:
            avg_response_time = (
                min_response_time
            ) = max_response_time = p95_response_time = p99_response_time = 0.0

        # Resource usage
        memory_usage = self.process.memory_info().rss / (1024 * 1024)  # MB
        cpu_usage = self.process.cpu_percent(interval=0.1)

        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        throughput_rps = total_requests / actual_duration if actual_duration > 0 else 0

        return LoadTestResult(
            test_name="concurrent_user_simulation",
            duration=actual_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            error_rate=error_rate,
            throughput_rps=throughput_rps,
        )

    async def run_memory_stress_test(
        self, num_operations: int = 1000, operation_size_kb: int = 100
    ) -> LoadTestResult:
        """
        Test memory usage under stress.

        Args:
            num_operations: Number of memory-intensive operations
            operation_size_kb: Size of each operation in KB

        Returns:
            LoadTestResult with memory metrics
        """
        print(
            f"🧠 Starting memory stress test: {num_operations} operations, {operation_size_kb}KB each"
        )

        start_time = time.time()
        memory_objects = []
        successful_operations = 0
        failed_operations = 0

        # Initial memory measurement
        initial_memory = self.process.memory_info().rss / (1024 * 1024)

        try:
            for i in range(num_operations):
                try:
                    # Simulate memory-intensive operation
                    data = await self._simulate_memory_operation(operation_size_kb)
                    memory_objects.append(data)
                    successful_operations += 1

                    # Periodic cleanup to prevent unlimited growth
                    if i % 100 == 0:
                        # Keep only last 50 objects
                        memory_objects = memory_objects[-50:]

                except Exception as e:
                    failed_operations += 1
                    print(f"❌ Memory operation {i} failed: {e}")

        except Exception as e:
            print(f"💥 Memory stress test failed: {e}")
            failed_operations = num_operations - successful_operations

        end_time = time.time()
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        memory_increase = final_memory - initial_memory

        # Cleanup
        del memory_objects

        return LoadTestResult(
            test_name="memory_stress_test",
            duration=end_time - start_time,
            total_requests=num_operations,
            successful_requests=successful_operations,
            failed_requests=failed_operations,
            average_response_time=(end_time - start_time) / num_operations
            if num_operations > 0
            else 0,
            min_response_time=0.0,  # Not measured
            max_response_time=0.0,  # Not measured
            p95_response_time=0.0,  # Not measured
            p99_response_time=0.0,  # Not measured
            memory_usage_mb=final_memory,
            cpu_usage_percent=self.process.cpu_percent(interval=0.1),
            error_rate=(failed_operations / num_operations) * 100 if num_operations > 0 else 0,
            throughput_rps=num_operations / (end_time - start_time)
            if (end_time - start_time) > 0
            else 0,
        )

    async def run_endurance_test(
        self, duration_minutes: int = 5, concurrent_users: int = 5
    ) -> List[LoadTestResult]:
        """
        Run endurance test over extended period.

        Args:
            duration_minutes: Test duration in minutes
            concurrent_users: Number of concurrent users

        Returns:
            List of LoadTestResult for each minute
        """
        print(
            f"🏃 Starting endurance test: {duration_minutes} minutes, {concurrent_users} concurrent users"
        )

        results = []
        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            minute_start = time.time()

            # Run 1-minute load test
            result = await self.run_concurrent_simulation(
                num_concurrent_users=concurrent_users,
                requests_per_user=10,  # 10 requests per user per minute
                test_duration_seconds=60,
            )

            results.append(result)

            # Brief pause between minutes
            remaining_time = 60 - (time.time() - minute_start)
            if remaining_time > 0:
                await asyncio.sleep(min(remaining_time, 5))

        return results

    async def _simulate_system_operation(self, user_id: int, request_id: int) -> Dict[str, Any]:
        """Simulate a system operation for testing."""
        # Simulate various system operations with different characteristics
        operation_types = ["llm_request", "tool_execution", "file_operation", "search_query"]

        # Simulate processing time (realistic distribution)
        import random

        base_delay = random.uniform(0.1, 2.0)  # 100ms to 2s

        # Some operations are slower
        if random.random() < 0.1:  # 10% chance
            base_delay *= 3  # 3x slower for "complex" operations

        await asyncio.sleep(base_delay)

        return {
            "user_id": user_id,
            "request_id": request_id,
            "operation_type": random.choice(operation_types),
            "processing_time": base_delay,
            "success": random.random() > 0.05,  # 95% success rate
        }

    async def _simulate_memory_operation(self, size_kb: int) -> bytes:
        """Simulate memory-intensive operation."""
        # Create data of specified size
        size_bytes = size_kb * 1024
        data = os.urandom(size_bytes)

        # Simulate some processing
        await asyncio.sleep(0.01)

        return data

    def print_results(self, results: LoadTestResult | List[LoadTestResult]):
        """Print formatted test results."""
        if isinstance(results, list):
            print("\n📊 Endurance Test Results:")
            print("=" * 80)

            for i, result in enumerate(results):
                print(f"\nMinute {i + 1}:")
                self._print_single_result(result)
        else:
            print("\n📊 Load Test Results:")
            print("=" * 50)
            self._print_single_result(results)

    def _print_single_result(self, result: LoadTestResult):
        """Print a single test result."""
        print(f"Test: {result.test_name}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"Throughput: {result.throughput_rps:.2f} RPS")

        if result.average_response_time > 0:
            print(f"Average Response Time: {result.average_response_time:.3f}s")
            print(f"Min Response Time: {result.min_response_time:.3f}s")
            print(f"Max Response Time: {result.max_response_time:.3f}s")
            print(f"P95 Response Time: {result.p95_response_time:.3f}s")
            print(f"P99 Response Time: {result.p99_response_time:.3f}s")

        print(f"Memory Usage: {result.memory_usage_mb:.1f}MB")
        print(f"CPU Usage: {result.cpu_usage_percent:.1f}%")

        # Performance assessment
        self._assess_performance(result)

    def _assess_performance(self, result: LoadTestResult):
        """Assess performance based on thresholds."""
        assessments = []

        # Response time assessment
        if result.average_response_time > 5.0:
            assessments.append("❌ High average response time")
        elif result.average_response_time > 2.0:
            assessments.append("⚠️ Moderate response time")
        else:
            assessments.append("✅ Good response time")

        # Error rate assessment
        if result.error_rate > 5.0:
            assessments.append("❌ High error rate")
        elif result.error_rate > 1.0:
            assessments.append("⚠️ Moderate error rate")
        else:
            assessments.append("✅ Low error rate")

        # Throughput assessment
        if result.throughput_rps > 50:
            assessments.append("✅ High throughput")
        elif result.throughput_rps > 20:
            assessments.append("⚠️ Moderate throughput")
        else:
            assessments.append("❌ Low throughput")

        # Memory assessment
        if result.memory_usage_mb > 500:
            assessments.append("❌ High memory usage")
        elif result.memory_usage_mb > 200:
            assessments.append("⚠️ Moderate memory usage")
        else:
            assessments.append("✅ Good memory usage")

        print("Assessment:")
        for assessment in assessments:
            print(f"  {assessment}")


async def main():
    """Run comprehensive load tests."""
    tester = LoadTester()

    print("🚀 Starting Comprehensive Load Testing Suite")
    print("=" * 60)

    # Test 1: Concurrent user simulation
    print("\n1. Concurrent User Simulation")
    concurrent_result = await tester.run_concurrent_simulation(
        num_concurrent_users=5, requests_per_user=3, test_duration_seconds=10
    )
    tester.print_results(concurrent_result)

    # Test 2: Memory stress test
    print("\n2. Memory Stress Test")
    memory_result = await tester.run_memory_stress_test(num_operations=100, operation_size_kb=50)
    tester.print_results(memory_result)

    # Test 3: Quick endurance test (2 minutes)
    print("\n3. Endurance Test (2 minutes)")
    endurance_results = await tester.run_endurance_test(duration_minutes=2, concurrent_users=3)
    tester.print_results(endurance_results)

    print("\n🎉 Load Testing Suite Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

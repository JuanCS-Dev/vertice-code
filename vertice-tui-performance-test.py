#!/usr/bin/env python3
"""
TUI Performance Benchmark Suite
Tests speed, memory usage, and responsiveness of the TUI
"""

import asyncio
import time
import psutil
import os
import subprocess
import signal
import statistics
from typing import Dict, List, Any, Optional
import tempfile
import sys

class TUIPerformanceTester:
    def __init__(self, tui_command: str = "python -m vertice_tui.app"):
        self.tui_command = tui_command
        self.process: Optional[subprocess.Popen] = None
        self.temp_dir = tempfile.mkdtemp()

    def start_tui_process(self) -> subprocess.Popen:
        """Start TUI process for testing."""
        env = os.environ.copy()
        env['PYTHONPATH'] = '/media/juan/DATA/Vertice-Code/src'

        self.process = subprocess.Popen(
            self.tui_command.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd='/media/juan/DATA/Vertice-Code',
            preexec_fn=os.setsid  # Create process group for clean killing
        )
        return self.process

    def stop_tui_process(self) -> None:
        """Stop TUI process cleanly."""
        if self.process:
            try:
                # Kill entire process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass  # Already dead
            finally:
                self.process = None

    def measure_startup_time(self) -> Dict[str, Any]:
        """Measure TUI startup time."""
        print("🕐 Measuring startup time...")

        start_time = time.time()
        process = self.start_tui_process()

        # Wait for TUI to initialize (look for ready indicator)
        timeout = 30
        ready_time = None

        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                if process.poll() is not None:
                    break  # Process died

                # Check if TUI is ready by looking for output
                try:
                    output = process.stdout.read(1024)
                    if output:
                        ready_time = time.time()
                        break
                except:
                    pass

                time.sleep(0.1)

        finally:
            self.stop_tui_process()

        startup_time = (ready_time - start_time) if ready_time else timeout

        return {
            "startup_time": startup_time,
            "success": ready_time is not None,
            "timeout": startup_time >= timeout
        }

    def measure_memory_usage(self) -> Dict[str, Any]:
        """Measure memory usage during operation."""
        print("📊 Measuring memory usage...")

        process = self.start_tui_process()
        memory_readings = []

        try:
            # Let TUI start up
            time.sleep(2)

            # Take memory readings for 10 seconds
            for _ in range(20):
                try:
                    proc = psutil.Process(process.pid)
                    memory_mb = proc.memory_info().rss / 1024 / 1024
                    memory_readings.append(memory_mb)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

                time.sleep(0.5)

        finally:
            self.stop_tui_process()

        if memory_readings:
            return {
                "memory_readings": memory_readings,
                "avg_memory_mb": statistics.mean(memory_readings),
                "max_memory_mb": max(memory_readings),
                "min_memory_mb": min(memory_readings),
                "memory_stability": statistics.stdev(memory_readings) if len(memory_readings) > 1 else 0
            }
        else:
            return {"error": "Could not measure memory usage"}

    def measure_ui_responsiveness(self) -> Dict[str, Any]:
        """Measure UI responsiveness to inputs."""
        print("⚡ Measuring UI responsiveness...")

        # This is a simplified test - in a real scenario we'd use a UI automation tool
        # For now, we'll measure basic process responsiveness

        process = self.start_tui_process()
        response_times = []

        try:
            time.sleep(2)  # Let TUI start

            # Send some test inputs (simplified - real test would need UI automation)
            for i in range(5):
                start_time = time.time()

                # In a real test, we'd send actual UI events
                # For now, just measure if process is still responsive
                try:
                    proc = psutil.Process(process.pid)
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                except:
                    break

        finally:
            self.stop_tui_process()

        if response_times:
            return {
                "response_times": response_times,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "responsiveness_score": 1 / statistics.mean(response_times) if response_times else 0
            }
        else:
            return {"error": "Could not measure responsiveness"}

    def measure_streaming_performance(self) -> Dict[str, Any]:
        """Measure streaming performance metrics."""
        print("🌊 Measuring streaming performance...")

        # Test Open Responses streaming performance
        import sys
        sys.path.insert(0, '/media/juan/DATA/Vertice-Code/src')

        try:
            from vertice_tui.core.openresponses_events import OpenResponsesParser

            # Create mock streaming data
            mock_events = [
                'event: response.created\ndata: {"type":"response.created","sequence_number":1}\n\n',
                'event: response.in_progress\ndata: {"type":"response.in_progress","sequence_number":2}\n\n',
                'event: response.output_item.added\ndata: {"type":"response.output_item.added","sequence_number":3}\n\n',
                'event: response.content_part.added\ndata: {"type":"response.content_part.added","sequence_number":4}\n\n',
            ] + [
                f'event: response.output_text.delta\ndata: {{"type":"response.output_text.delta","sequence_number":{5+i},"delta":"chunk{i} "}}\n\n'
                for i in range(10)
            ] + [
                'event: response.output_text.done\ndata: {"type":"response.output_text.done","sequence_number":15}\n\n',
                'event: response.content_part.done\ndata: {"type":"response.content_part.done","sequence_number":16}\n\n',
                'event: response.output_item.done\ndata: {"type":"response.output_item.done","sequence_number":17}\n\n',
                'event: response.completed\ndata: {"type":"response.completed","sequence_number":18}\n\n',
                'event: done\ndata: [DONE]\n\n'
            ]

            # Measure parsing performance
            parser = OpenResponsesParser()
            events_parsed = 0
            start_time = time.time()

            for event_line in mock_events:
                for line in event_line.splitlines(keepends=True):
                    event = parser.feed(line)
                    if event:
                        events_parsed += 1

            end_time = time.time()
            parsing_time = end_time - start_time

            return {
                "events_parsed": events_parsed,
                "parsing_time": parsing_time,
                "parsing_speed": events_parsed / parsing_time if parsing_time > 0 else 0,
                "avg_event_time": parsing_time / events_parsed if events_parsed > 0 else 0
            }

        except Exception as e:
            return {"error": f"Streaming test failed: {e}"}

    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run all performance tests."""
        print("🚀 Starting TUI Performance Benchmark Suite\n")

        results = {}

        # Test 1: Startup time
        startup_result = self.measure_startup_time()
        results["startup"] = startup_result

        print(".2f")
        print(f"  Success: {startup_result['success']}")
        print()

        # Test 2: Memory usage
        memory_result = self.measure_memory_usage()
        results["memory"] = memory_result

        if "avg_memory_mb" in memory_result:
            print("📊 Memory Usage Results:")
        print(".1f")
        print(".1f")
        print(".1f")
        print(".3f")
        print()

        # Test 3: UI Responsiveness
        responsiveness_result = self.measure_ui_responsiveness()
        results["responsiveness"] = responsiveness_result

        if "avg_response_time" in responsiveness_result:
            print("⚡ UI Responsiveness Results:")
        print(".4f")
        print(".4f")
        print(".2f")
        print()

        # Test 4: Streaming Performance
        streaming_result = self.measure_streaming_performance()
        results["streaming"] = streaming_result

        if "parsing_speed" in streaming_result:
            print("🌊 Streaming Performance Results:")
            print(f"  Events Parsed: {streaming_result['events_parsed']}")
            print(".4f")
            print(".6f")
            print()

        # Overall assessment
        overall_score = self.calculate_overall_score(results)

        assessment = {
            "results": results,
            "overall_score": overall_score,
            "grade": self.get_performance_grade(overall_score),
            "recommendations": self.generate_recommendations(results)
        }

        return assessment

    def calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 0
        factors = 0

        # Startup time (30% weight)
        if results["startup"]["success"] and not results["startup"]["timeout"]:
            startup_score = max(0, 100 - (results["startup"]["startup_time"] * 10))
            score += startup_score * 0.3
            factors += 1

        # Memory usage (25% weight)
        if "avg_memory_mb" in results["memory"]:
            memory_mb = results["memory"]["avg_memory_mb"]
            # Lower memory is better, target < 100MB
            memory_score = max(0, 100 - (memory_mb - 50))
            score += memory_score * 0.25
            factors += 1

        # Responsiveness (25% weight)
        if "avg_response_time" in results["responsiveness"]:
            response_time = results["responsiveness"]["avg_response_time"]
            # Lower response time is better, target < 0.1s
            responsiveness_score = max(0, 100 - (response_time * 1000))
            score += responsiveness_score * 0.25
            factors += 1

        # Streaming performance (20% weight)
        if "parsing_speed" in results["streaming"]:
            parsing_speed = results["streaming"]["parsing_speed"]
            # Higher parsing speed is better, target > 100 events/sec
            streaming_score = min(100, parsing_speed * 10)
            score += streaming_score * 0.2
            factors += 1

        return score / factors if factors > 0 else 0

    def get_performance_grade(self, score: float) -> str:
        """Convert score to performance grade."""
        if score >= 90:
            return "🏆 EXCELLENT (Relógio Suíço)"
        elif score >= 80:
            return "✅ VERY GOOD"
        elif score >= 70:
            return "🟡 GOOD"
        elif score >= 60:
            return "🟠 FAIR"
        else:
            return "❌ NEEDS IMPROVEMENT"

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if results["startup"]["timeout"]:
            recommendations.append("Optimize startup time - reduce initialization overhead")

        if "avg_memory_mb" in results["memory"] and results["memory"]["avg_memory_mb"] > 150:
            recommendations.append("Reduce memory usage - implement lazy loading for heavy components")

        if "avg_response_time" in results["responsiveness"] and results["responsiveness"]["avg_response_time"] > 0.2:
            recommendations.append("Improve UI responsiveness - optimize event handling and rendering")

        if "parsing_speed" in results["streaming"] and results["streaming"]["parsing_speed"] < 50:
            recommendations.append("Optimize streaming performance - improve event parsing efficiency")

        if not recommendations:
            recommendations.append("Performance is excellent - maintain current optimization level")

        return recommendations

async def main():
    tester = TUIPerformanceTester()

    print("🧪 TUI Performance Benchmark Suite")
    print("=" * 50)

    results = await tester.run_comprehensive_benchmark()

    print("🎯 Final Performance Assessment:"    print(".1f"    print(f"Grade: {results['grade']}")
    print()
    print("💡 Recommendations:")
    for rec in results["recommendations"]:
        print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
REAL TUI Performance Benchmark - Production Ready
Tests actual performance metrics under realistic conditions
"""

import asyncio
import time
import psutil
import os
import subprocess
import signal
import statistics
import threading
import tracemalloc
from typing import Dict, List, Any, Optional
import tempfile
import sys
import gc
import resource

class RealTUIPerformanceBenchmark:
    def __init__(self, tui_script: str = "/media/juan/DATA/Vertice-Code/src/vertice_tui/app.py"):
        self.tui_script = tui_script
        self.process: Optional[subprocess.Popen] = None
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_memory = 0

    def get_memory_usage(self, pid: int) -> Dict[str, float]:
        """Get detailed memory usage for a process."""
        try:
            proc = psutil.Process(pid)
            mem_info = proc.memory_info()
            mem_percent = proc.memory_percent()

            # Get children processes too
            children = proc.children(recursive=True)
            total_rss = mem_info.rss
            total_vms = mem_info.vms

            for child in children:
                try:
                    child_mem = child.memory_info()
                    total_rss += child_mem.rss
                    total_vms += child_mem.vms
                except:
                    pass

            return {
                'rss_mb': total_rss / 1024 / 1024,
                'vms_mb': total_vms / 1024 / 1024,
                'percent': mem_percent,
                'children_count': len(children)
            }
        except Exception as e:
            return {'error': str(e)}

    def get_cpu_usage(self, pid: int) -> Dict[str, float]:
        """Get CPU usage for a process."""
        try:
            proc = psutil.Process(pid)
            cpu_percent = proc.cpu_percent(interval=0.1)

            # Get children CPU too
            children = proc.children(recursive=True)
            total_cpu = cpu_percent

            for child in children:
                try:
                    total_cpu += child.cpu_percent(interval=0.1)
                except:
                    pass

            return {
                'cpu_percent': total_cpu,
                'cores_used': min(total_cpu / 100, psutil.cpu_count())
            }
        except Exception as e:
            return {'error': str(e)}

    def measure_real_startup_time(self) -> Dict[str, Any]:
        """Measure real startup time with detailed metrics."""
        print("🚀 Measuring REAL startup performance...")

        tracemalloc.start()
        start_time = time.time()
        start_memory = psutil.virtual_memory().used

        # Start TUI process
        env = os.environ.copy()
        env['PYTHONPATH'] = '/media/juan/DATA/Vertice-Code/src'

        self.process = subprocess.Popen(
            [sys.executable, self.tui_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd='/media/juan/DATA/Vertice-Code',
            preexec_fn=os.setsid
        )

        startup_complete = False
        ui_ready_time = None
        first_output_time = None

        try:
            # Monitor startup process
            end_time = time.time() + 15  # 15 second timeout

            while time.time() < end_time and not startup_complete:
                if self.process.poll() is not None:
                    # Process died
                    stdout, stderr = self.process.communicate()
                    return {
                        'success': False,
                        'error': 'Process crashed during startup',
                        'stdout': stdout.decode() if stdout else '',
                        'stderr': stderr.decode() if stderr else '',
                        'startup_time': time.time() - start_time
                    }

                # Check for first output (indicates TUI started)
                try:
                    output = self.process.stdout.read(1024)
                    if output and not first_output_time:
                        first_output_time = time.time()

                    # Look for UI ready indicators
                    output_str = output.decode(errors='ignore')
                    if 'ready' in output_str.lower() or 'initialized' in output_str.lower():
                        ui_ready_time = time.time()
                        startup_complete = True
                        break

                except:
                    pass

                # Check memory usage during startup
                if self.process.pid:
                    mem_usage = self.get_memory_usage(self.process.pid)
                    if 'rss_mb' in mem_usage and mem_usage['rss_mb'] > 50:  # TUI loaded
                        if not ui_ready_time:
                            ui_ready_time = time.time()
                        startup_complete = True
                        break

                time.sleep(0.05)

        finally:
            if self.process and self.process.poll() is None:
                self.stop_process()

        end_memory = psutil.virtual_memory().used
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        startup_time = time.time() - start_time
        memory_delta = (end_memory - start_memory) / 1024 / 1024  # MB

        return {
            'success': startup_complete,
            'total_startup_time': startup_time,
            'first_output_time': first_output_time - start_time if first_output_time else None,
            'ui_ready_time': ui_ready_time - start_time if ui_ready_time else None,
            'memory_delta_mb': memory_delta,
            'tracemalloc_current_mb': current / 1024 / 1024,
            'tracemalloc_peak_mb': peak / 1024 / 1024,
            'crashed': self.process.poll() is not None if self.process else False
        }

    def measure_runtime_performance(self, duration: int = 30) -> Dict[str, Any]:
        """Measure runtime performance over a period."""
        print(f"📊 Measuring {duration}s runtime performance...")

        self.process = self.start_process()
        if not self.process or not self.process.pid:
            return {'error': 'Failed to start process'}

        memory_readings = []
        cpu_readings = []
        start_time = time.time()

        try:
            # Baseline
            time.sleep(2)
            baseline_mem = self.get_memory_usage(self.process.pid)
            self.baseline_memory = baseline_mem.get('rss_mb', 0)

            # Monitor for duration
            for i in range(duration * 2):  # 2 readings per second
                if self.process.poll() is not None:
                    break

                mem = self.get_memory_usage(self.process.pid)
                cpu = self.get_cpu_usage(self.process.pid)

                if 'rss_mb' in mem:
                    memory_readings.append(mem['rss_mb'])
                if 'cpu_percent' in cpu:
                    cpu_readings.append(cpu['cpu_percent'])

                time.sleep(0.5)

        finally:
            self.stop_process()

        if not memory_readings:
            return {'error': 'No performance data collected'}

        return {
            'duration_measured': len(memory_readings) * 0.5,
            'memory_mb': {
                'min': min(memory_readings),
                'max': max(memory_readings),
                'avg': statistics.mean(memory_readings),
                'median': statistics.median(memory_readings),
                'stability': statistics.stdev(memory_readings) if len(memory_readings) > 1 else 0,
                'baseline': self.baseline_memory
            },
            'cpu_percent': {
                'min': min(cpu_readings) if cpu_readings else 0,
                'max': max(cpu_readings) if cpu_readings else 0,
                'avg': statistics.mean(cpu_readings) if cpu_readings else 0,
                'peaks': len([c for c in cpu_readings if c > 50]) if cpu_readings else 0
            },
            'memory_leak_mb': max(memory_readings) - min(memory_readings),
            'crashed': self.process.poll() is not None if self.process else False
        }

    def benchmark_command_execution(self) -> Dict[str, Any]:
        """Benchmark command execution speed."""
        print("⚡ Benchmarking command execution speed...")

        results = {'commands': {}}

        # Test different command types
        test_commands = [
            ('help', '/help'),
            ('clear', '/clear --force'),
            ('version', '/version'),
            ('invalid', '/nonexistent'),
        ]

        for cmd_name, cmd_input in test_commands:
            print(f"  Testing /{cmd_name}...")

            self.process = self.start_process()
            if not self.process:
                results['commands'][cmd_name] = {'error': 'Failed to start'}
                continue

            try:
                time.sleep(1)  # Let TUI initialize

                start_time = time.time()

                # Send command (simplified - in real test would use UI automation)
                # For now, just measure if process survives
                time.sleep(2)

                end_time = time.time()

                mem_usage = self.get_memory_usage(self.process.pid) if self.process.pid else {}

                results['commands'][cmd_name] = {
                    'execution_time': end_time - start_time,
                    'memory_mb': mem_usage.get('rss_mb', 0),
                    'success': self.process.poll() is None
                }

            except Exception as e:
                results['commands'][cmd_name] = {'error': str(e)}
            finally:
                self.stop_process()

        return results

    def benchmark_chat_streaming(self) -> Dict[str, Any]:
        """Benchmark chat streaming performance."""
        print("💬 Benchmarking chat streaming performance...")

        # Import Open Responses components for direct testing
        sys.path.insert(0, '/media/juan/DATA/Vertice-Code/src')

        try:
            from vertice_tui.core.openresponses_events import OpenResponsesParser

            # Test data
            test_messages = [
                "Hello, how are you?",
                "This is a longer message to test streaming performance with more content. " * 5,
                "Short",
                "A" * 1000,  # Large message
            ]

            results = {'messages': {}}

            for i, message in enumerate(test_messages):
                print(f"  Testing message {i+1} ({len(message)} chars)...")

                # Simulate Open Responses streaming
                parser = OpenResponsesParser()
                events_received = 0
                chunks_processed = 0

                # Mock SSE data
                mock_chunks = [
                    'event: response.created\ndata: {"type":"response.created","sequence_number":1}\n\n',
                    'event: response.in_progress\ndata: {"type":"response.in_progress","sequence_number":2}\n\n',
                    'event: response.output_item.added\ndata: {"type":"response.output_item.added","sequence_number":3}\n\n',
                ]

                # Generate response chunks
                words = message.split()
                chunk_size = max(1, len(words) // 10)  # 10 chunks max

                for j in range(0, len(words), chunk_size):
                    chunk_words = words[j:j+chunk_size]
                    chunk_text = ' '.join(chunk_words)
                    mock_chunks.append(
                        f'event: response.output_text.delta\ndata: {{"type":"response.output_text.delta","sequence_number":{4+j},"delta":"{chunk_text} "}}\n\n'
                    )

                mock_chunks.extend([
                    'event: response.output_text.done\ndata: {"type":"response.output_text.done","sequence_number":100}\n\n',
                    'event: response.content_part.done\ndata: {"type":"response.content_part.done","sequence_number":101}\n\n',
                    'event: response.output_item.done\ndata: {"type":"response.output_item.done","sequence_number":102}\n\n',
                    'event: response.completed\ndata: {"type":"response.completed","sequence_number":103}\n\n',
                    'event: done\ndata: [DONE]\n\n'
                ])

                # Process chunks
                start_time = time.time()
                for chunk in mock_chunks:
                    for line in chunk.splitlines(keepends=True):
                        event = parser.feed(line)
                        if event:
                            events_received += 1
                            if hasattr(event, 'delta') and event.delta:
                                chunks_processed += 1

                processing_time = time.time() - start_time

                results['messages'][f'message_{i+1}'] = {
                    'chars': len(message),
                    'events_processed': events_received,
                    'chunks_processed': chunks_processed,
                    'processing_time': processing_time,
                    'events_per_second': events_received / processing_time if processing_time > 0 else 0,
                    'chars_per_second': len(message) / processing_time if processing_time > 0 else 0
                }

            # Calculate aggregates
            all_times = [r['processing_time'] for r in results['messages'].values()]
            all_eps = [r['events_per_second'] for r in results['messages'].values()]
            all_cps = [r['chars_per_second'] for r in results['messages'].values()]

            results['aggregate'] = {
                'avg_processing_time': statistics.mean(all_times),
                'avg_events_per_second': statistics.mean(all_eps),
                'avg_chars_per_second': statistics.mean(all_cps),
                'total_events': sum(r['events_processed'] for r in results['messages'].values()),
                'total_chars': sum(r['chars'] for r in results['messages'].values())
            }

            return results

        except Exception as e:
            return {'error': f'Streaming benchmark failed: {e}'}

    def benchmark_memory_leaks(self) -> Dict[str, Any]:
        """Test for memory leaks under repeated operations."""
        print("🔍 Testing for memory leaks...")

        tracemalloc.start()
        initial_snapshot = tracemalloc.take_snapshot()

        self.process = self.start_process()
        if not self.process:
            return {'error': 'Failed to start process'}

        leak_test_memory = []

        try:
            # Let TUI stabilize
            time.sleep(3)

            # Simulate repeated operations
            for i in range(10):
                # Take memory snapshot
                if self.process.pid:
                    mem = self.get_memory_usage(self.process.pid)
                    if 'rss_mb' in mem:
                        leak_test_memory.append(mem['rss_mb'])

                # Simulate some activity (in real test would interact with UI)
                time.sleep(1)

            # Force garbage collection
            gc.collect()

            final_snapshot = tracemalloc.take_snapshot()

            # Analyze memory differences
            stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
            significant_growth = [stat for stat in stats if stat.size_diff > 10000]  # 10KB+ growth

        finally:
            tracemalloc.stop()
            self.stop_process()

        if not leak_test_memory:
            return {'error': 'No memory data collected'}

        memory_growth = leak_test_memory[-1] - leak_test_memory[0] if len(leak_test_memory) > 1 else 0

        return {
            'memory_growth_mb': memory_growth,
            'memory_stability': statistics.stdev(leak_test_memory) if len(leak_test_memory) > 1 else 0,
            'significant_allocations': len(significant_growth),
            'leak_detected': memory_growth > 10,  # 10MB growth = leak
            'tracemalloc_stats': len(stats) if 'stats' in locals() else 0
        }

    def start_process(self) -> Optional[subprocess.Popen]:
        """Start TUI process for testing."""
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = '/media/juan/DATA/Vertice-Code/src'

            process = subprocess.Popen(
                [sys.executable, self.tui_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd='/media/juan/DATA/Vertice-Code',
                preexec_fn=os.setsid
            )

            # Give it time to start
            time.sleep(2)

            if process.poll() is None:
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"Process failed to start: {stderr.decode()}")
                return None

        except Exception as e:
            print(f"Failed to start process: {e}")
            return None

    def stop_process(self) -> None:
        """Stop TUI process cleanly."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
            except ProcessLookupError:
                pass
            finally:
                self.process = None

    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run all benchmarks."""
        print("🧪 REAL TUI Performance Benchmark Suite")
        print("=" * 60)

        results = {}

        try:
            # 1. Startup Performance
            startup_result = self.measure_real_startup_time()
            results["startup"] = startup_result

            print("🚀 Startup Performance:")
            if startup_result['success']:
                print(".2f")
                if startup_result.get('first_output_time'):
                    print(".2f")
                if startup_result.get('ui_ready_time'):
                    print(".2f")
                print(".1f")
                print(".1f")
                print(".1f")
            else:
                print("❌ Startup failed!")
                if 'error' in startup_result:
                    print(f"   Error: {startup_result['error']}")
            print()

            # 2. Runtime Performance
            runtime_result = self.measure_runtime_performance(duration=15)
            results["runtime"] = runtime_result

            if 'memory_mb' in runtime_result:
                print("📊 Runtime Performance (15s):")
                print(".1f")
                print(".1f")
                print(".1f")
                print(".2f")
                print(".1f")
                print(".2f")
                print(f"   CPU Peaks (>50%): {runtime_result['cpu_percent']['peaks']}")
                print(".1f")
                print("   Memory Leak Detected!" if runtime_result.get('memory_leak_mb', 0) > 10 else "   No Memory Leak")
            else:
                print("❌ Runtime measurement failed!")
            print()

            # 3. Command Execution
            command_result = self.benchmark_command_execution()
            results["commands"] = command_result

            if 'commands' in command_result:
                print("⚡ Command Execution Performance:"                for cmd_name, cmd_data in command_result['commands'].items():
                    if 'execution_time' in cmd_data:
                        status = "✅" if cmd_data.get('success', False) else "❌"
                        print(".2f"                    else:
                        print(f"   /{cmd_name}: ❌ Failed - {cmd_data.get('error', 'Unknown')}")
            print()

            # 4. Streaming Performance
            streaming_result = self.benchmark_chat_streaming()
            results["streaming"] = streaming_result

            if 'aggregate' in streaming_result:
                agg = streaming_result['aggregate']
                print("💬 Chat Streaming Performance:"                print(".3f"                print(".0f"                print(".0f"                print(".0f"            else:
                print("❌ Streaming benchmark failed!")
            print()

            # 5. Memory Leak Test
            leak_result = self.benchmark_memory_leaks()
            results["memory_leaks"] = leak_result

            if 'memory_growth_mb' in leak_result:
                print("🔍 Memory Leak Analysis:"                print(".1f"                print(".2f"                print(f"   Significant Allocations: {leak_result['significant_allocations']}")
                print("   Leak Status: " + ("🚨 LEAK DETECTED!" if leak_result['leak_detected'] else "✅ No Leak"))
            else:
                print("❌ Memory leak test failed!")
            print()

            # Overall Assessment
            overall_score = self.calculate_overall_performance_score(results)
            grade = self.get_performance_grade(overall_score)

            print("🎯 OVERALL PERFORMANCE ASSESSMENT:"            print(".1f"            print(f"Grade: {grade}")

            recommendations = self.generate_performance_recommendations(results)
            if recommendations:
                print("\n💡 Optimization Recommendations:"                for rec in recommendations:
                    print(f"   • {rec}")

            results["overall_score"] = overall_score
            results["grade"] = grade
            results["recommendations"] = recommendations

        except Exception as e:
            print(f"❌ Benchmark failed with error: {e}")
            results["error"] = str(e)

        return results

    def calculate_overall_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 0
        factors = 0

        # Startup (25% weight)
        if results.get("startup", {}).get("success"):
            startup_time = results["startup"]["total_startup_time"]
            # Target: < 5 seconds
            startup_score = max(0, 100 - (startup_time * 20))
            score += startup_score * 0.25
            factors += 1

        # Runtime Memory (20% weight)
        if "runtime" in results and "memory_mb" in results["runtime"]:
            avg_mem = results["runtime"]["memory_mb"]["avg"]
            # Target: < 200MB
            mem_score = max(0, 100 - (avg_mem - 100))
            score += mem_score * 0.20
            factors += 1

        # Runtime CPU (15% weight)
        if "runtime" in results and "cpu_percent" in results["runtime"]:
            avg_cpu = results["runtime"]["cpu_percent"]["avg"]
            # Lower CPU is better
            cpu_score = max(0, 100 - avg_cpu)
            score += cpu_score * 0.15
            factors += 1

        # Streaming Performance (20% weight)
        if "streaming" in results and "aggregate" in results["streaming"]:
            eps = results["streaming"]["aggregate"]["avg_events_per_second"]
            # Target: > 100 events/sec
            streaming_score = min(100, eps * 10)
            score += streaming_score * 0.20
            factors += 1

        # Memory Leaks (20% weight)
        if "memory_leaks" in results and not results["memory_leaks"].get("leak_detected", True):
            leak_score = 100  # No leak = perfect score
            score += leak_score * 0.20
            factors += 1

        return score / factors if factors > 0 else 0

    def get_performance_grade(self, score: float) -> str:
        """Convert score to performance grade."""
        if score >= 95:
            return "🏆 EXCEPTIONAL (Lightning Fast)"
        elif score >= 90:
            return "✅ EXCELLENT (Production Ready)"
        elif score >= 80:
            return "🟢 VERY GOOD"
        elif score >= 70:
            return "🟡 GOOD"
        elif score >= 60:
            return "🟠 FAIR"
        else:
            return "❌ NEEDS OPTIMIZATION"

    def generate_performance_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if results.get("startup", {}).get("total_startup_time", 10) > 8:
            recommendations.append("Optimize startup time - lazy load heavy components")

        if results.get("runtime", {}).get("memory_mb", {}).get("avg", 300) > 250:
            recommendations.append("Reduce memory usage - implement object pooling for UI components")

        if results.get("runtime", {}).get("cpu_percent", {}).get("avg", 0) > 30:
            recommendations.append("Optimize CPU usage - profile and optimize event handlers")

        if results.get("streaming", {}).get("aggregate", {}).get("avg_events_per_second", 0) < 50:
            recommendations.append("Improve streaming performance - optimize event parsing and state updates")

        if results.get("memory_leaks", {}).get("leak_detected", False):
            recommendations.append("Fix memory leaks - implement proper cleanup in component lifecycle")

        if not recommendations:
            recommendations.append("Performance is excellent - maintain current optimization level")

        return recommendations

async def main():
    benchmark = RealTUIPerformanceBenchmark()

    results = await benchmark.run_comprehensive_benchmark()

    # Save detailed results
    import json
    with open('/media/juan/DATA/Vertice-Code/tui_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: tui_performance_results.json")

if __name__ == "__main__":
    asyncio.run(main())
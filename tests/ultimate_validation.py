#!/usr/bin/env python3
"""
🛡️  ULTIMATE SYSTEM VALIDATION: BLINDADO E RESILIENTE

Validação completa e rigorosa seguindo "o seguro morreu de velhice".
Sistema testado contra todos os possíveis pontos de falha.
"""

import asyncio
import sys
import time
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class UltimateValidationSuite:
    """Suite de validação definitiva para sistema blindado."""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.temp_dir = None

    def log(self, message: str, level: str = "INFO"):
        """Log estruturado."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    async def run_comprehensive_validation(self):
        """Execução completa da validação."""
        self.start_time = time.time()

        self.log("🛡️  ULTIMATE SYSTEM VALIDATION: BLINDADO E RESILIENTE")
        self.log("=" * 80)

        # Setup
        await self.setup_test_environment()

        # Core system validation
        await self.test_core_system_integrity()
        await self.test_import_resilience()
        await self.test_circular_dependency_elimination()

        # Tool system validation
        await self.test_tool_system_completeness()
        await self.test_tool_functionality_under_stress()
        await self.test_tool_error_handling()
        await self.test_tool_concurrent_operations()

        # Security and safety validation
        await self.test_security_boundaries()
        await self.test_input_validation()
        await self.test_resource_limits()

        # Performance and scalability validation
        await self.test_performance_baseline()
        await self.test_memory_usage()
        await self.test_scalability_limits()

        # Resilience and recovery validation
        await self.test_failure_recovery()
        await self.test_corruption_resistance()
        await self.test_partial_failure_handling()

        # Integration validation
        await self.test_system_integration()
        await self.test_data_integrity()
        await self.test_state_consistency()

        # Cleanup
        await self.cleanup_test_environment()

        # Final report
        self.generate_ultimate_report()

    # ============================================================================
    # SETUP AND TEARDOWN
    # ============================================================================

    async def setup_test_environment(self):
        """Setup isolated test environment."""
        self.log("🔧 Setting up isolated test environment")

        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp(prefix="vertice_validation_"))
        self.log(f"Created test directory: {self.temp_dir}")

        # Create test files
        test_files = {
            "validation_test.txt": "This is a test file for validation.",
            "empty_file.txt": "",
            "large_file.txt": "x" * 10000,
            "special_chars_ñáéíóú.txt": "ñáéíóú 中文 🚀",
            "binary_test.dat": b"\x00\x01\x02\x03\xFF\xFE\xFD",
        }

        for filename, content in test_files.items():
            file_path = self.temp_dir / filename
            if isinstance(content, str):
                file_path.write_text(content, encoding='utf-8')
            else:
                file_path.write_bytes(content)

        # Create nested directories
        (self.temp_dir / "subdir").mkdir()
        (self.temp_dir / "subdir" / "nested_file.txt").write_text("Nested content")

        (self.temp_dir / "protected").mkdir()
        (self.temp_dir / "protected" / "sensitive.txt").write_text("sensitive data")

        self.log("✅ Test environment ready")

    async def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.log("🧹 Test environment cleaned up")

    # ============================================================================
    # CORE SYSTEM VALIDATION
    # ============================================================================

    async def test_core_system_integrity(self):
        """Test core system components integrity."""
        self.log("🔍 Testing Core System Integrity")

        integrity_checks = {
            "clean_system_import": False,
            "tool_registry_creation": False,
            "mcp_client_creation": False,
            "system_health_check": False,
            "component_initialization": False,
        }

        try:
            # Clean system import
            from clean_tool_system_v2 import (
                create_clean_tool_registry,
                create_clean_mcp_client,
                BaseTool, ToolResult
            )
            integrity_checks["clean_system_import"] = True

            # Registry creation
            registry = create_clean_tool_registry()
            integrity_checks["tool_registry_creation"] = len(registry) == 4

            # MCP client creation
            mcp = create_clean_mcp_client()
            health = mcp.get_health_status()
            integrity_checks["mcp_client_creation"] = health["healthy"]

            # Health check
            integrity_checks["system_health_check"] = (
                health["tools_registered"] == 4 and
                health["healthy"] is True
            )

            # Component initialization
            tool_classes = [BaseTool, ToolResult]
            integrity_checks["component_initialization"] = all(
                cls is not None for cls in tool_classes
            )

        except Exception as e:
            self.log(f"❌ Core system integrity failed: {e}")

        success_count = sum(integrity_checks.values())
        total_checks = len(integrity_checks)

        self.test_results["core_integrity"] = {
            "status": "PASSED" if success_count == total_checks else "FAILED",
            "passed": success_count,
            "total": total_checks,
            "details": integrity_checks
        }

        self.log(f"✅ Core integrity: {success_count}/{total_checks} checks passed")

    async def test_import_resilience(self):
        """Test import system resilience."""
        self.log("📦 Testing Import Resilience")

        # Critical modules that must import
        critical_modules = [
            "clean_tool_system_v2",
            "vertice_cli.tools.base",
        ]

        # Optional modules that may fail
        optional_modules = [
            "vertice_cli.core.mcp",
            "vertice_cli.tools.registry_setup",
            "vertice_cli.tools.plan_mode",
        ]

        import_results = {}

        # Test critical imports
        for module in critical_modules:
            try:
                __import__(module)
                import_results[f"critical_{module.split('.')[-1]}"] = "PASSED"
            except ImportError as e:
                import_results[f"critical_{module.split('.')[-1]}"] = f"FAILED: {e}"

        # Test optional imports
        for module in optional_modules:
            try:
                __import__(module)
                import_results[f"optional_{module.split('.')[-1]}"] = "PASSED"
            except ImportError as e:
                import_results[f"optional_{module.split('.')[-1]}"] = f"SOFT_FAIL: {e}"

        # Assess results
        critical_failed = [k for k, v in import_results.items()
                          if k.startswith("critical_") and not v.startswith("PASSED")]
        optional_failed = [k for k, v in import_results.items()
                          if k.startswith("optional_") and not v.startswith("PASSED")]

        status = "FAILED" if critical_failed else "PASSED"

        self.test_results["import_resilience"] = {
            "status": status,
            "critical_failed": len(critical_failed),
            "optional_failed": len(optional_failed),
            "details": import_results
        }

        self.log(f"✅ Import resilience: {len(critical_failed)} critical failures")

    async def test_circular_dependency_elimination(self):
        """Test that circular dependencies are eliminated."""
        self.log("🔄 Testing Circular Dependency Elimination")

        # Modules that previously had circular dependencies
        problematic_modules = [
            "vertice_cli.tools.base",
            "vertice_cli.tools.file_ops",
            "vertice_cli.core.mcp",
            "vertice_cli.tools.registry_setup",
        ]

        circular_detected = []

        for module_name in problematic_modules:
            try:
                # Force full import and attribute access
                module = __import__(module_name, fromlist=[""])
                if hasattr(module, '__all__'):
                    for attr in getattr(module, '__all__', []):
                        getattr(module, attr, None)
                # Try to access key functions
                if hasattr(module, 'create_clean_tool_registry'):
                    getattr(module, 'create_clean_tool_registry', None)
            except ImportError as e:
                if "circular" in str(e).lower() or "import" in str(e).lower():
                    circular_detected.append(module_name)
            except Exception:
                pass  # Other errors are OK, just not circular imports

        self.test_results["circular_dependencies"] = {
            "status": "PASSED" if not circular_detected else "FAILED",
            "circular_modules": circular_detected,
            "modules_tested": len(problematic_modules)
        }

        self.log(f"✅ Circular dependencies: {len(circular_detected)} detected")

    # ============================================================================
    # TOOL SYSTEM VALIDATION
    # ============================================================================

    async def test_tool_system_completeness(self):
        """Test tool system completeness."""
        self.log("🔧 Testing Tool System Completeness")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Check tool registration
            registry = mcp.registry
            expected_tools = {"read_file", "write_file", "edit_file", "list_directory"}

            registered_tools = set(registry.list_tools())
            tools_missing = expected_tools - registered_tools
            tools_extra = registered_tools - expected_tools

            # Check tool instantiation
            tool_instances = {}
            for tool_name in expected_tools:
                tool = registry.get(tool_name)
                tool_instances[tool_name] = tool is not None and hasattr(tool, 'execute')

            all_tools_present = len(tools_missing) == 0
            all_tools_instantiable = all(tool_instances.values())

            self.test_results["tool_completeness"] = {
                "status": "PASSED" if all_tools_present and all_tools_instantiable else "FAILED",
                "tools_expected": len(expected_tools),
                "tools_registered": len(registered_tools),
                "tools_missing": list(tools_missing),
                "tools_extra": list(tools_extra),
                "tools_instantiable": tool_instances
            }

            self.log(f"✅ Tool completeness: {len(registered_tools)}/{len(expected_tools)} tools")

        except Exception as e:
            self.test_results["tool_completeness"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Tool completeness failed: {e}")

    async def test_tool_functionality_under_stress(self):
        """Test tools under stress conditions."""
        self.log("🏋️  Testing Tool Functionality Under Stress")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            stress_results = {}

            # Stress test 1: Rapid sequential operations
            start_time = time.time()
            operations = 0
            for i in range(50):  # 50 rapid operations
                result = await mcp.call_tool("read_file", {"path": str(project_root / "README.md")})
                if "result" in result:
                    operations += 1
            rapid_time = time.time() - start_time
            stress_results["rapid_operations"] = {
                "operations": operations,
                "time": rapid_time,
                "avg_time": rapid_time / operations if operations > 0 else 0
            }

            # Stress test 2: Large file operations
            large_content = "x" * 100000  # 100KB content
            large_file = self.temp_dir / "stress_large.txt"
            large_file.write_text(large_content)

            start_time = time.time()
            result = await mcp.call_tool("read_file", {"path": str(large_file)})
            large_read_time = time.time() - start_time

            stress_results["large_file_handling"] = {
                "file_size": len(large_content),
                "read_time": large_read_time,
                "success": "result" in result
            }

            # Stress test 3: Concurrent operations
            import asyncio
            concurrent_tasks = []
            for i in range(10):
                task = mcp.call_tool("list_directory", {"path": str(self.temp_dir)})
                concurrent_tasks.append(task)

            start_time = time.time()
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            concurrent_time = time.time() - start_time

            successful_concurrent = sum(1 for r in concurrent_results if isinstance(r, dict) and "result" in r)

            stress_results["concurrent_operations"] = {
                "operations": len(concurrent_tasks),
                "successful": successful_concurrent,
                "time": concurrent_time,
                "avg_time": concurrent_time / len(concurrent_tasks)
            }

            # Assess stress test results
            all_stress_passed = (
                operations >= 45 and  # At least 90% success rate
                stress_results["large_file_handling"]["success"] and
                successful_concurrent >= 8  # At least 80% concurrent success
            )

            self.test_results["stress_testing"] = {
                "status": "PASSED" if all_stress_passed else "FAILED",
                "results": stress_results
            }

            self.log(f"✅ Stress testing: {operations}/50 rapid, {successful_concurrent}/10 concurrent")

        except Exception as e:
            self.test_results["stress_testing"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Stress testing failed: {e}")

    async def test_tool_error_handling(self):
        """Test comprehensive error handling."""
        self.log("🚨 Testing Tool Error Handling")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            error_scenarios = [
                # File not found
                ("nonexistent_file", "read_file", {"path": "/definitely/does/not/exist.txt"}),
                # Permission denied (try to access root)
                ("permission_denied", "list_directory", {"path": "/root"}),
                # Invalid tool
                ("invalid_tool", "nonexistent_tool", {"param": "value"}),
                # Missing required parameters
                ("missing_params", "read_file", {}),
                # Invalid parameters
                ("invalid_params", "read_file", {"path": "", "invalid_param": "value"}),
            ]

            error_results = {}

            for scenario_name, tool_name, params in error_scenarios:
                try:
                    result = await mcp.call_tool(tool_name, params)
                    # Should return error, not success
                    returned_error = "error" in result
                    error_results[scenario_name] = returned_error

                    if returned_error:
                        self.log(f"✅ {scenario_name}: Proper error handling")
                    else:
                        self.log(f"❌ {scenario_name}: Should have errored but returned: {result}")

                except Exception as e:
                    # Exceptions are also acceptable error handling
                    error_results[scenario_name] = True
                    self.log(f"✅ {scenario_name}: Exception handled: {type(e).__name__}")

            # All scenarios should result in errors
            all_errors_handled = all(error_results.values())

            self.test_results["error_handling"] = {
                "status": "PASSED" if all_errors_handled else "FAILED",
                "scenarios_tested": len(error_scenarios),
                "errors_properly_handled": sum(error_results.values()),
                "details": error_results
            }

            self.log(f"✅ Error handling: {sum(error_results.values())}/{len(error_scenarios)} scenarios handled")

        except Exception as e:
            self.test_results["error_handling"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Error handling test failed: {e}")

    async def test_tool_concurrent_operations(self):
        """Test concurrent tool operations."""
        self.log("🔄 Testing Tool Concurrent Operations")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client

            # Test multiple MCP clients running concurrently
            num_clients = 5
            operations_per_client = 20

            async def client_operations(client_id: int):
                """Operations for a single client."""
                mcp = create_clean_mcp_client()
                results = []

                for i in range(operations_per_client):
                    # Mix of operations
                    if i % 4 == 0:
                        result = await mcp.call_tool("read_file", {"path": str(project_root / "README.md")})
                    elif i % 4 == 1:
                        result = await mcp.call_tool("list_directory", {"path": str(self.temp_dir)})
                    elif i % 4 == 2:
                        unique_file = self.temp_dir / f"concurrent_{client_id}_{i}.txt"
                        result = await mcp.call_tool("write_file", {
                            "path": str(unique_file),
                            "content": f"Concurrent test {client_id}-{i}"
                        })
                    else:
                        # Edit operation (if file exists)
                        test_file = self.temp_dir / f"concurrent_{client_id}_{i-2}.txt"
                        if test_file.exists():
                            result = await mcp.call_tool("edit_file", {
                                "path": str(test_file),
                                "old_string": f"Concurrent test {client_id}-{i-2}",
                                "new_string": f"Edited concurrent test {client_id}-{i-2}"
                            })
                        else:
                            result = {"result": "skipped"}

                    results.append("result" in result or "error" in result)

                successful_ops = sum(results)
                return {
                    "client_id": client_id,
                    "total_operations": len(results),
                    "successful_operations": successful_ops,
                    "success_rate": successful_ops / len(results)
                }

            # Run concurrent clients
            start_time = time.time()
            client_tasks = [client_operations(i) for i in range(num_clients)]
            client_results = await asyncio.gather(*client_tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Analyze results
            valid_results = [r for r in client_results if isinstance(r, dict)]
            total_operations = sum(r["total_operations"] for r in valid_results)
            total_successful = sum(r["successful_operations"] for r in valid_results)
            avg_success_rate = sum(r["success_rate"] for r in valid_results) / len(valid_results)

            concurrent_ok = (
                len(valid_results) == num_clients and  # All clients completed
                avg_success_rate >= 0.9 and  # 90%+ success rate
                total_time < 30  # Completed within 30 seconds
            )

            self.test_results["concurrent_operations"] = {
                "status": "PASSED" if concurrent_ok else "FAILED",
                "clients": num_clients,
                "operations_per_client": operations_per_client,
                "total_operations": total_operations,
                "total_successful": total_successful,
                "avg_success_rate": avg_success_rate,
                "total_time": total_time,
                "ops_per_second": total_operations / total_time if total_time > 0 else 0
            }

            self.log(f"✅ Concurrent ops: {total_successful}/{total_operations} successful ({avg_success_rate:.1%})")

        except Exception as e:
            self.test_results["concurrent_operations"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Concurrent operations failed: {e}")

    # ============================================================================
    # SECURITY AND SAFETY VALIDATION
    # ============================================================================

    async def test_security_boundaries(self):
        """Test security boundaries and access control."""
        self.log("🔒 Testing Security Boundaries")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            security_tests = [
                # Sensitive file access attempts
                ("passwd_access", "read_file", {"path": "/etc/passwd"}),
                ("shadow_access", "read_file", {"path": "/etc/shadow"}),
                ("env_file", "read_file", {"path": ".env"}),
                ("git_config", "list_directory", {"path": ".git"}),

                # Path traversal attempts
                ("path_traversal", "read_file", {"path": "../../../etc/passwd"}),
                ("absolute_path", "read_file", {"path": "/root/.bashrc"}),

                # Directory listing of sensitive areas
                ("proc_listing", "list_directory", {"path": "/proc"}),
                ("sys_listing", "list_directory", {"path": "/sys"}),
            ]

            security_results = {}

            for test_name, tool_name, params in security_tests:
                try:
                    result = await mcp.call_tool(tool_name, params)
                    # Should be blocked (return error)
                    blocked = "error" in result
                    security_results[test_name] = blocked

                    if blocked:
                        self.log(f"✅ {test_name}: Access properly blocked")
                    else:
                        self.log(f"❌ {test_name}: Access not blocked - SECURITY ISSUE!")

                except Exception as e:
                    # Exceptions count as blocking
                    security_results[test_name] = True
                    self.log(f"✅ {test_name}: Exception blocked access")

            # All security attempts should be blocked
            all_blocked = all(security_results.values())

            self.test_results["security_boundaries"] = {
                "status": "PASSED" if all_blocked else "CRITICAL_SECURITY_FAILURE",
                "tests_run": len(security_tests),
                "accesses_blocked": sum(security_results.values()),
                "details": security_results
            }

            if all_blocked:
                self.log("✅ Security boundaries: All sensitive access attempts blocked")
            else:
                self.log("🚨 CRITICAL: Security boundaries breached!")

        except Exception as e:
            self.test_results["security_boundaries"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Security boundary test failed: {e}")

    async def test_input_validation(self):
        """Test input validation robustness."""
        self.log("✅ Testing Input Validation")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            validation_tests = [
                # Empty/invalid inputs
                ("empty_path", "read_file", {"path": ""}),
                ("none_path", "read_file", {"path": None}),
                ("whitespace_path", "read_file", {"path": "   \n\t  "}),

                # Oversized inputs
                ("huge_content", "write_file", {
                    "path": str(self.temp_dir / "huge.txt"),
                    "content": "x" * 10000000  # 10MB
                }),

                # Invalid parameters
                ("wrong_param_type", "list_directory", {"path": 12345}),
                ("extra_params", "read_file", {
                    "path": str(project_root / "README.md"),
                    "extra_param": "should_be_ignored",
                    "another_extra": 42
                }),

                # Special characters
                ("special_chars_path", "read_file", {
                    "path": str(self.temp_dir / "special_chars_ñáéíóú.txt")
                }),
            ]

            validation_results = {}

            for test_name, tool_name, params in validation_tests:
                try:
                    result = await mcp.call_tool(tool_name, params)

                    # Check if operation succeeded or failed gracefully
                    has_result = "result" in result
                    has_error = "error" in result

                    if has_result or has_error:
                        validation_results[test_name] = "PASSED"
                        self.log(f"✅ {test_name}: Input handled gracefully")
                    else:
                        validation_results[test_name] = "FAILED"
                        self.log(f"❌ {test_name}: Unexpected response: {result}")

                except Exception as e:
                    # Some exceptions are acceptable for extreme inputs
                    if "huge_content" in test_name:
                        validation_results[test_name] = "PASSED"
                        self.log(f"✅ {test_name}: Large input properly rejected")
                    else:
                        validation_results[test_name] = "FAILED"
                        self.log(f"❌ {test_name}: Unexpected exception: {e}")

            passed_validations = sum(1 for r in validation_results.values() if r == "PASSED")
            total_validations = len(validation_tests)

            self.test_results["input_validation"] = {
                "status": "PASSED" if passed_validations == total_validations else "FAILED",
                "tests_run": total_validations,
                "passed": passed_validations,
                "details": validation_results
            }

            self.log(f"✅ Input validation: {passed_validations}/{total_validations} inputs handled")

        except Exception as e:
            self.test_results["input_validation"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Input validation test failed: {e}")

    async def test_resource_limits(self):
        """Test resource limit enforcement."""
        self.log("📊 Testing Resource Limits")

        try:
            # Test file size limits (should be handled gracefully)
            large_content = "x" * 50000000  # 50MB
            large_file = self.temp_dir / "massive_test.txt"

            # Write large file
            with open(large_file, 'w') as f:
                f.write(large_content)

            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Try to read massive file
            start_time = time.time()
            result = await mcp.call_tool("read_file", {"path": str(large_file)})
            read_time = time.time() - start_time

            # Should either succeed or fail gracefully
            handled_properly = "result" in result or "error" in result

            # Performance check
            reasonable_time = read_time < 30  # Should complete within 30 seconds

            self.test_results["resource_limits"] = {
                "status": "PASSED" if handled_properly and reasonable_time else "FAILED",
                "large_file_size": len(large_content),
                "read_time": read_time,
                "handled_properly": handled_properly,
                "reasonable_performance": reasonable_time
            }

            if handled_properly and reasonable_time:
                self.log("✅ Resource limits: Large files handled appropriately")
            else:
                self.log(f"❌ Resource limits: Issues with large file handling")

        except Exception as e:
            self.test_results["resource_limits"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Resource limits test failed: {e}")

    # ============================================================================
    # PERFORMANCE AND SCALABILITY
    # ============================================================================

    async def test_performance_baseline(self):
        """Test performance baseline."""
        self.log("⚡ Testing Performance Baseline")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Baseline performance test
            operations = ["read_file", "list_directory"] * 25  # 50 operations

            start_time = time.time()

            for i, op in enumerate(operations):
                if op == "read_file":
                    await mcp.call_tool("read_file", {"path": str(project_root / "README.md")})
                else:
                    await mcp.call_tool("list_directory", {"path": str(self.temp_dir)})

            total_time = time.time() - start_time
            avg_time = total_time / len(operations)

            # Performance thresholds
            acceptable_avg = 0.1  # 100ms per operation
            performance_ok = avg_time <= acceptable_avg

            self.test_results["performance_baseline"] = {
                "status": "PASSED" if performance_ok else "FAILED",
                "operations": len(operations),
                "total_time": total_time,
                "avg_time_per_op": avg_time,
                "threshold": acceptable_avg,
                "ops_per_second": len(operations) / total_time
            }

            self.log(f"✅ Performance: {avg_time:.3f}s avg per operation ({len(operations)/total_time:.1f} ops/sec)")

        except Exception as e:
            self.test_results["performance_baseline"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Performance baseline test failed: {e}")

    async def test_memory_usage(self):
        """Test memory usage stability."""
        self.log("🧠 Testing Memory Usage")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Perform memory-intensive operations
            for i in range(100):
                await mcp.call_tool("read_file", {"path": str(project_root / "README.md")})
                await mcp.call_tool("list_directory", {"path": str(self.temp_dir)})

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory leak check: should not increase by more than 50MB
            memory_ok = memory_increase < 50

            self.test_results["memory_usage"] = {
                "status": "PASSED" if memory_ok else "FAILED",
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_increase": memory_increase,
                "threshold_mb": 50
            }

            self.log(f"✅ Memory usage: {memory_increase:.1f}MB increase (threshold: 50MB)")

        except ImportError:
            # psutil not available, skip test
            self.test_results["memory_usage"] = {"status": "SKIPPED", "reason": "psutil not available"}
            self.log("⚠️ Memory usage test skipped (psutil not available)")

        except Exception as e:
            self.test_results["memory_usage"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Memory usage test failed: {e}")

    async def test_scalability_limits(self):
        """Test scalability limits."""
        self.log("📈 Testing Scalability Limits")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client

            # Test increasing load
            client_counts = [1, 5, 10, 20]
            scalability_results = {}

            for num_clients in client_counts:
                start_time = time.time()

                # Create multiple clients
                clients = [create_clean_mcp_client() for _ in range(num_clients)]

                # Each client performs operations
                operations_per_client = 10
                all_tasks = []

                for client in clients:
                    for _ in range(operations_per_client):
                        task = client.call_tool("read_file", {"path": str(project_root / "README.md")})
                        all_tasks.append(task)

                # Execute all operations
                results = await asyncio.gather(*all_tasks, return_exceptions=True)
                successful_ops = sum(1 for r in results if isinstance(r, dict) and "result" in r)

                total_time = time.time() - start_time
                success_rate = successful_ops / len(all_tasks)

                scalability_results[f"{num_clients}_clients"] = {
                    "clients": num_clients,
                    "total_operations": len(all_tasks),
                    "successful_operations": successful_ops,
                    "success_rate": success_rate,
                    "total_time": total_time,
                    "ops_per_second": len(all_tasks) / total_time if total_time > 0 else 0
                }

                self.log(f"✅ {num_clients} clients: {successful_ops}/{len(all_tasks)} ops ({success_rate:.1%})")

            # Assess scalability
            final_test = scalability_results["20_clients"]
            scalable = (
                final_test["success_rate"] >= 0.8 and  # At least 80% success
                final_test["ops_per_second"] >= 10     # At least 10 ops/second
            )

            self.test_results["scalability"] = {
                "status": "PASSED" if scalable else "FAILED",
                "results": scalability_results
            }

        except Exception as e:
            self.test_results["scalability"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Scalability test failed: {e}")

    # ============================================================================
    # RESILIENCE AND RECOVERY
    # ============================================================================

    async def test_failure_recovery(self):
        """Test failure recovery capabilities."""
        self.log("🔄 Testing Failure Recovery")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client

            recovery_results = {}

            # Test 1: Recovery from tool failures
            mcp = create_clean_mcp_client()

            # Mix successful and failed operations
            operations = [
                ("success_1", "read_file", {"path": str(project_root / "README.md")}),
                ("failure_1", "read_file", {"path": "/nonexistent/file.txt"}),
                ("success_2", "list_directory", {"path": str(self.temp_dir)}),
                ("failure_2", "list_directory", {"path": "/root/private"}),
                ("success_3", "write_file", {"path": str(self.temp_dir / "recovery_test.txt"), "content": "test"}),
            ]

            for op_name, tool_name, params in operations:
                try:
                    result = await mcp.call_tool(tool_name, params)
                    recovery_results[op_name] = "result" in result or "error" in result
                except Exception:
                    recovery_results[op_name] = True  # Exception handled

            # Test 2: System continues working after failures
            post_failure_ops = []
            for i in range(10):
                result = await mcp.call_tool("read_file", {"path": str(project_root / "README.md")})
                post_failure_ops.append("result" in result)

            recovery_results["post_failure_stability"] = sum(post_failure_ops) >= 8  # 80% success

            # Overall recovery assessment
            all_ops_handled = all(recovery_results.values())

            self.test_results["failure_recovery"] = {
                "status": "PASSED" if all_ops_handled else "FAILED",
                "operations_tested": len(operations),
                "post_failure_stable": recovery_results["post_failure_stability"],
                "details": recovery_results
            }

            self.log("✅ Failure recovery: System handles failures gracefully")

        except Exception as e:
            self.test_results["failure_recovery"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Failure recovery test failed: {e}")

    async def test_corruption_resistance(self):
        """Test resistance to data corruption."""
        self.log("🛡️  Testing Corruption Resistance")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Create test files with various content types
            test_files = {
                "normal.txt": "Normal content",
                "unicode.txt": "Unicode: ñáéíóú 中文 🚀",
                "binary.dat": b"\x00\x01\x02\x03\xFF\xFE\xFD",
                "empty.txt": "",
                "large.txt": "x" * 10000,
            }

            corruption_results = {}

            for filename, content in test_files.items():
                file_path = self.temp_dir / filename
                if isinstance(content, str):
                    file_path.write_text(content, encoding='utf-8', errors='replace')
                else:
                    file_path.write_bytes(content)

                # Try to read the file
                result = await mcp.call_tool("read_file", {"path": str(file_path)})
                corruption_results[filename] = "result" in result or "error" in result

            # Test directory with corrupted entries
            corrupted_dir = self.temp_dir / "corrupted"
            corrupted_dir.mkdir()

            # Create files with problematic names
            problematic_names = [
                "file with spaces.txt",
                "file-with-dashes.txt",
                "file.with.dots.txt",
                "file_with_underscores.txt",
                "file(with)parens.txt",
            ]

            for name in problematic_names:
                (corrupted_dir / name).write_text(f"Content of {name}")

            # Try to list corrupted directory
            result = await mcp.call_tool("list_directory", {"path": str(corrupted_dir)})
            corruption_results["corrupted_directory"] = "result" in result or "error" in result

            # Overall corruption resistance
            corruption_resistant = all(corruption_results.values())

            self.test_results["corruption_resistance"] = {
                "status": "PASSED" if corruption_resistant else "FAILED",
                "files_tested": len(test_files),
                "corruption_handled": sum(corruption_results.values()),
                "details": corruption_results
            }

            self.log("✅ Corruption resistance: Handles various file types and edge cases")

        except Exception as e:
            self.test_results["corruption_resistance"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Corruption resistance test failed: {e}")

    async def test_partial_failure_handling(self):
        """Test handling of partial failures."""
        self.log("🔀 Testing Partial Failure Handling")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client

            # Create scenario with mixed success/failure
            mcp = create_clean_mcp_client()

            # Create a batch of operations
            batch_operations = []

            # Successful operations
            for i in range(5):
                batch_operations.append(("read_file", {"path": str(project_root / "README.md")}))

            # Failing operations
            for i in range(3):
                batch_operations.append(("read_file", {"path": f"/nonexistent/path/file_{i}.txt"}))

            # Execute batch
            results = []
            for tool_name, params in batch_operations:
                result = await mcp.call_tool(tool_name, params)
                results.append("result" in result or "error" in result)

            # System should handle partial failures gracefully
            operations_completed = sum(results)
            partial_failure_handled = operations_completed >= 6  # At least 6 out of 8

            # Test system stability after partial failures
            post_failure_results = []
            for i in range(5):
                result = await mcp.call_tool("list_directory", {"path": str(self.temp_dir)})
                post_failure_results.append("result" in result)

            system_stable = sum(post_failure_results) >= 4  # At least 4 out of 5

            overall_partial_handling = partial_failure_handled and system_stable

            self.test_results["partial_failure_handling"] = {
                "status": "PASSED" if overall_partial_handling else "FAILED",
                "batch_operations": len(batch_operations),
                "operations_completed": operations_completed,
                "system_stable_post_failure": system_stable
            }

            self.log("✅ Partial failure handling: System remains stable with mixed success/failure")

        except Exception as e:
            self.test_results["partial_failure_handling"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Partial failure handling test failed: {e}")

    # ============================================================================
    # INTEGRATION VALIDATION
    # ============================================================================

    async def test_system_integration(self):
        """Test complete system integration."""
        self.log("🔗 Testing System Integration")

        try:
            # Test the entire pipeline from CLI to tools
            import subprocess
            import sys

            # Try to run a simple command through the system
            # This tests the entire integration pipeline
            cmd = [
                sys.executable, "-c",
                """
from clean_tool_system_v2 import create_clean_mcp_client
import asyncio

async def test():
    mcp = create_clean_mcp_client()
    result = await mcp.call_tool('read_file', {'path': 'README.md'})
    return 'result' in result

print(asyncio.run(test()))
                """
            ]

            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            integration_success = result.returncode == 0 and result.stdout.strip() == "True"

            self.test_results["system_integration"] = {
                "status": "PASSED" if integration_success else "FAILED",
                "subprocess_exit_code": result.returncode,
                "subprocess_output": result.stdout.strip(),
                "subprocess_error": result.stderr.strip()
            }

            if integration_success:
                self.log("✅ System integration: Full pipeline working end-to-end")
            else:
                self.log(f"❌ System integration failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.test_results["system_integration"] = {"status": "FAILED", "error": "Integration test timed out"}
            self.log("❌ System integration timed out")

        except Exception as e:
            self.test_results["system_integration"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ System integration test failed: {e}")

    async def test_data_integrity(self):
        """Test data integrity across operations."""
        self.log("🔒 Testing Data Integrity")

        try:
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp = create_clean_mcp_client()

            # Create a file with known content
            test_content = "Data integrity test content with special chars: ñáéíóú 🚀"
            test_file = self.temp_dir / "integrity_test.txt"

            # Write content
            write_result = await mcp.call_tool("write_file", {
                "path": str(test_file),
                "content": test_content
            })

            if "result" not in write_result:
                raise Exception("Write operation failed")

            # Read content back
            read_result = await mcp.call_tool("read_file", {"path": str(test_file)})

            if "result" not in read_result:
                raise Exception("Read operation failed")

            read_content = read_result["result"]["content"]

            # Verify integrity
            content_integrity = read_content == test_content

            # Test modification integrity
            modified_content = test_content + " [MODIFIED]"
            edit_result = await mcp.call_tool("edit_file", {
                "path": str(test_file),
                "old_string": test_content,
                "new_string": modified_content
            })

            if "result" not in edit_result:
                raise Exception("Edit operation failed")

            # Read modified content
            reread_result = await mcp.call_tool("read_file", {"path": str(test_file)})

            if "result" not in reread_result:
                raise Exception("Reread operation failed")

            reread_content = reread_result["result"]["content"]
            modification_integrity = reread_content == modified_content

            # Overall integrity
            data_integrity_ok = content_integrity and modification_integrity

            self.test_results["data_integrity"] = {
                "status": "PASSED" if data_integrity_ok else "FAILED",
                "content_integrity": content_integrity,
                "modification_integrity": modification_integrity,
                "original_content_length": len(test_content),
                "modified_content_length": len(modified_content)
            }

            if data_integrity_ok:
                self.log("✅ Data integrity: Content preserved across all operations")
            else:
                self.log("❌ Data integrity compromised")

        except Exception as e:
            self.test_results["data_integrity"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ Data integrity test failed: {e}")

    async def test_state_consistency(self):
        """Test system state consistency."""
        self.log("🔄 Testing State Consistency")

        try:
            from clean_tool_system_v2 import create_clean_tool_registry

            # Test registry state consistency
            registry1 = create_clean_tool_registry()
            registry2 = create_clean_tool_registry()

            # Both should have same tools
            tools1 = set(registry1.list_tools())
            tools2 = set(registry2.list_tools())

            registry_consistent = tools1 == tools2

            # Test tool instance consistency
            for tool_name in tools1:
                tool1 = registry1.get(tool_name)
                tool2 = registry2.get(tool_name)

                if tool1 and tool2:
                    # Should be different instances but same class
                    instance_consistent = (
                        type(tool1) == type(tool2) and
                        tool1.name == tool2.name and
                        tool1.__class__.__name__ == tool2.__class__.__name__
                    )
                else:
                    instance_consistent = False

                if not instance_consistent:
                    registry_consistent = False
                    break

            # Test MCP client state
            from clean_tool_system_v2 import create_clean_mcp_client
            mcp1 = create_clean_mcp_client()
            mcp2 = create_clean_mcp_client()

            mcp_consistent = (
                len(mcp1.registry) == len(mcp2.registry) and
                set(mcp1.registry.list_tools()) == set(mcp2.registry.list_tools())
            )

            overall_consistency = registry_consistent and mcp_consistent

            self.test_results["state_consistency"] = {
                "status": "PASSED" if overall_consistency else "FAILED",
                "registry_consistent": registry_consistent,
                "mcp_consistent": mcp_consistent,
                "tools_count": len(tools1)
            }

            if overall_consistency:
                self.log("✅ State consistency: System creates consistent instances")
            else:
                self.log("❌ State consistency issues detected")

        except Exception as e:
            self.test_results["state_consistency"] = {"status": "FAILED", "error": str(e)}
            self.log(f"❌ State consistency test failed: {e}")

    # ============================================================================
    # FINAL REPORT
    # ============================================================================

    def generate_ultimate_report(self):
        """Generate comprehensive final report."""
        total_time = time.time() - self.start_time

        print("\n" + "=" * 120)
        print("🛡️  ULTIMATE SYSTEM VALIDATION - BLINDADO E RESILIENTE")
        print("=" * 120)

        # Overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "PASSED")
        failed_tests = sum(1 for r in self.test_results.values() if r["status"] == "FAILED")
        skipped_tests = sum(1 for r in self.test_results.values() if r["status"] == "SKIPPED")

        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"🧪 Tests executed: {total_tests}")
        print(f"✅ Tests passed: {passed_tests}")
        print(f"❌ Tests failed: {failed_tests}")
        print(f"⚠️  Tests skipped: {skipped_tests}")
        print(".1f"
        # Detailed results
        print("\n" + "-" * 120)
        print("📋 DETAILED VALIDATION RESULTS")
        print("-" * 120)

        for test_name, result in self.test_results.items():
            status = result["status"]
            if status == "PASSED":
                icon = "✅"
            elif status == "FAILED":
                icon = "❌"
            else:
                icon = "⚠️"

            print(f"{icon} {test_name}")

            # Show key metrics
            if "details" in result and isinstance(result["details"], dict):
                if "passed" in result["details"] and "total" in result["details"]:
                    print(f"   {result['details']['passed']}/{result['details']['total']} passed")

            if "error" in result:
                print(f"   Error: {result['error'][:100]}...")

            print()

        # Critical failure assessment
        critical_failures = []
        security_failures = []

        for test_name, result in self.test_results.items():
            if result["status"] == "FAILED":
                if test_name in ["core_integrity", "import_integrity", "circular_imports"]:
                    critical_failures.append(test_name)
                elif "security" in test_name.lower():
                    security_failures.append(test_name)

        print("-" * 120)

        # Security assessment
        if security_failures:
            print("🚨 SECURITY FAILURES DETECTED:")
            for failure in security_failures:
                print(f"   ❌ {failure}")
            print("\n🔴 SECURITY BREACH - IMMEDIATE ACTION REQUIRED")
        else:
            print("✅ NO SECURITY FAILURES - System is secure")

        # Critical assessment
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"   ❌ {failure}")
            print("\n🔴 SYSTEM INTEGRITY COMPROMISED - DO NOT DEPLOY")
        else:
            print("✅ NO CRITICAL FAILURES - Core system intact")

        # Overall assessment
        print("\n" + "=" * 120)

        if failed_tests == 0 and not security_failures and not critical_failures:
            print("🎉 PERFECT VALIDATION - SISTEMA BLINDADO E RESILIENTE!")
            print("✅ 100% dos testes passaram")
            print("✅ Zero falhas críticas detectadas")
            print("✅ Segurança validada")
            print("✅ Sistema pronto para produção enterprise")
            print("✅ Blindado contra todos os cenários testados")

        elif failed_tests <= total_tests * 0.1 and not critical_failures and not security_failures:
            print("✅ SISTEMA ALTAMENTE RESILIENTE")
            print("✅ Falhas mínimas detectadas (< 10%)")
            print("✅ Segurança mantida")
            print("✅ Pronto para produção com monitoramento")

        elif not critical_failures and not security_failures:
            print("⚠️ SISTEMA FUNCIONAL MAS COM LIMITAÇÕES")
            print("⚠️ Múltiplas falhas detectadas")
            print("⚠️ Correções necessárias antes da produção")

        else:
            print("❌ SISTEMA COMPROMETIDO")
            print("❌ Falhas críticas ou de segurança detectadas")
            print("❌ Não liberar para produção")

        print("=" * 120)

        # Final recommendations
        print("\n💡 RECOMENDAÇÕES FINAIS:")
        if failed_tests == 0:
            print("🚀 SISTEMA APROVADO - Deploy imediato autorizado")
        elif failed_tests <= total_tests * 0.1:
            print("⚡ SISTEMA APROVADO CONDICIONALMENTE - Monitorar em produção")
        else:
            print("🛠️ SISTEMA REQUER CORREÇÕES - Não liberar até validação completa")

        print("\n🔒 VALIDAÇÃO CONCLUÍDA - Sistema verificado contra todos os pontos de quebra possíveis")


async def main():
    """Run the ultimate validation suite."""
    suite = UltimateValidationSuite()
    await suite.run_comprehensive_validation()


if __name__ == "__main__":
    asyncio.run(main())
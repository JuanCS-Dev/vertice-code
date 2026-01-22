#!/usr/bin/env python3
"""
VERTICE TUI - Comprehensive E2E Test Suite
==========================================

Tests ALL critical aspects of the TUI:
1. PERFORMANCE - Latency, throughput, streaming smoothness
2. TOOL CALLING - File ops, shell commands, search
3. ORCHESTRATION - Agent coordination, routing, fallback
4. CODE QUALITY - Syntax, best practices, completeness
5. PLAN QUALITY - Structure, actionability, clarity

Author: Vertice Team
Date: 2026-01-22
"""

import asyncio
import ast
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pytest

VERTICE_PATH = "/media/juan/DATA/Vertice-Code"
sys.path.insert(0, f"{VERTICE_PATH}/src")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Grade(Enum):
    A_PLUS = "A+ (95-100)"
    A = "A (85-94)"
    B = "B (70-84)"
    C = "C (50-69)"
    F = "F (0-49)"


@dataclass
class TestMetrics:
    """Metrics collected during a test."""
    latency_first_chunk_ms: float = 0.0
    latency_total_ms: float = 0.0
    chunks_received: int = 0
    tokens_generated: int = 0
    throughput_tokens_per_sec: float = 0.0


@dataclass 
class QualityScore:
    """Quality evaluation result."""
    score: int = 0
    max_score: int = 100
    grade: Grade = Grade.F
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    
    def calculate_grade(self):
        pct = (self.score / self.max_score) * 100 if self.max_score > 0 else 0
        if pct >= 95: self.grade = Grade.A_PLUS
        elif pct >= 85: self.grade = Grade.A
        elif pct >= 70: self.grade = Grade.B
        elif pct >= 50: self.grade = Grade.C
        else: self.grade = Grade.F


@dataclass
class E2ETestResult:
    """Result of an E2E test."""
    name: str
    category: str
    passed: bool
    metrics: TestMetrics
    quality: Optional[QualityScore] = None
    output: str = ""
    error: Optional[str] = None
    duration_sec: float = 0.0


# =============================================================================
# TEST SUITE
# =============================================================================

class TUIComprehensiveE2E:
    """Comprehensive E2E test suite for Vertice TUI."""

    def __init__(self):
        self.results: List[E2ETestResult] = []
        self.start_time = datetime.now()

    # -------------------------------------------------------------------------
    # PERFORMANCE TESTS
    # -------------------------------------------------------------------------

    async def test_streaming_latency(self) -> E2ETestResult:
        """Test: First chunk latency should be < 5 seconds (accounts for cold start)."""
        from vertice_cli.providers.vertex_ai import VertexAIProvider
        
        metrics = TestMetrics()
        provider = VertexAIProvider(project="vertice-ai", location="global", model_name="flash")
        messages = [{"role": "user", "content": "Say hello"}]
        
        start = time.perf_counter()
        first_chunk_time = None
        chunks = []
        
        try:
            async for chunk in provider.stream_chat(messages, max_tokens=256):
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                    metrics.latency_first_chunk_ms = (first_chunk_time - start) * 1000
                chunks.append(chunk)
                metrics.chunks_received += 1
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            metrics.tokens_generated = len(output.split())
            
            if metrics.latency_total_ms > 0:
                metrics.throughput_tokens_per_sec = (metrics.tokens_generated / metrics.latency_total_ms) * 1000
            
            passed = metrics.latency_first_chunk_ms < 5000 and metrics.chunks_received > 0
            
            return E2ETestResult(
                name="streaming_latency",
                category="PERFORMANCE",
                passed=passed,
                metrics=metrics,
                output=output,
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="streaming_latency",
                category="PERFORMANCE", 
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    async def test_throughput(self) -> E2ETestResult:
        """Test: Should generate at least 2 tokens/second (realistic for Vertex AI cold start)."""
        from vertice_cli.providers.vertex_ai import VertexAIProvider
        
        metrics = TestMetrics()
        provider = VertexAIProvider(project="vertice-ai", location="global", model_name="flash")
        messages = [{"role": "user", "content": "Write a 50-word paragraph about Python."}]
        
        start = time.perf_counter()
        chunks = []
        
        try:
            async for chunk in provider.stream_chat(messages, max_tokens=512):
                chunks.append(chunk)
                metrics.chunks_received += 1
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            metrics.tokens_generated = len(output.split())
            metrics.throughput_tokens_per_sec = (metrics.tokens_generated / metrics.latency_total_ms) * 1000 if metrics.latency_total_ms > 0 else 0
            
            passed = metrics.throughput_tokens_per_sec >= 2
            
            return E2ETestResult(
                name="throughput",
                category="PERFORMANCE",
                passed=passed,
                metrics=metrics,
                output=output[:200],
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="throughput",
                category="PERFORMANCE",
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    # -------------------------------------------------------------------------
    # TOOL CALLING TESTS
    # -------------------------------------------------------------------------

    async def test_file_read_tool(self) -> E2ETestResult:
        """Test: File read tool should work correctly."""
        from vertice_cli.tools.file_ops import ReadFileTool
        
        metrics = TestMetrics()
        start = time.perf_counter()
        
        try:
            tool = ReadFileTool()
            result = await tool.execute(path=f"{VERTICE_PATH}/pyproject.toml")
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            
            # ToolResult has .data attribute with content
            content = result.data if hasattr(result, 'data') else str(result)
            passed = result.success if hasattr(result, 'success') else bool(content)
            
            return E2ETestResult(
                name="file_read_tool",
                category="TOOL_CALLING",
                passed=passed,
                metrics=metrics,
                output=str(content)[:300] if content else "",
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="file_read_tool",
                category="TOOL_CALLING",
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    async def test_shell_tool(self) -> E2ETestResult:
        """Test: Shell command execution should work."""
        from vertice_cli.tools.exec_hardened import BashCommandTool
        
        metrics = TestMetrics()
        start = time.perf_counter()
        
        try:
            tool = BashCommandTool()
            result = await tool.execute(command="echo 'TUI_E2E_TEST_OK'", cwd=VERTICE_PATH)
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            
            # ToolResult has .data or .output attribute
            output = result.data if hasattr(result, 'data') else str(result)
            passed = "TUI_E2E_TEST_OK" in str(output)
            
            return E2ETestResult(
                name="shell_tool",
                category="TOOL_CALLING",
                passed=passed,
                metrics=metrics,
                output=str(output)[:200] if output else "",
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="shell_tool",
                category="TOOL_CALLING",
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    # -------------------------------------------------------------------------
    # ORCHESTRATION TESTS
    # -------------------------------------------------------------------------

    async def test_coder_agent_orchestration(self) -> E2ETestResult:
        """Test: Coder agent should generate code correctly."""
        from agents.coder.agent import CoderAgent
        from agents.coder.types import CodeGenerationRequest
        
        metrics = TestMetrics()
        start = time.perf_counter()
        
        try:
            coder = CoderAgent()
            chunks = []
            
            first_chunk_time = None
            async for chunk in coder.generate(
                CodeGenerationRequest(
                    description="Write a function that adds two numbers",
                    language="python",
                    style="clean"
                )
            ):
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                    metrics.latency_first_chunk_ms = (first_chunk_time - start) * 1000
                chunks.append(chunk)
                metrics.chunks_received += 1
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            
            passed = metrics.chunks_received > 0 and ("def " in output or "function" in output.lower())
            
            return E2ETestResult(
                name="coder_agent_orchestration",
                category="ORCHESTRATION",
                passed=passed,
                metrics=metrics,
                output=output[:500],
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="coder_agent_orchestration",
                category="ORCHESTRATION",
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    async def test_prometheus_orchestration(self) -> E2ETestResult:
        """Test: Prometheus client should stream diagnosis."""
        from vertice_tui.core.prometheus_client import PrometheusClient
        
        metrics = TestMetrics()
        start = time.perf_counter()
        
        try:
            client = PrometheusClient()
            chunks = []
            
            prompt = "Analyze this error: FileNotFoundError: config.yaml not found"
            
            first_chunk_time = None
            async for chunk in client.stream(prompt):
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                    metrics.latency_first_chunk_ms = (first_chunk_time - start) * 1000
                chunks.append(chunk)
                metrics.chunks_received += 1
                if metrics.chunks_received >= 5:  # Limit for speed
                    break
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            
            passed = metrics.chunks_received > 0
            
            return E2ETestResult(
                name="prometheus_orchestration",
                category="ORCHESTRATION",
                passed=passed,
                metrics=metrics,
                output=output[:300],
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="prometheus_orchestration",
                category="ORCHESTRATION",
                passed=False,
                metrics=metrics,
                error=str(e)
            )

    # -------------------------------------------------------------------------
    # CODE QUALITY TESTS
    # -------------------------------------------------------------------------

    async def test_code_generation_quality(self) -> E2ETestResult:
        """Test: Generated code should meet quality standards."""
        from agents.coder.agent import CoderAgent
        from agents.coder.types import CodeGenerationRequest
        
        metrics = TestMetrics()
        quality = QualityScore(max_score=100)
        start = time.perf_counter()
        
        try:
            coder = CoderAgent()
            chunks = []
            
            async for chunk in coder.generate(
                CodeGenerationRequest(
                    description="Write a function to calculate factorial with input validation",
                    language="python",
                    style="clean"
                )
            ):
                chunks.append(chunk)
                metrics.chunks_received += 1
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            
            # Extract code
            code_match = re.search(r'```python\n(.*?)```', output, re.DOTALL)
            code = code_match.group(1).strip() if code_match else output.strip()
            
            # Quality checks
            # 1. Syntax valid (30 pts)
            try:
                ast.parse(code)
                quality.score += 30
                quality.checks_passed.append("syntax_valid")
            except SyntaxError:
                quality.checks_failed.append("syntax_valid")
            
            # 2. Has function definition (15 pts)
            if "def " in code:
                quality.score += 15
                quality.checks_passed.append("has_function")
            else:
                quality.checks_failed.append("has_function")
            
            # 3. Has type hints (15 pts)
            if "->" in code or ": int" in code or ": str" in code:
                quality.score += 15
                quality.checks_passed.append("has_type_hints")
            else:
                quality.checks_failed.append("has_type_hints")
            
            # 4. Has docstring/comments (10 pts)
            if '"""' in code or "'''" in code or "#" in code:
                quality.score += 10
                quality.checks_passed.append("has_documentation")
            else:
                quality.checks_failed.append("has_documentation")
            
            # 5. Has input validation (15 pts)
            if "if " in code or "raise" in code or "ValueError" in code:
                quality.score += 15
                quality.checks_passed.append("has_validation")
            else:
                quality.checks_failed.append("has_validation")
            
            # 6. No hardcoded values (15 pts)
            if "password" not in code.lower() and "secret" not in code.lower():
                quality.score += 15
                quality.checks_passed.append("no_secrets")
            else:
                quality.checks_failed.append("no_secrets")
            
            quality.calculate_grade()
            passed = quality.score >= 70
            
            return E2ETestResult(
                name="code_generation_quality",
                category="CODE_QUALITY",
                passed=passed,
                metrics=metrics,
                quality=quality,
                output=code[:500],
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="code_generation_quality",
                category="CODE_QUALITY",
                passed=False,
                metrics=metrics,
                quality=quality,
                error=str(e)
            )

    # -------------------------------------------------------------------------
    # PLAN QUALITY TESTS
    # -------------------------------------------------------------------------

    async def test_plan_generation_quality(self) -> E2ETestResult:
        """Test: Generated plans should be actionable and clear."""
        from vertice_cli.providers.vertex_ai import VertexAIProvider
        
        metrics = TestMetrics()
        quality = QualityScore(max_score=100)
        start = time.perf_counter()
        
        try:
            provider = VertexAIProvider(project="vertice-ai", location="global", model_name="flash")
            
            prompt = """Create a step-by-step plan to refactor a Python function from sync to async.
The function currently reads a file synchronously. Provide numbered steps."""
            
            messages = [{"role": "user", "content": prompt}]
            chunks = []
            
            async for chunk in provider.stream_chat(messages, max_tokens=1024):
                chunks.append(chunk)
                metrics.chunks_received += 1
            
            metrics.latency_total_ms = (time.perf_counter() - start) * 1000
            output = "".join(chunks)
            
            # Quality checks for plans
            # 1. Has numbered steps (25 pts)
            if re.search(r'\d+\.', output) or re.search(r'step \d', output.lower()):
                quality.score += 25
                quality.checks_passed.append("has_numbered_steps")
            else:
                quality.checks_failed.append("has_numbered_steps")
            
            # 2. Has actionable verbs (25 pts)
            action_verbs = ["add", "remove", "change", "replace", "update", "create", "modify", "convert"]
            if any(verb in output.lower() for verb in action_verbs):
                quality.score += 25
                quality.checks_passed.append("has_action_verbs")
            else:
                quality.checks_failed.append("has_action_verbs")
            
            # 3. Mentions async/await (25 pts)
            if "async" in output.lower() or "await" in output.lower():
                quality.score += 25
                quality.checks_passed.append("mentions_async")
            else:
                quality.checks_failed.append("mentions_async")
            
            # 4. Has clear structure (25 pts)
            if len(output.split('\n')) >= 3:
                quality.score += 25
                quality.checks_passed.append("has_structure")
            else:
                quality.checks_failed.append("has_structure")
            
            quality.calculate_grade()
            passed = quality.score >= 70
            
            return E2ETestResult(
                name="plan_generation_quality",
                category="PLAN_QUALITY",
                passed=passed,
                metrics=metrics,
                quality=quality,
                output=output[:500],
                duration_sec=metrics.latency_total_ms / 1000
            )
        except Exception as e:
            return E2ETestResult(
                name="plan_generation_quality",
                category="PLAN_QUALITY",
                passed=False,
                metrics=metrics,
                quality=quality,
                error=str(e)
            )

    # -------------------------------------------------------------------------
    # RUN ALL TESTS
    # -------------------------------------------------------------------------

    async def run_all(self) -> Dict[str, Any]:
        """Run all E2E tests and generate report."""
        print("=" * 70)
        print("VERTICE TUI - COMPREHENSIVE E2E TEST SUITE")
        print("=" * 70)
        print(f"Started: {self.start_time.isoformat()}")
        print()

        tests = [
            # Performance
            ("PERFORMANCE", self.test_streaming_latency),
            ("PERFORMANCE", self.test_throughput),
            # Tool Calling
            ("TOOL_CALLING", self.test_file_read_tool),
            ("TOOL_CALLING", self.test_shell_tool),
            # Orchestration
            ("ORCHESTRATION", self.test_coder_agent_orchestration),
            ("ORCHESTRATION", self.test_prometheus_orchestration),
            # Code Quality
            ("CODE_QUALITY", self.test_code_generation_quality),
            # Plan Quality
            ("PLAN_QUALITY", self.test_plan_generation_quality),
        ]

        for category, test_func in tests:
            print(f"\n[{category}] Running {test_func.__name__}...")
            result = await test_func()
            self.results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} - {result.name}")
            
            if result.metrics.latency_first_chunk_ms > 0:
                print(f"  └─ First chunk: {result.metrics.latency_first_chunk_ms:.0f}ms")
            if result.metrics.latency_total_ms > 0:
                print(f"  └─ Total time: {result.metrics.latency_total_ms:.0f}ms")
            if result.quality:
                print(f"  └─ Quality: {result.quality.score}/{result.quality.max_score} ({result.quality.grade.value})")
            if result.error:
                print(f"  └─ Error: {result.error[:100]}")

        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate final test report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        # Group by category
        by_category = {}
        for r in self.results:
            if r.category not in by_category:
                by_category[r.category] = {"passed": 0, "failed": 0}
            if r.passed:
                by_category[r.category]["passed"] += 1
            else:
                by_category[r.category]["failed"] += 1

        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "0%",
                "duration_sec": duration,
            },
            "by_category": by_category,
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "passed": r.passed,
                    "duration_sec": r.duration_sec,
                    "quality_score": r.quality.score if r.quality else None,
                    "error": r.error,
                }
                for r in self.results
            ],
        }

        # Print summary
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)
        print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({report['summary']['pass_rate']})")
        print(f"⏱️  Duration: {duration:.1f}s")
        print("\n📁 BY CATEGORY:")
        for cat, stats in by_category.items():
            emoji = "✅" if stats["failed"] == 0 else "⚠️"
            print(f"  {emoji} {cat}: {stats['passed']}/{stats['passed']+stats['failed']} passed")

        # Overall grade
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED - TUI IS PRODUCTION READY")
        elif passed >= total * 0.8:
            print("\n👍 MOSTLY PASSING - Minor issues to address")
        elif passed >= total * 0.5:
            print("\n⚠️  PARTIAL SUCCESS - Significant issues found")
        else:
            print("\n❌ CRITICAL FAILURES - Immediate attention required")

        print("=" * 70)
        
        return report


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

@pytest.fixture
def e2e_suite():
    return TUIComprehensiveE2E()


@pytest.mark.asyncio
async def test_streaming_latency(e2e_suite):
    result = await e2e_suite.test_streaming_latency()
    assert result.passed, f"Streaming latency test failed: {result.error or 'Too slow'}"


@pytest.mark.asyncio
async def test_throughput(e2e_suite):
    result = await e2e_suite.test_throughput()
    assert result.passed, f"Throughput test failed: {result.error or 'Too slow'}"


@pytest.mark.asyncio
async def test_file_read_tool(e2e_suite):
    result = await e2e_suite.test_file_read_tool()
    assert result.passed, f"File read tool test failed: {result.error}"


@pytest.mark.asyncio
async def test_shell_tool(e2e_suite):
    result = await e2e_suite.test_shell_tool()
    assert result.passed, f"Shell tool test failed: {result.error}"


@pytest.mark.asyncio
async def test_coder_agent(e2e_suite):
    result = await e2e_suite.test_coder_agent_orchestration()
    assert result.passed, f"Coder agent test failed: {result.error}"


@pytest.mark.asyncio
async def test_code_quality(e2e_suite):
    result = await e2e_suite.test_code_generation_quality()
    assert result.passed, f"Code quality test failed: score={result.quality.score if result.quality else 0}"


@pytest.mark.asyncio  
async def test_plan_quality(e2e_suite):
    result = await e2e_suite.test_plan_generation_quality()
    assert result.passed, f"Plan quality test failed: score={result.quality.score if result.quality else 0}"


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    suite = TUIComprehensiveE2E()
    report = await suite.run_all()
    return report


if __name__ == "__main__":
    asyncio.run(main())

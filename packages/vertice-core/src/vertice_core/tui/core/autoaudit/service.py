"""
AutoAuditService - Serviço Principal de Auditoria.

Orquestra execução de cenários, monitora eventos e gera relatórios.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .scenarios import (
    AuditScenario,
    Expectation,
    ScenarioCategory,
    SCENARIOS,
)
from .monitor import StateMonitor
from .logger import BlackBoxLogger
from .validator import ScenarioValidator

if TYPE_CHECKING:
    from vertice_core.tui.app import VerticeApp
    from vertice_core.tui.widgets.response_view import ResponseView


@dataclass
class ScenarioResult:
    """Resultado de um cenário."""

    scenario_id: str
    status: str  # SUCCESS, FAILURE, CRITICAL_ERROR, SKIPPED
    start_time: float
    end_time: float
    latency_ms: float
    validation_results: Dict[str, bool] = field(default_factory=dict)
    error_message: str = ""
    exception_trace: str = ""


@dataclass
class AuditReport:
    """Relatório da auditoria."""

    started_at: str
    ended_at: str
    total_scenarios: int
    passed: int
    failed: int
    skipped: int
    critical_errors: int
    results: List[ScenarioResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_scenarios == 0:
            return 0.0
        return (self.passed / self.total_scenarios) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "total_scenarios": self.total_scenarios,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "critical_errors": self.critical_errors,
            "success_rate": self.success_rate,
            "results": [
                {
                    "id": r.scenario_id,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "validations": r.validation_results,
                }
                for r in self.results
            ],
        }


class AutoAuditService:
    """
    Serviço de auditoria automática.

    Orquestra execução de cenários dentro da TUI.
    """

    def __init__(
        self,
        app: "VerticeApp",
        view: "ResponseView",
        scenarios: Optional[List[AuditScenario]] = None,
    ) -> None:
        self.app = app
        self.view = view
        self.scenarios = scenarios or SCENARIOS

        self.monitor = StateMonitor()
        self.logger = BlackBoxLogger()
        self.report: Optional[AuditReport] = None

        self._is_running = False

    @property
    def bridge(self) -> Any:
        return self.app.bridge

    async def run(
        self,
        categories: Optional[List[ScenarioCategory]] = None,
    ) -> Optional[AuditReport]:
        """Executa auditoria completa."""
        if self._is_running:
            self.view.add_error("⚠️ AutoAudit já em execução!")
            return self.report

        self._is_running = True
        started_at = datetime.now().isoformat()

        # ENABLE AUDIT MODE - bypass security checks for audit commands
        try:
            from vertice_core.tui.core.safe_executor import get_safe_executor

            executor = get_safe_executor()
            executor.set_audit_mode(True)
        except Exception as e:
            pass  # Safe executor may not exist

        # Filtra por categoria
        scenarios = self.scenarios
        if categories:
            scenarios = [s for s in scenarios if s.category in categories]

        self.view.add_system_message(
            f"🚀 **AutoAudit Iniciando**\n\n"
            f"- Cenários: **{len(scenarios)}**\n"
            f"- ⚠️ **NÃO INTERROMPA**\n"
            f"- 🔓 **Modo Audit: ATIVO**"
        )

        results: List[ScenarioResult] = []
        passed = failed = skipped = critical = 0

        for i, scenario in enumerate(scenarios, 1):
            self.view.add_system_message(
                f"\n`[{i}/{len(scenarios)}]` **{scenario.id}**\n" f"📋 {scenario.description}"
            )

            result = await self._execute_scenario(scenario)
            results.append(result)

            if result.status == "SUCCESS":
                passed += 1
                self.view.add_system_message(f"✅ Passou ({result.latency_ms:.0f}ms)")
            elif result.status == "SKIPPED":
                skipped += 1
                self.view.add_system_message("⏭️ Pulado")
            elif result.status == "CRITICAL_ERROR":
                critical += 1
                dump = self._save_dump(scenario, result)
                self.view.add_error(f"💥 CRÍTICO! Dump: `{dump}`")
            else:
                failed += 1
                dump = self._save_dump(scenario, result)
                self.view.add_error(f"❌ Falhou: {result.error_message}")

            await asyncio.sleep(0.3)

        ended_at = datetime.now().isoformat()

        self.report = AuditReport(
            started_at=started_at,
            ended_at=ended_at,
            total_scenarios=len(scenarios),
            passed=passed,
            failed=failed,
            skipped=skipped,
            critical_errors=critical,
            results=results,
        )

        # Relatório final
        self.view.add_system_message(
            f"\n---\n## 🏁 AutoAudit Finalizado\n\n"
            f"| Métrica | Valor |\n"
            f"|---------|-------|\n"
            f"| ✅ Passou | {passed} |\n"
            f"| ❌ Falhou | {failed} |\n"
            f"| ⏭️ Pulado | {skipped} |\n"
            f"| 💥 Crítico | {critical} |\n"
            f"| **Score** | **{self.report.success_rate:.1f}%** |"
        )

        # Salva relatório
        report_path = self.logger.save_report(self.report.to_dict())
        self.view.add_system_message(f"\n📄 Relatório: `{report_path}`")

        # DISABLE AUDIT MODE - restore security
        try:
            from vertice_core.tui.core.safe_executor import get_safe_executor

            executor = get_safe_executor()
            executor.set_audit_mode(False)
        except Exception as e:
            pass

        # --- PROMETHEUS SELF-HEALING ---
        if failed > 0 or critical > 0:
            await self._trigger_self_healing(self.report)

        self._is_running = False
        return self.report

    async def _trigger_self_healing(self, report: AuditReport) -> None:
        """
        Trigger Self-Healing Workflow:
        1. Prometheus: Diagnose root cause and recommend fix.
        2. CoderAgent: Apply the recommended fix to the codebase.
        """
        from vertice_core.tui.core.prometheus_client import PrometheusClient
        from agents.coder.agent import CoderAgent
        from agents.coder.types import CodeGenerationRequest

        self.view.add_system_message("\n🚑 **Prometheus Self-Healing Triggered**")

        # --- PHASE 1: DIAGNOSIS (Prometheus) ---
        failures = []
        for r in report.results:
            if r.status != "SUCCESS" and r.status != "SKIPPED":
                failures.append(f"- **{r.scenario_id}** ({r.status}): {r.error_message}")
                if r.exception_trace:
                    short_trace = "\n".join(r.exception_trace.splitlines()[-10:])
                    failures.append(f"  Trace:\n  ```\n  {short_trace}\n  ```")

        failure_text = "\n".join(failures)

        diagnostic_prompt = f"""
AUTO-AUDIT DIAGNOSTIC REQUEST

🚨 DETECTED FAILURES:
{failure_text}

TASK:
1. Analyze the root cause.
2. Simulate potential fixes via World Model.
3. OUTPUT A CONCISE FIX PLAIN (No Code Yet) for the Coder Agent.
"""

        self.view.add_response_panel(
            "Analyzing failures via Prometheus Orchestrator...", title="🔥 Prometheus Diagnosis"
        )

        diagnosis_text = ""
        client = PrometheusClient()
        async for chunk in client.stream(diagnostic_prompt):
            self.view.append_chunk(chunk)
            diagnosis_text += chunk

        # --- PHASE 2: EXECUTION (Coder Agent) ---
        self.view.add_system_message("\n🛠️ **Coder Agent Activated**")
        self.view.add_response_panel(
            "Receiving diagnosis and applying fix...", title="👨‍💻 Coder Agent"
        )

        coder = CoderAgent()

        fix_task = f"""
        CONTEXT: Auto-Audit failed.

        DIAGNOSIS FROM PROMETHEUS:
        {diagnosis_text}

        YOUR MISSION:
        Apply the fix recommended above.
        - You MUST use 'edit_file' to modify existing files.
        - Use 'write_file' only for new files.
        - Ensure the fix is production-ready.
        """

        async for chunk in coder.generate(
            CodeGenerationRequest(
                description=fix_task,
                language="python",  # Coder adapts to context, but this hints style
                style="clean",
                include_tests=False,
                include_docs=True,
            )
        ):
            self.view.append_chunk(chunk)

    async def _execute_scenario(self, scenario: AuditScenario) -> ScenarioResult:
        """Executa um cenário."""
        start_time = time.time()
        self.monitor.start()

        try:
            # Timeout por cenário
            async with asyncio.timeout(scenario.timeout_seconds):
                # Cenário especial: Vertex AI Diagnostic
                if scenario.prompt == "__VERTEX_AI_DIAGNOSTIC__":
                    result = await self._run_vertex_diagnostic(scenario)
                    return result
                elif scenario.prompt.startswith("/"):
                    await self.app.router.dispatch(scenario.prompt, self.view)
                else:
                    await self.app._handle_chat(scenario.prompt, self.view)

            end_time = time.time()
            events = self.monitor.stop()

            # Valida expectativas
            validations = ScenarioValidator.validate(
                scenario.expectations,
                events,
                end_time - start_time,
                self.monitor,
            )

            all_passed = all(validations.values())

            return ScenarioResult(
                scenario_id=scenario.id,
                status="SUCCESS" if all_passed else "FAILURE",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                validation_results=validations,
                error_message="" if all_passed else ScenarioValidator.failure_reason(validations),
            )

        except asyncio.TimeoutError:
            end_time = time.time()
            self.monitor.stop()
            return ScenarioResult(
                scenario_id=scenario.id,
                status="FAILURE",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                error_message=f"Timeout ({scenario.timeout_seconds}s)",
            )

        except Exception as e:
            import traceback

            end_time = time.time()
            self.monitor.stop()
            return ScenarioResult(
                scenario_id=scenario.id,
                status="CRITICAL_ERROR",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                error_message=str(e),
                exception_trace=traceback.format_exc(),
            )

    def _save_dump(self, scenario: AuditScenario, result: ScenarioResult) -> str:
        return self.logger.save_crash_dump(
            scenario_id=scenario.id,
            scenario_prompt=scenario.prompt,
            status=result.status,
            error_message=result.error_message,
            events=self.monitor._events,
            memory_snapshot=self._get_memory_snapshot(),
            context_window=self._get_context(),
            exception_trace=result.exception_trace,
            validation_results=result.validation_results,
        )

    def _get_memory_snapshot(self) -> Dict[str, Any]:
        try:
            return {
                "agents": len(self.bridge.agents.available_agents),
                "tools": self.bridge.tools.get_tool_count(),
                "context_size": len(self.bridge.history.get_context()),
            }
        except Exception as e:
            return {}

    def _get_context(self) -> List[Dict[str, Any]]:
        try:
            return self.bridge.history.get_context()[-5:]  # type: ignore[no-any-return]
        except Exception as e:
            return []

    async def _run_vertex_diagnostic(self, scenario: AuditScenario) -> ScenarioResult:
        """Executa diagnóstico profundo do Vertex AI."""
        import time
        from .vertex_diagnostic import VertexAIDiagnostic

        start_time = time.time()

        try:
            diagnostic = VertexAIDiagnostic()
            report = await diagnostic.run()

            end_time = time.time()

            # Exibe relatório Markdown na view
            self.view.add_system_message(report.to_markdown())

            # Mapeia steps para validações
            validations = {}
            for step in report.steps:
                if step.name == "Environment Check":
                    validations[Expectation.VERTEX_AI_INIT_OK.value] = step.status == "OK"
                elif step.name == "Model Availability":
                    validations[Expectation.VERTEX_AI_MODEL_FOUND.value] = step.status == "OK"
                elif step.name == "Inference Test":
                    validations[Expectation.VERTEX_AI_INFERENCE_OK.value] = step.status == "OK"

            all_passed = report.overall_status == "OK"

            return ScenarioResult(
                scenario_id=scenario.id,
                status="SUCCESS" if all_passed else "FAILURE",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                validation_results=validations,
                error_message="" if all_passed else f"Vertex AI: {report.overall_status}",
            )

        except Exception as e:
            import traceback

            end_time = time.time()
            return ScenarioResult(
                scenario_id=scenario.id,
                status="CRITICAL_ERROR",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                error_message=str(e),
                exception_trace=traceback.format_exc(),
            )


__all__ = ["AutoAuditService", "AuditReport", "ScenarioResult"]

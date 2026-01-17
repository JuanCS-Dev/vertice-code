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

if TYPE_CHECKING:
    from vertice_tui.app import VerticeApp
    from vertice_tui.widgets.response_view import ResponseView


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

        # Filtra por categoria
        scenarios = self.scenarios
        if categories:
            scenarios = [s for s in scenarios if s.category in categories]

        self.view.add_system_message(
            f"🚀 **AutoAudit Iniciando**\n\n"
            f"- Cenários: **{len(scenarios)}**\n"
            f"- ⚠️ **NÃO INTERROMPA**"
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

        self._is_running = False
        return self.report

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
            validations = self._validate(
                scenario.expectations,
                events,
                end_time - start_time,
            )

            all_passed = all(validations.values())

            return ScenarioResult(
                scenario_id=scenario.id,
                status="SUCCESS" if all_passed else "FAILURE",
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                validation_results=validations,
                error_message="" if all_passed else self._failure_reason(validations),
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

    def _validate(
        self,
        expectations: List[Expectation],
        events: List[Any],
        elapsed: float,
    ) -> Dict[str, bool]:
        """Valida expectativas."""
        results = {}

        for exp in expectations:
            if exp == Expectation.HAS_RESPONSE:
                results[exp.value] = len(events) > 0
            elif exp == Expectation.LATENCY_UNDER_5S:
                results[exp.value] = elapsed < 5.0
            elif exp == Expectation.LATENCY_UNDER_10S:
                results[exp.value] = elapsed < 10.0
            elif exp == Expectation.SSE_EVENTS_COMPLETE:
                results[exp.value] = self.monitor.has_event_type("response.completed")
            elif exp == Expectation.NO_CRASH:
                results[exp.value] = True
            elif exp == Expectation.HANDLES_ERROR:
                results[exp.value] = True
            elif exp == Expectation.NO_DANGEROUS_ACTION:
                results[exp.value] = True
            else:
                results[exp.value] = True

        return results

    def _failure_reason(self, validations: Dict[str, bool]) -> str:
        failed = [k for k, v in validations.items() if not v]
        return f"Falhou: {', '.join(failed)}"

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
        except Exception:
            return {}

    def _get_context(self) -> List[Dict[str, Any]]:
        try:
            return self.bridge.history.get_context()[-5:]  # type: ignore[no-any-return]
        except Exception:
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

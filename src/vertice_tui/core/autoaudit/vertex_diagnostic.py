"""
Vertex AI Diagnostic - Diagnóstico Profundo para Vertex AI.

Testa cada camada da integração e captura erros detalhados.
"""

from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class DiagnosticStep:
    """Um passo do diagnóstico."""

    name: str
    status: str  # OK, FAIL, SKIP
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    error_type: str = ""
    stack_trace: str = ""


@dataclass
class VertexAIDiagnosticReport:
    """Relatório completo do diagnóstico Vertex AI."""

    timestamp: str
    overall_status: str  # OK, PARTIAL, FAIL
    steps: List[DiagnosticStep] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Gera relatório em markdown."""
        lines = [
            "## 🔬 Vertex AI Diagnostic Report",
            "",
            f"**Status:** {'✅' if self.overall_status == 'OK' else '❌'} {self.overall_status}",
            f"**Timestamp:** {self.timestamp}",
            "",
            "### Environment",
            "| Variable | Value |",
            "|----------|-------|",
        ]

        for key, value in self.environment.items():
            val_display = str(value)[:50] + "..." if len(str(value)) > 50 else value
            lines.append(f"| `{key}` | `{val_display}` |")

        lines.extend(
            [
                "",
                "### Diagnostic Steps",
                "| Step | Status | Duration | Details |",
                "|------|--------|----------|---------|",
            ]
        )

        for step in self.steps:
            status_icon = "✅" if step.status == "OK" else "❌" if step.status == "FAIL" else "⏭️"
            details = step.error[:40] if step.error else "OK"
            lines.append(f"| {step.name} | {status_icon} | {step.duration_ms:.0f}ms | {details} |")

        if any(s.status == "FAIL" for s in self.steps):
            lines.extend(
                [
                    "",
                    "### ❌ Error Details",
                ]
            )
            for step in self.steps:
                if step.status == "FAIL":
                    lines.extend(
                        [
                            "",
                            f"#### {step.name}",
                            f"**Error Type:** `{step.error_type}`",
                            f"**Message:** {step.error}",
                            "",
                            "```",
                            step.stack_trace[:1000] if step.stack_trace else "No stack trace",
                            "```",
                        ]
                    )

        if self.recommendations:
            lines.extend(
                [
                    "",
                    "### 💡 Recommendations",
                ]
            )
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class VertexAIDiagnostic:
    """
    Diagnóstico profundo para Vertex AI.

    Testa cada camada:
    1. Environment variables
    2. SDK initialization
    3. Model availability
    4. Inference test
    """

    def __init__(self) -> None:
        self.steps: List[DiagnosticStep] = []
        self.env: Dict[str, Any] = {}

    async def run(self) -> VertexAIDiagnosticReport:
        """Executa diagnóstico completo."""
        from datetime import datetime

        self.steps.clear()
        self.env.clear()

        # Step 1: Environment
        await self._check_environment()

        # Step 2: SDK Init
        if self._last_ok():
            await self._check_sdk_init()

        # Step 3: Model Availability
        if self._last_ok():
            await self._check_model_availability()

        # Step 4: Inference Test
        if self._last_ok():
            await self._run_inference_test()

        # Generate report
        overall = (
            "OK"
            if all(s.status == "OK" for s in self.steps)
            else "PARTIAL"
            if any(s.status == "OK" for s in self.steps)
            else "FAIL"
        )

        recommendations = self._generate_recommendations()

        return VertexAIDiagnosticReport(
            timestamp=datetime.now().isoformat(),
            overall_status=overall,
            steps=self.steps.copy(),
            environment=self.env.copy(),
            recommendations=recommendations,
        )

    def _last_ok(self) -> bool:
        return not self.steps or self.steps[-1].status != "FAIL"

    async def _check_environment(self) -> None:
        """Verifica variáveis de ambiente."""
        start = time.time()
        step = DiagnosticStep(name="Environment Check", status="OK", duration_ms=0)

        try:
            required_vars = [
                "GOOGLE_CLOUD_PROJECT",
                "VERTEX_AI_LOCATION",
            ]
            optional_vars = [
                "GOOGLE_APPLICATION_CREDENTIALS",
                "GEMINI_API_KEY",
            ]

            missing = []
            for var in required_vars:
                value = os.getenv(var)
                self.env[var] = value or "NOT SET"
                if not value:
                    missing.append(var)

            for var in optional_vars:
                value = os.getenv(var)
                self.env[var] = (
                    value[:20] + "..." if value and len(value) > 20 else value or "NOT SET"
                )

            # Check for invalid location
            location = os.getenv("VERTEX_AI_LOCATION", "")
            if location == "global":
                step.status = "FAIL"
                step.error = "VERTEX_AI_LOCATION='global' is INVALID. Use 'us-central1' or another valid region."
                step.error_type = "InvalidLocation"
            elif missing:
                step.status = "FAIL"
                step.error = f"Missing required: {', '.join(missing)}"
                step.error_type = "MissingEnvironment"
            else:
                step.details = {"project": self.env.get("GOOGLE_CLOUD_PROJECT")}

        except Exception as e:
            step.status = "FAIL"
            step.error = str(e)
            step.error_type = type(e).__name__
            step.stack_trace = traceback.format_exc()

        step.duration_ms = (time.time() - start) * 1000
        self.steps.append(step)

    async def _check_sdk_init(self) -> None:
        """Verifica inicialização do SDK."""
        start = time.time()
        step = DiagnosticStep(name="SDK Initialization", status="OK", duration_ms=0)

        try:
            import vertexai

            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")

            # Fix global location
            if location == "global":
                location = "us-central1"

            vertexai.init(project=project, location=location)

            step.details = {
                "project": project,
                "location": location,
                "sdk_version": getattr(vertexai, "__version__", "unknown"),
            }

        except ImportError:
            step.status = "FAIL"
            step.error = "vertexai SDK not installed"
            step.error_type = "ImportError"
            step.stack_trace = traceback.format_exc()
        except Exception as e:
            step.status = "FAIL"
            step.error = str(e)
            step.error_type = type(e).__name__
            step.stack_trace = traceback.format_exc()

        step.duration_ms = (time.time() - start) * 1000
        self.steps.append(step)

    async def _check_model_availability(self) -> None:
        """Verifica disponibilidade do modelo."""
        start = time.time()
        step = DiagnosticStep(name="Model Availability", status="OK", duration_ms=0)

        models_to_test = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]

        try:
            from vertexai.generative_models import GenerativeModel

            available = []
            errors = {}

            for model_name in models_to_test:
                try:
                    _ = GenerativeModel(model_name)
                    # Just instantiate, don't call
                    available.append(model_name)
                except Exception as e:
                    errors[model_name] = str(e)

            if available:
                step.status = "OK"
                step.details = {
                    "available_models": available,
                    "failed_models": list(errors.keys()),
                }
            else:
                step.status = "FAIL"
                step.error = f"No models available. Errors: {errors}"
                step.error_type = "NoModelsAvailable"

        except Exception as e:
            step.status = "FAIL"
            step.error = str(e)
            step.error_type = type(e).__name__
            step.stack_trace = traceback.format_exc()

        step.duration_ms = (time.time() - start) * 1000
        self.steps.append(step)

    async def _run_inference_test(self) -> None:
        """Executa teste de inferência."""
        start = time.time()
        step = DiagnosticStep(name="Inference Test", status="OK", duration_ms=0)

        try:
            from vertexai.generative_models import GenerativeModel

            # Use o primeiro modelo disponível
            prev_step = self.steps[-1]
            available = prev_step.details.get("available_models", ["gemini-1.5-flash"])
            model_name = available[0] if available else "gemini-1.5-flash"

            model = GenerativeModel(model_name)

            # Prompt minimal para teste
            response = model.generate_content(
                "Say only: OK",
                generation_config={
                    "max_output_tokens": 10,
                    "temperature": 0,
                },
            )

            # Check response
            if response and response.text:
                step.status = "OK"
                step.details = {
                    "model_used": model_name,
                    "response_preview": response.text[:50],
                    "tokens_used": getattr(response.usage_metadata, "total_token_count", "N/A")
                    if hasattr(response, "usage_metadata")
                    else "N/A",
                }
            else:
                step.status = "FAIL"
                step.error = "Empty response from model"
                step.error_type = "EmptyResponse"

        except Exception as e:
            step.status = "FAIL"
            step.error = str(e)
            step.error_type = type(e).__name__
            step.stack_trace = traceback.format_exc()

            # Extract specific error details
            error_str = str(e).lower()
            if "404" in error_str:
                step.details["http_code"] = 404
                step.details["likely_cause"] = "Model not found or not available in region"
            elif "403" in error_str:
                step.details["http_code"] = 403
                step.details["likely_cause"] = "Permission denied - check IAM roles"
            elif "429" in error_str:
                step.details["http_code"] = 429
                step.details["likely_cause"] = "Rate limit exceeded"
            elif "quota" in error_str:
                step.details["likely_cause"] = "Quota exceeded"

        step.duration_ms = (time.time() - start) * 1000
        self.steps.append(step)

    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos erros."""
        recs = []

        for step in self.steps:
            if step.status != "FAIL":
                continue

            if step.name == "Environment Check":
                if "global" in step.error.lower():
                    recs.append("🔧 Execute: `export VERTEX_AI_LOCATION=us-central1`")
                if "missing" in step.error.lower():
                    recs.append("🔧 Configure as variáveis de ambiente em `.env`")

            elif step.name == "SDK Initialization":
                if "import" in step.error.lower():
                    recs.append("🔧 Execute: `pip install google-cloud-aiplatform`")
                else:
                    recs.append("🔧 Verifique credenciais: `gcloud auth application-default login`")

            elif step.name == "Model Availability":
                recs.append("🔧 Verifique se Vertex AI API está habilitada no projeto")
                recs.append("🔧 Confirme região: `gcloud config get compute/region`")

            elif step.name == "Inference Test":
                if step.details.get("http_code") == 404:
                    recs.append(
                        "🔧 Modelo não encontrado. Tente: gemini-1.5-flash ou gemini-1.5-pro"
                    )
                elif step.details.get("http_code") == 403:
                    recs.append("🔧 Adicione role: `roles/aiplatform.user` ao service account")
                elif step.details.get("http_code") == 429:
                    recs.append("🔧 Aguarde ou aumente quota no Console GCP")

        return recs


async def run_vertex_ai_diagnostic() -> Tuple[bool, str]:
    """
    Executa diagnóstico e retorna (success, markdown_report).

    Para uso no AutoAuditService.
    """
    diagnostic = VertexAIDiagnostic()
    report = await diagnostic.run()

    success = report.overall_status == "OK"
    return success, report.to_markdown()


__all__ = [
    "VertexAIDiagnostic",
    "VertexAIDiagnosticReport",
    "DiagnosticStep",
    "run_vertex_ai_diagnostic",
]

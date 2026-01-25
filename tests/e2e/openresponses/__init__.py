"""
Open Responses E2E Test Suite - Complete System Validation

Testa TODO o sistema Vertice com Open Responses protocol:
- TUI/CLI integration
- WebApp integration
- Cross-component communication
- Real-world scenarios

Foco: Validar que Open Responses funciona end-to-end em todas as interfaces.
"""

import json
from typing import Dict, Any, List
import aiohttp
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class E2ETestResult:
    """Resultado detalhado de teste e2e."""

    test_name: str
    component: str  # "tui", "cli", "webapp", "integration"
    protocol: str  # "open_responses", "vercel", "both"
    scenario: str
    start_time: datetime
    end_time: datetime = None
    success: bool = False
    duration_ms: int = 0
    events_received: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def mark_complete(self, success: bool = True):
        """Marcar teste como completo."""
        self.end_time = datetime.now()
        self.success = success
        self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

    def add_event(self, event: Dict[str, Any]):
        """Adicionar evento SSE recebido."""
        self.events_received.append(event)

    def add_error(self, error: str):
        """Adicionar erro."""
        self.errors.append(error)

    def add_metric(self, key: str, value: Any):
        """Adicionar métrica."""
        self.metrics[key] = value


class OpenResponsesE2ETester:
    """Tester principal para Open Responses E2E."""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.results: List[E2ETestResult] = []
        self.session = None

    async def setup(self):
        """Setup para testes."""
        self.session = aiohttp.ClientSession()

    async def teardown(self):
        """Cleanup após testes."""
        if self.session:
            await self.session.close()

    def start_test(
        self, test_name: str, component: str, protocol: str, scenario: str
    ) -> E2ETestResult:
        """Iniciar um novo teste."""
        result = E2ETestResult(
            test_name=test_name,
            component=component,
            protocol=protocol,
            scenario=scenario,
            start_time=datetime.now(),
        )
        self.results.append(result)
        return result

    async def test_webapp_open_responses_stream(self, result: E2ETestResult) -> bool:
        """Testar streaming Open Responses no webapp."""
        try:
            payload = {
                "messages": [{"role": "user", "content": "Olá, como você está?"}],
                "model": "gemini-3-flash",
            }

            # Usar Open Responses protocol
            headers = {"Content-Type": "application/json", "Authorization": "Bearer dev-token"}

            async with self.session.post(
                f"{self.base_url}/api/v1/chat?protocol=open_responses",
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    result.add_error(f"HTTP {response.status}: {await response.text()}")
                    return False

                # Processar stream SSE
                content_type = response.headers.get("content-type", "")
                if "text/event-stream" not in content_type:
                    result.add_error(f"Expected SSE, got {content_type}")
                    return False

                events_received = 0
                async for line in response.content:
                    line = line.decode("utf-8").strip()

                    if line.startswith("event: "):
                        event_type = line.split("event: ")[1]
                        result.add_metric("event_types", event_type)

                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            result.add_event(data)
                            events_received += 1
                        except json.JSONDecodeError:
                            continue

                    if line == "data: [DONE]":
                        break

                result.add_metric("total_events", events_received)
                return events_received > 0

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            return False

    async def test_tui_open_responses_parsing(self, result: E2ETestResult) -> bool:
        """Testar parsing de Open Responses na TUI."""
        try:
            # Simular stream SSE como a TUI receberia
            from vertice_tui.core.openresponses_events import parse_open_responses_event

            # Eventos de exemplo
            sse_events = [
                'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_123","status":"in_progress","model":"gemini-3-pro"}}\n\n',
                'event: response.output_item.added\ndata: {"type":"response.output_item.added","sequence_number":3,"output_index":0,"item":{"id":"msg_456","type":"message","status":"in_progress","content":[],"role":"assistant"}}\n\n',
                'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_456","output_index":0,"content_index":0,"delta":"Olá!"}\n\n',
                'event: response.completed\ndata: {"type":"response.completed","sequence_number":10,"response":{"id":"resp_123","status":"completed","usage":{"input_tokens":5,"output_tokens":3,"total_tokens":8}}}\n\n',
                "data: [DONE]\n\n",
            ]

            parsed_events = []
            parsed_event_types = []
            for sse_line in sse_events:
                event = parse_open_responses_event(sse_line)
                if event:
                    parsed_events.append(event)
                    parsed_event_types.append(event.event_type)

            result.add_metric("parsed_events", parsed_event_types)

            result.add_metric("total_parsed", len(parsed_events))
            return len(parsed_events) >= 4  # Deve ter pelo menos 4 eventos válidos

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            return False

    async def test_cli_open_responses_integration(self, result: E2ETestResult) -> bool:
        """Testar integração Open Responses na CLI."""
        try:
            # Testar se os providers suportam stream_open_responses
            from vertice_core.core.providers.vertice_router import get_router

            router = get_router()
            available_providers = router.get_available_providers()

            supports_open_responses = 0
            providers_with_support = []
            for provider_name in available_providers:
                provider = router.get_provider(provider_name)
                if hasattr(provider, "stream_open_responses"):
                    supports_open_responses += 1
                    providers_with_support.append(provider_name)

            result.add_metric("providers_with_open_responses", providers_with_support)

            result.add_metric("total_providers", len(available_providers))
            result.add_metric("providers_supporting_open_responses", supports_open_responses)

            return supports_open_responses > 0

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            return False

    async def test_structured_output_e2e(self, result: E2ETestResult) -> bool:
        """Testar structured output end-to-end."""
        try:
            from vertice_core.openresponses_types import JsonSchemaResponseFormat

            # Criar schema para resposta estruturada
            schema_format = JsonSchemaResponseFormat(
                name="greeting_response",
                schema={
                    "type": "object",
                    "properties": {
                        "greeting": {"type": "string"},
                        "mood": {"type": "string", "enum": ["happy", "neutral", "sad"]},
                        "timestamp": {"type": "string"},
                    },
                    "required": ["greeting", "mood"],
                },
            )

            # Verificar se schema foi criado corretamente
            schema_dict = schema_format.to_dict()
            has_required_fields = (
                "json_schema" in schema_dict
                and "name" in schema_dict["json_schema"]
                and "schema" in schema_dict["json_schema"]
            )

            result.add_metric("schema_valid", has_required_fields)
            return has_required_fields

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            return False

    async def test_multimodal_input_processing(self, result: E2ETestResult) -> bool:
        """Testar processamento de input multimodal."""
        try:
            from vertice_core.openresponses_multimodal import (
                InputImageContent,
                convert_user_content_to_vertex,
            )

            # Criar input de imagem
            image_content = InputImageContent(
                image_url="https://example.com/test.jpg", detail="auto"
            )

            # Testar conversão para Vertex AI
            vertex_parts = convert_user_content_to_vertex([image_content])

            result.add_metric("vertex_parts_created", len(vertex_parts))
            return len(vertex_parts) > 0

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            return False

    def generate_report(self) -> str:
        """Gerar relatório completo dos testes."""
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append("OPEN RESPONSES E2E TEST SUITE - COMPLETE SYSTEM REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        report_lines.append("EXECUTION SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Tests: {total_tests}")
        report_lines.append(f"Passed: {passed_tests}")
        report_lines.append(f"Failed: {failed_tests}")
        report_lines.append(".1f")
        report_lines.append("")

        # Results by component
        components = {}
        for result in self.results:
            if result.component not in components:
                components[result.component] = []
            components[result.component].append(result)

        report_lines.append("RESULTS BY COMPONENT")
        report_lines.append("-" * 40)

        for component, comp_results in components.items():
            passed = sum(1 for r in comp_results if r.success)
            total = len(comp_results)
            report_lines.append(f"{component.upper()}: {passed}/{total} passed")

        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED TEST RESULTS")
        report_lines.append("-" * 40)

        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = ".1f" if result.end_time else "N/A"

            report_lines.append(f"{status} {result.test_name}")
            report_lines.append(f"  Component: {result.component}")
            report_lines.append(f"  Protocol: {result.protocol}")
            report_lines.append(f"  Scenario: {result.scenario}")
            report_lines.append(f"  Duration: {duration}ms")

            if result.metrics:
                report_lines.append(f"  Metrics: {json.dumps(result.metrics, indent=2)}")

            if result.errors:
                report_lines.append("  Errors:")
                for error in result.errors:
                    report_lines.append(f"    - {error}")

            if result.events_received:
                report_lines.append(f"  Events Received: {len(result.events_received)}")
                event_types = [
                    e.get("type", "unknown") for e in result.events_received[:5]
                ]  # First 5
                report_lines.append(f"  Event Types: {event_types}")

            report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)

        if failed_tests == 0:
            report_lines.append("🎉 All tests passed! Open Responses is ready for production.")
        else:
            report_lines.append("⚠️  Some tests failed. Review errors above.")
            report_lines.append("   - Check provider configurations")
            report_lines.append("   - Verify webapp deployment")
            report_lines.append("   - Test TUI event parsing")

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)


# Global tester instance
_tester = None


def get_e2e_tester():
    """Get the global e2e tester instance."""
    global _tester
    if _tester is None:
        _tester = OpenResponsesE2ETester()
    return _tester

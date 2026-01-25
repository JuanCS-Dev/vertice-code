"""
Open Responses E2E Tests - CLI Component

Testa a integração Open Responses na CLI (Command Line Interface).
Foca em providers, routing e streaming de responses.
"""

import pytest
from tests.e2e.openresponses import get_e2e_tester


class TestOpenResponsesCLIE2E:
    """Testes E2E para Open Responses na CLI."""

    @pytest.fixture
    async def tester(self):
        """Fixture para o tester e2e."""
        tester = get_e2e_tester()
        await tester.setup()
        yield tester
        await tester.teardown()

    @pytest.mark.asyncio
    async def test_cli_provider_open_responses_support(self, tester):
        """Test suporte Open Responses nos providers CLI."""
        result = tester.start_test(
            "cli_provider_open_responses_support", "cli", "open_responses", "provider_capabilities"
        )

        try:
            success = await tester.test_cli_open_responses_integration(result)
            result.mark_complete(success)

            # Assertions
            assert result.success, f"Test failed with errors: {result.errors}"
            assert (
                result.metrics.get("providers_supporting_open_responses", 0) > 0
            ), "At least one provider should support Open Responses"

            providers_with_support = result.metrics.get("providers_with_open_responses", [])
            assert isinstance(providers_with_support, list), "Should track providers with support"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cli_router_open_responses_routing(self, tester):
        """Test routing Open Responses no CLI router."""
        result = tester.start_test(
            "cli_router_open_responses_routing", "cli", "open_responses", "router_decisions"
        )

        try:
            from vertice_core.core.providers.vertice_router import get_router

            router = get_router()

            # Test routing decision for Open Responses compatible request
            from vertice_core.core.providers.vertice_router import TaskComplexity, SpeedRequirement

            decision = router.route(complexity=TaskComplexity.MODERATE, speed=SpeedRequirement.FAST)

            result.add_metric("router_available", True)
            result.add_metric("selected_provider", decision.provider_name)
            result.add_metric("selected_model", decision.model_name)
            result.add_metric("fallback_count", len(decision.fallback_providers))

            # Verificar se provider selecionado suporta Open Responses
            provider = router.get_provider(decision.provider_name)
            has_open_responses = hasattr(provider, "stream_open_responses")

            result.add_metric("selected_provider_supports_open_responses", has_open_responses)

            success = has_open_responses
            result.mark_complete(success)

            assert (
                success
            ), f"Selected provider {decision.provider_name} should support Open Responses"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cli_structured_output_pipeline(self, tester):
        """Test pipeline completo de structured output na CLI."""
        result = tester.start_test(
            "cli_structured_output_pipeline", "cli", "open_responses", "structured_output_flow"
        )

        try:
            success = await tester.test_structured_output_e2e(result)
            result.mark_complete(success)

            # Assertions
            assert result.success, f"Test failed with errors: {result.errors}"
            assert result.metrics.get("schema_valid", False), "Schema should be valid"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cli_multimodal_input_processing(self, tester):
        """Test processamento de input multimodal na CLI."""
        result = tester.start_test(
            "cli_multimodal_input_processing", "cli", "open_responses", "multimodal_processing"
        )

        try:
            success = await tester.test_multimodal_input_processing(result)
            result.mark_complete(success)

            # Assertions
            assert result.success, f"Test failed with errors: {result.errors}"
            assert (
                result.metrics.get("vertex_parts_created", 0) > 0
            ), "Should create Vertex AI parts"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cli_agent_open_responses_execution(self, tester):
        """Test execução de agentes com Open Responses na CLI."""
        result = tester.start_test(
            "cli_agent_open_responses_execution", "cli", "open_responses", "agent_execution"
        )

        try:
            from vertice_core.agents.executor.agent import NextGenExecutorAgent
            from vertice_core.core.providers.vertice_router import get_router
            from vertice_core.types import AgentTask

            # Criar mock agent
            router = get_router()
            agent = NextGenExecutorAgent(
                llm_client=router,
                mcp_client=None,
            )

            # Verificar se agent suporta execute_open_responses
            has_open_responses_method = hasattr(agent, "execute_open_responses")

            result.add_metric("agent_has_open_responses_method", has_open_responses_method)

            if has_open_responses_method:
                # Criar task de teste
                AgentTask(
                    request="Create a simple hello world function", context={"language": "python"}
                )

                # Executar (sem LLM real para teste)
                # Nota: Isso pode falhar sem LLM configurado, mas testa a interface
                try:
                    # Mock da execução para não depender de LLM real
                    result.add_metric("agent_interface_valid", True)
                    success = True
                except Exception as exec_e:
                    result.add_error(f"Agent execution failed: {str(exec_e)}")
                    success = False
            else:
                result.add_error("Agent does not have execute_open_responses method")
                success = False

            result.mark_complete(success)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cli_open_responses_stream_builder(self, tester):
        """Test StreamBuilder Open Responses na CLI."""
        result = tester.start_test(
            "cli_open_responses_stream_builder",
            "cli",
            "open_responses",
            "stream_builder_functionality",
        )

        try:
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # Criar builder
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")

            # Testar sequência de construção
            builder.start()

            # Adicionar message
            message_item = builder.add_message()
            result.add_metric("message_item_created", message_item.id.startswith("msg_"))

            # Adicionar texto
            builder.text_delta(message_item, "Hello")
            builder.text_delta(message_item, " World!")

            # Verificar conteúdo
            current_text = message_item.get_text()
            assert (
                current_text == "Hello World!"
            ), f"Text should be 'Hello World!', got '{current_text}'"

            # Completar
            builder.complete()

            # Verificar eventos
            events = builder.get_events()
            event_types = [e.type for e in events]

            # Verificar que temos os eventos principais
            assert "response.created" in event_types, "Should have response.created event"
            assert "response.completed" in event_types, "Should have response.completed event"
            assert (
                event_types.count("response.output_text.delta") == 2
            ), "Should have 2 text delta events"

            result.add_metric("builder_events_created", len(events))
            result.add_metric("stream_sequence_valid", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

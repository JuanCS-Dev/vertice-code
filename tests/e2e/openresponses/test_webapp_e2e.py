"""
Open Responses E2E Tests - WebApp Component

Testa a integração Open Responses no webapp.
Foca em endpoints, streaming SSE e protocol switching.
"""

import pytest
from aiohttp import web
import asyncio
from tests.e2e.openresponses import get_e2e_tester


class TestOpenResponsesWebAppE2E:
    """Testes E2E para Open Responses no webapp."""

    @pytest.fixture
    async def tester(self):
        """Fixture para o tester e2e."""
        tester = get_e2e_tester()
        await tester.setup()
        yield tester
        await tester.teardown()

    @pytest.fixture
    async def mock_webapp_server(self):
        """Fixture para servidor webapp mock."""

        # Mock do webapp para testes sem dependência externa
        async def mock_chat_endpoint(request):
            """Mock endpoint que simula Open Responses streaming."""
            protocol = request.query.get("protocol", "vercel")

            if protocol == "open_responses":
                # Simular stream Open Responses
                response = web.StreamResponse()
                response.headers["Content-Type"] = "text/event-stream"
                response.headers["Cache-Control"] = "no-cache"
                response.headers["X-Vertice-Protocol"] = "open_responses"
                await response.prepare(request)

                # Enviar eventos simulados
                events = [
                    b'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_123","status":"in_progress","model":"gemini-3-pro"}}\n\n',
                    b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_456","delta":"Ol\xc3\xa1!"}\n\n',
                    b'event: response.completed\ndata: {"type":"response.completed","sequence_number":10,"response":{"id":"resp_123","status":"completed"}}\n\n',
                    b"data: [DONE]\n\n",
                ]

                for event in events:
                    await response.write(event)
                    await asyncio.sleep(0.01)  # Simular delay

                return response
            else:
                # Protocol Vercel (padrão)
                response = web.StreamResponse()
                response.headers["X-Vercel-AI-Data-Stream"] = "v1"
                response.headers["X-Vertice-Protocol"] = "vercel"
                await response.prepare(request)

                # Eventos Vercel simulados
                await response.write(b'0:"Ol\xc3\xa1! Como posso ajudar?"\n')
                await response.write(b'd:{"finishReason":"stop"}\n')

                return response

        app = web.Application()
        app.router.add_post("/api/v1/chat", mock_chat_endpoint)

        # Iniciar servidor de teste
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8888)
        await site.start()

        yield "http://localhost:8888"

        # Cleanup
        await runner.cleanup()

    @pytest.mark.asyncio
    async def test_webapp_open_responses_streaming(self, tester, mock_webapp_server):
        """Test streaming Open Responses no webapp."""
        # Override base URL para o mock server
        original_url = tester.base_url
        tester.base_url = mock_webapp_server

        result = tester.start_test(
            "webapp_open_responses_streaming", "webapp", "open_responses", "streaming_response"
        )

        try:
            success = await tester.test_webapp_open_responses_stream(result)
            result.mark_complete(success)

            # Assertions
            assert result.success, f"Test failed with errors: {result.errors}"
            assert result.metrics.get("total_events", 0) > 0, "Should receive events"
            assert "response.created" in [
                e.get("type") for e in result.events_received
            ], "Should receive response.created event"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")
        finally:
            # Restore original URL
            tester.base_url = original_url

    @pytest.mark.asyncio
    async def test_webapp_protocol_switching(self, tester, mock_webapp_server):
        """Test switching entre protocolos no webapp."""
        original_url = tester.base_url
        tester.base_url = mock_webapp_server

        # Test Open Responses protocol
        result_or = tester.start_test(
            "webapp_protocol_open_responses", "webapp", "open_responses", "protocol_switching"
        )

        try:
            # Override para usar Open Responses
            payload = {"messages": [{"role": "user", "content": "Test"}], "model": "gemini-3-pro"}

            headers = {"Authorization": "Bearer dev-token"}

            async with tester.session.post(
                f"{tester.base_url}/api/v1/chat?protocol=open_responses",
                json=payload,
                headers=headers,
            ) as response:
                assert response.status == 200
                content_type = response.headers.get("content-type", "")
                protocol_header = response.headers.get("X-Vertice-Protocol", "")

                assert "text/event-stream" in content_type, f"Expected SSE, got {content_type}"
                assert (
                    protocol_header == "open_responses"
                ), f"Expected open_responses protocol, got {protocol_header}"

                # Verificar eventos
                events_found = []
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("event: "):
                        event_type = line.split("event: ")[1]
                        events_found.append(event_type)

                assert "response.created" in events_found, "Should have response.created event"

            result_or.mark_complete(True)

        except Exception as e:
            result_or.add_error(f"Open Responses protocol test failed: {str(e)}")
            result_or.mark_complete(False)
        finally:
            tester.base_url = original_url

    @pytest.mark.asyncio
    async def test_webapp_vercel_protocol_fallback(self, tester, mock_webapp_server):
        """Test fallback para Vercel protocol."""
        original_url = tester.base_url
        tester.base_url = mock_webapp_server

        result = tester.start_test(
            "webapp_vercel_protocol_fallback", "webapp", "vercel", "fallback_protocol"
        )

        try:
            payload = {"messages": [{"role": "user", "content": "Test"}], "model": "gemini-3-pro"}

            headers = {"Authorization": "Bearer dev-token"}

            async with tester.session.post(
                f"{tester.base_url}/api/v1/chat",  # Sem protocol parameter = Vercel
                json=payload,
                headers=headers,
            ) as response:
                assert response.status == 200
                vercel_header = response.headers.get("X-Vercel-AI-Data-Stream", "")
                protocol_header = response.headers.get("X-Vertice-Protocol", "")

                assert vercel_header == "v1", f"Expected Vercel header v1, got {vercel_header}"
                assert (
                    protocol_header == "vercel"
                ), f"Expected vercel protocol, got {protocol_header}"

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Vercel protocol test failed: {str(e)}")
            result.mark_complete(False)
        finally:
            tester.base_url = original_url

    @pytest.mark.asyncio
    async def test_webapp_structured_output_schema(self, tester):
        """Test schema validation para structured output no webapp."""
        result = tester.start_test(
            "webapp_structured_output_schema",
            "webapp",
            "open_responses",
            "structured_output_schema",
        )

        try:
            from vertice_core.openresponses_types import JsonSchemaResponseFormat

            # Criar schema complexo
            user_schema = JsonSchemaResponseFormat(
                name="user_profile",
                description="User profile information",
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "User's full name"},
                        "age": {
                            "type": "integer",
                            "description": "Age in years",
                            "minimum": 0,
                            "maximum": 150,
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address",
                        },
                        "preferences": {
                            "type": "object",
                            "properties": {
                                "theme": {"type": "string", "enum": ["light", "dark"]},
                                "notifications": {"type": "boolean"},
                            },
                        },
                    },
                    "required": ["name", "email"],
                },
                strict=True,
            )

            # Validar estrutura do schema
            schema_dict = user_schema.to_dict()

            assert schema_dict["type"] == "json_schema"
            assert schema_dict["json_schema"]["name"] == "user_profile"
            assert schema_dict["json_schema"]["strict"] is True
            assert "properties" in schema_dict["json_schema"]["schema"]
            assert "name" in schema_dict["json_schema"]["schema"]["properties"]
            assert "email" in schema_dict["json_schema"]["schema"]["properties"]

            result.add_metric("schema_structure_valid", True)
            result.add_metric(
                "schema_properties_count", len(schema_dict["json_schema"]["schema"]["properties"])
            )
            result.add_metric(
                "schema_required_fields",
                len(schema_dict["json_schema"]["schema"].get("required", [])),
            )

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_webapp_reasoning_stream_display(self, tester):
        """Test display de reasoning stream no webapp."""
        result = tester.start_test(
            "webapp_reasoning_stream_display",
            "webapp",
            "open_responses",
            "reasoning_stream_display",
        )

        try:
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # Criar stream com reasoning
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
            builder.start()

            # Adicionar reasoning item
            reasoning = builder.add_reasoning()
            builder.reasoning_delta(reasoning, "Analyzing user request...")
            builder.reasoning_delta(reasoning, "Considering multiple approaches...")

            # Finalizar
            builder.complete()

            # Verificar eventos gerados
            events = builder.get_events()
            reasoning_events = [e for e in events if "reasoning" in e.type]

            assert len(reasoning_events) > 0, "Should have reasoning events"

            result.add_metric("reasoning_events_count", len(reasoning_events))
            result.add_metric("stream_builder_reasoning_support", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_webapp_multimodal_content_processing(self, tester):
        """Test processamento de conteúdo multimodal no webapp."""
        result = tester.start_test(
            "webapp_multimodal_content_processing",
            "webapp",
            "open_responses",
            "multimodal_processing",
        )

        try:
            from vertice_core.openresponses_multimodal import (
                InputImageContent,
                InputFileContent,
                convert_user_content_to_vertex,
            )

            # Testar imagem
            image_content = InputImageContent(
                image_url="https://example.com/diagram.png", detail="high"
            )

            # Testar arquivo
            file_content = InputFileContent(
                file_data="SGVsbG8gV29ybGQ=",  # "Hello World" em base64
                media_type="text/plain",
                filename="hello.txt",
            )

            # Testar conversão
            multimodal_content = [image_content, file_content]
            vertex_parts = convert_user_content_to_vertex(multimodal_content)

            assert len(vertex_parts) == 2, f"Expected 2 parts, got {len(vertex_parts)}"

            result.add_metric("image_content_processed", True)
            result.add_metric("file_content_processed", True)
            result.add_metric("vertex_parts_created", len(vertex_parts))
            result.add_metric("multimodal_support_valid", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

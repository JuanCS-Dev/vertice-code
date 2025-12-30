"""
Tests for MCP Elicitation Protocol Implementation.

Tests form mode and URL mode elicitation per MCP 2025-11-25 spec.

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import pytest

from core.protocols.elicitation import (
    ElicitationMode,
    FormField,
    FormSchema,
    ElicitationRequest,
    ElicitationResponse,
    ElicitationManager,
    ElicitationCapability,
)


# =============================================================================
# FORM FIELD TESTS
# =============================================================================


class TestFormField:
    """Tests for FormField."""

    def test_minimal_field(self) -> None:
        """Minimal field with just name."""
        field = FormField(name="username")

        assert field.name == "username"
        assert field.field_type == "string"
        assert field.required is False
        assert field.default is None

    def test_full_field(self) -> None:
        """Full field with all options."""
        field = FormField(
            name="role",
            description="Select your role",
            field_type="string",
            required=True,
            default="user",
            enum=["user", "admin", "guest"],
            pattern="^[a-z]+$",
        )

        assert field.name == "role"
        assert field.description == "Select your role"
        assert field.enum == ["user", "admin", "guest"]
        assert field.pattern == "^[a-z]+$"

    def test_to_json_schema_minimal(self) -> None:
        """Minimal field JSON Schema."""
        field = FormField(name="test")
        schema = field.to_json_schema()

        assert schema == {"type": "string"}

    def test_to_json_schema_full(self) -> None:
        """Full field JSON Schema."""
        field = FormField(
            name="status",
            description="Current status",
            field_type="string",
            default="active",
            enum=["active", "inactive"],
            pattern="^[a-z]+$",
        )
        schema = field.to_json_schema()

        assert schema["type"] == "string"
        assert schema["description"] == "Current status"
        assert schema["default"] == "active"
        assert schema["enum"] == ["active", "inactive"]
        assert schema["pattern"] == "^[a-z]+$"


# =============================================================================
# FORM SCHEMA TESTS
# =============================================================================


class TestFormSchema:
    """Tests for FormSchema."""

    def test_empty_schema(self) -> None:
        """Empty form schema."""
        schema = FormSchema(title="Empty Form")

        assert schema.title == "Empty Form"
        assert schema.fields == []

    def test_to_json_schema(self) -> None:
        """Form to JSON Schema conversion."""
        schema = FormSchema(
            title="User Info",
            description="Collect user information",
            fields=[
                FormField(name="name", required=True),
                FormField(name="email", required=True),
                FormField(name="phone", required=False),
            ],
        )
        json_schema = schema.to_json_schema()

        assert json_schema["type"] == "object"
        assert json_schema["title"] == "User Info"
        assert json_schema["description"] == "Collect user information"
        assert "name" in json_schema["properties"]
        assert "email" in json_schema["properties"]
        assert "phone" in json_schema["properties"]
        assert json_schema["required"] == ["name", "email"]


# =============================================================================
# ELICITATION REQUEST TESTS
# =============================================================================


class TestElicitationRequest:
    """Tests for ElicitationRequest."""

    def test_form_mode_request(self) -> None:
        """Form mode request."""
        request = ElicitationRequest(
            mode=ElicitationMode.FORM,
            message="Please fill out the form",
            schema={"type": "object", "properties": {}},
        )

        assert request.mode == ElicitationMode.FORM
        assert request.message == "Please fill out the form"
        assert request.schema is not None

    def test_url_mode_request(self) -> None:
        """URL mode request."""
        request = ElicitationRequest(
            mode=ElicitationMode.URL,
            message="Complete OAuth in browser",
            url="https://auth.example.com/authorize",
            url_reason="Authorize GitHub access",
        )

        assert request.mode == ElicitationMode.URL
        assert request.url == "https://auth.example.com/authorize"
        assert request.url_reason == "Authorize GitHub access"

    def test_to_mcp_request_form(self) -> None:
        """Form mode MCP request format."""
        request = ElicitationRequest(
            mode=ElicitationMode.FORM,
            message="Input needed",
            schema={"type": "object"},
        )
        mcp_req = request.to_mcp_request()

        assert mcp_req["mode"] == "form"
        assert mcp_req["message"] == "Input needed"
        assert mcp_req["schema"] == {"type": "object"}

    def test_to_mcp_request_url(self) -> None:
        """URL mode MCP request format."""
        request = ElicitationRequest(
            mode=ElicitationMode.URL,
            message="Navigate to URL",
            url="https://example.com",
            url_reason="Complete payment",
        )
        mcp_req = request.to_mcp_request()

        assert mcp_req["mode"] == "url"
        assert mcp_req["message"] == "Navigate to URL"
        assert mcp_req["url"] == "https://example.com"
        assert mcp_req["urlReason"] == "Complete payment"


# =============================================================================
# ELICITATION RESPONSE TESTS
# =============================================================================


class TestElicitationResponse:
    """Tests for ElicitationResponse."""

    def test_accepted_response(self) -> None:
        """Accepted response with data."""
        response = ElicitationResponse(
            accepted=True,
            data={"api_key": "sk-xxx"},
        )

        assert response.accepted is True
        assert response.data == {"api_key": "sk-xxx"}

    def test_declined_response(self) -> None:
        """Declined response with reason."""
        response = ElicitationResponse(
            accepted=False,
            declined_reason="User cancelled",
        )

        assert response.accepted is False
        assert response.declined_reason == "User cancelled"

    def test_from_mcp_response(self) -> None:
        """Create from MCP protocol response."""
        mcp_response = {
            "accepted": True,
            "data": {"name": "John", "email": "john@example.com"},
        }
        response = ElicitationResponse.from_mcp_response(mcp_response)

        assert response.accepted is True
        assert response.data["name"] == "John"

    def test_from_mcp_response_declined(self) -> None:
        """Create declined from MCP response."""
        mcp_response = {
            "accepted": False,
            "declinedReason": "User denied permission",
        }
        response = ElicitationResponse.from_mcp_response(mcp_response)

        assert response.accepted is False
        assert response.declined_reason == "User denied permission"


# =============================================================================
# ELICITATION MANAGER TESTS
# =============================================================================


class TestElicitationManager:
    """Tests for ElicitationManager."""

    @pytest.fixture
    def manager(self) -> ElicitationManager:
        """Create test manager."""
        return ElicitationManager("test-mcp-server")

    def test_request_form(self, manager: ElicitationManager) -> None:
        """Create form mode request."""
        fields = [
            FormField(name="username", required=True),
            FormField(name="password", field_type="string", required=True),
        ]
        request = manager.request_form(
            message="Enter credentials",
            fields=fields,
            title="Login",
        )

        assert request.mode == ElicitationMode.FORM
        assert request.message == "Enter credentials"
        assert request.schema is not None
        assert request.schema["title"] == "Login"

    def test_request_api_key(self, manager: ElicitationManager) -> None:
        """Request API key input."""
        request = manager.request_api_key(
            service_name="OpenAI",
            description="Your OpenAI API key from platform.openai.com",
        )

        assert request.mode == ElicitationMode.FORM
        assert "OpenAI" in request.message
        assert request.schema is not None
        assert "api_key" in request.schema["properties"]
        assert request.schema["required"] == ["api_key"]

    def test_request_confirmation(self, manager: ElicitationManager) -> None:
        """Request action confirmation."""
        request = manager.request_confirmation(
            action="Delete all files in /tmp",
            details="This action cannot be undone.",
        )

        assert request.mode == ElicitationMode.FORM
        assert "Delete all files" in request.message
        assert "cannot be undone" in request.message
        assert "confirmed" in request.schema["properties"]

    def test_request_url_interaction(self, manager: ElicitationManager) -> None:
        """Request URL mode interaction."""
        request = manager.request_url_interaction(
            url="https://checkout.stripe.com/pay/xxx",
            reason="Complete subscription payment",
            message="Please complete payment in your browser",
        )

        assert request.mode == ElicitationMode.URL
        assert request.url == "https://checkout.stripe.com/pay/xxx"
        assert request.url_reason == "Complete subscription payment"

    def test_request_oauth_flow(self, manager: ElicitationManager) -> None:
        """Request OAuth authorization flow."""
        request = manager.request_oauth_flow(
            authorization_url="https://github.com/login/oauth/authorize?...",
            service_name="GitHub",
        )

        assert request.mode == ElicitationMode.URL
        assert "github.com" in request.url
        assert "GitHub" in request.url_reason
        assert "never shared" in request.message.lower()

    def test_request_payment(self, manager: ElicitationManager) -> None:
        """Request payment flow."""
        request = manager.request_payment(
            checkout_url="https://pay.example.com/checkout/123",
            description="Premium subscription - $10/month",
        )

        assert request.mode == ElicitationMode.URL
        assert request.url == "https://pay.example.com/checkout/123"
        assert "Premium subscription" in request.url_reason
        assert "secure" in request.message.lower()


# =============================================================================
# ELICITATION CAPABILITY TESTS
# =============================================================================


class TestElicitationCapability:
    """Tests for ElicitationCapability."""

    def test_default_capabilities(self) -> None:
        """Default capabilities include form and url."""
        cap = ElicitationCapability()

        assert cap.form is True
        assert cap.url is True
        assert cap.binary_max_size is None

    def test_to_mcp_capability_minimal(self) -> None:
        """Minimal capability declaration."""
        cap = ElicitationCapability(form=True, url=False)
        mcp_cap = cap.to_mcp_capability()

        assert "form" in mcp_cap
        assert "url" not in mcp_cap

    def test_to_mcp_capability_with_binary(self) -> None:
        """Capability with binary support."""
        cap = ElicitationCapability(
            form=True,
            url=True,
            binary_max_size=10 * 1024 * 1024,  # 10MB
            binary_mime_types=["image/png", "image/jpeg", "application/pdf"],
        )
        mcp_cap = cap.to_mcp_capability()

        assert "form" in mcp_cap
        assert "url" in mcp_cap
        assert "binary" in mcp_cap
        assert mcp_cap["binary"]["maxFileSize"] == 10 * 1024 * 1024
        assert "image/png" in mcp_cap["binary"]["supportedMimeTypes"]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestElicitationIntegration:
    """Integration tests for elicitation flows."""

    def test_oauth_flow_creates_valid_request(self) -> None:
        """OAuth flow creates spec-compliant request."""
        manager = ElicitationManager("github-mcp")
        request = manager.request_oauth_flow(
            authorization_url=(
                "https://github.com/login/oauth/authorize"
                "?client_id=xxx&scope=repo&state=abc123"
            ),
            service_name="GitHub",
        )

        mcp_req = request.to_mcp_request()

        # Verify MCP spec compliance
        assert mcp_req["mode"] == "url"
        assert "url" in mcp_req
        assert "urlReason" in mcp_req
        assert "github.com" in mcp_req["url"]

    def test_form_collects_structured_data(self) -> None:
        """Form mode collects structured data with validation."""
        manager = ElicitationManager("db-mcp")
        request = manager.request_form(
            message="Configure database connection",
            fields=[
                FormField(
                    name="host",
                    description="Database host",
                    required=True,
                    pattern=r"^[\w\.\-]+$",
                ),
                FormField(
                    name="port",
                    description="Database port",
                    field_type="number",
                    required=True,
                    default=5432,
                ),
                FormField(
                    name="database",
                    description="Database name",
                    required=True,
                ),
            ],
            title="Database Configuration",
        )

        mcp_req = request.to_mcp_request()
        schema = mcp_req["schema"]

        assert schema["type"] == "object"
        assert schema["required"] == ["host", "port", "database"]
        assert schema["properties"]["host"]["pattern"] == r"^[\w\.\-]+$"
        assert schema["properties"]["port"]["type"] == "number"
        assert schema["properties"]["port"]["default"] == 5432

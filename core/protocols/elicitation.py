"""
MCP Elicitation Protocol Implementation.
=========================================

Implements MCP 2025-11-25 elicitation capabilities:
- Form mode: Structured data collection with JSON Schema
- URL mode (SEP-1036): Secure out-of-band interactions

Security Requirements:
- URL mode MUST be used for sensitive information (credentials, OAuth)
- Third-party credentials MUST NOT transit through MCP client
- Clients MUST display target domain and gather consent

References:
- MCP Elicitation: https://modelcontextprotocol.io/specification/draft/client/elicitation
- SEP-1036: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1036

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# ELICITATION TYPES
# =============================================================================


class ElicitationMode(Enum):
    """Elicitation interaction mode."""

    FORM = "form"
    URL = "url"


@dataclass
class FormField:
    """Form field definition for form mode elicitation.

    Attributes:
        name: Field identifier
        description: Human-readable description
        field_type: JSON Schema type (string, number, boolean, etc.)
        required: Whether field is required
        default: Default value
        enum: Allowed values (for select fields)
        pattern: Regex pattern for validation
    """

    name: str
    description: str = ""
    field_type: str = "string"
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    pattern: Optional[str] = None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema property definition."""
        schema: Dict[str, Any] = {"type": self.field_type}

        if self.description:
            schema["description"] = self.description
        if self.default is not None:
            schema["default"] = self.default
        if self.enum:
            schema["enum"] = self.enum
        if self.pattern:
            schema["pattern"] = self.pattern

        return schema


@dataclass
class FormSchema:
    """JSON Schema for form mode elicitation.

    Attributes:
        title: Form title
        description: Form description
        fields: List of form fields
    """

    title: str
    description: str = ""
    fields: List[FormField] = field(default_factory=list)

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to complete JSON Schema."""
        properties = {f.name: f.to_json_schema() for f in self.fields}
        required = [f.name for f in self.fields if f.required]

        return {
            "type": "object",
            "title": self.title,
            "description": self.description,
            "properties": properties,
            "required": required,
        }


@dataclass
class ElicitationRequest:
    """Request for user input via elicitation.

    For form mode: Collects structured data using JSON Schema.
    For URL mode: Directs user to external URL for sensitive flows.

    Attributes:
        mode: Elicitation mode (form or url)
        message: Message to display to user
        schema: JSON Schema for form validation (form mode)
        url: Target URL for sensitive interaction (url mode)
        url_reason: Explanation for URL navigation (url mode)
        timeout: Maximum wait time in seconds
    """

    mode: ElicitationMode
    message: str
    schema: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    url_reason: Optional[str] = None
    timeout: int = 300  # 5 minutes default

    def to_mcp_request(self) -> Dict[str, Any]:
        """Convert to MCP protocol request format."""
        request: Dict[str, Any] = {
            "mode": self.mode.value,
            "message": self.message,
        }

        if self.mode == ElicitationMode.FORM:
            if self.schema:
                request["schema"] = self.schema
        elif self.mode == ElicitationMode.URL:
            if self.url:
                request["url"] = self.url
            if self.url_reason:
                request["urlReason"] = self.url_reason

        return request


@dataclass
class ElicitationResponse:
    """Response from elicitation request.

    Attributes:
        accepted: Whether user completed the interaction
        data: Form data (form mode) or completion indicator (url mode)
        declined_reason: Reason if user declined
    """

    accepted: bool
    data: Optional[Dict[str, Any]] = None
    declined_reason: Optional[str] = None

    @classmethod
    def from_mcp_response(cls, response: Dict[str, Any]) -> "ElicitationResponse":
        """Create from MCP protocol response."""
        return cls(
            accepted=response.get("accepted", False),
            data=response.get("data"),
            declined_reason=response.get("declinedReason"),
        )


# =============================================================================
# ELICITATION MANAGER
# =============================================================================


class ElicitationManager:
    """Manages elicitation requests for MCP servers.

    Provides helper methods to create elicitation requests for
    common use cases like credentials, OAuth, and confirmations.

    Example:
        >>> manager = ElicitationManager("my-mcp-server")
        >>> # Request API key via form
        >>> request = manager.request_api_key("OpenAI API Key")
        >>> # Request OAuth via URL mode
        >>> request = manager.request_oauth_flow(
        ...     "https://auth.example.com/authorize?...",
        ...     "Connect your GitHub account"
        ... )
    """

    def __init__(self, server_name: str) -> None:
        """Initialize elicitation manager.

        Args:
            server_name: Name of MCP server (for logging)
        """
        self.server_name = server_name

    def request_form(
        self,
        message: str,
        fields: List[FormField],
        title: str = "Input Required",
    ) -> ElicitationRequest:
        """Create form mode elicitation request.

        Args:
            message: Message to display
            fields: Form fields to collect
            title: Form title

        Returns:
            ElicitationRequest for form mode
        """
        schema = FormSchema(title=title, fields=fields)

        return ElicitationRequest(
            mode=ElicitationMode.FORM,
            message=message,
            schema=schema.to_json_schema(),
        )

    def request_api_key(
        self,
        service_name: str,
        description: str = "",
    ) -> ElicitationRequest:
        """Create request for API key input.

        Uses form mode for non-sensitive key collection.
        For production, consider URL mode with secure input.

        Args:
            service_name: Name of the service (e.g., "OpenAI")
            description: Additional instructions

        Returns:
            ElicitationRequest
        """
        fields = [
            FormField(
                name="api_key",
                description=description or f"Enter your {service_name} API key",
                field_type="string",
                required=True,
            )
        ]

        return self.request_form(
            message=f"Please provide your {service_name} API key to continue.",
            fields=fields,
            title=f"{service_name} API Key",
        )

    def request_confirmation(
        self,
        action: str,
        details: Optional[str] = None,
    ) -> ElicitationRequest:
        """Create confirmation request.

        Args:
            action: Description of action requiring confirmation
            details: Additional details

        Returns:
            ElicitationRequest
        """
        fields = [
            FormField(
                name="confirmed",
                description="Confirm this action",
                field_type="boolean",
                required=True,
                default=False,
            )
        ]

        message = f"Please confirm: {action}"
        if details:
            message += f"\n\n{details}"

        return self.request_form(
            message=message,
            fields=fields,
            title="Confirmation Required",
        )

    def request_url_interaction(
        self,
        url: str,
        reason: str,
        message: Optional[str] = None,
    ) -> ElicitationRequest:
        """Create URL mode elicitation request.

        Use for sensitive interactions that should not pass
        through the MCP client (OAuth, payments, credentials).

        Args:
            url: Target URL for user interaction
            reason: Why URL navigation is needed
            message: Optional custom message

        Returns:
            ElicitationRequest for URL mode
        """
        return ElicitationRequest(
            mode=ElicitationMode.URL,
            message=message or "Please complete the following action in your browser.",
            url=url,
            url_reason=reason,
        )

    def request_oauth_flow(
        self,
        authorization_url: str,
        service_name: str,
    ) -> ElicitationRequest:
        """Create OAuth flow elicitation request.

        Directs user to OAuth authorization URL in browser.
        Credentials never transit through MCP client.

        Args:
            authorization_url: OAuth authorization endpoint with params
            service_name: Name of service being authorized

        Returns:
            ElicitationRequest for URL mode
        """
        return self.request_url_interaction(
            url=authorization_url,
            reason=f"Authorize {self.server_name} to access your {service_name} account",
            message=(
                f"To connect your {service_name} account, you'll be redirected "
                "to authorize in your browser. Your credentials are never shared "
                "with the MCP client."
            ),
        )

    def request_payment(
        self,
        checkout_url: str,
        description: str,
    ) -> ElicitationRequest:
        """Create payment elicitation request.

        Directs user to secure payment page.
        PCI-compliant: payment details never touch MCP.

        Args:
            checkout_url: Payment/checkout URL
            description: What user is paying for

        Returns:
            ElicitationRequest for URL mode
        """
        return self.request_url_interaction(
            url=checkout_url,
            reason=description,
            message=(
                "You'll be redirected to a secure payment page. "
                "Your payment information is handled securely and never "
                "shared with the MCP client."
            ),
        )


# =============================================================================
# CLIENT CAPABILITY DECLARATION
# =============================================================================


@dataclass
class ElicitationCapability:
    """Client elicitation capability declaration.

    Clients declare supported modes during initialization.

    Attributes:
        form: Support for form mode
        url: Support for URL mode
        binary_max_size: Max file size for binary mode (bytes)
        binary_mime_types: Supported MIME types for binary mode
    """

    form: bool = True
    url: bool = True
    binary_max_size: Optional[int] = None
    binary_mime_types: Optional[List[str]] = None

    def to_mcp_capability(self) -> Dict[str, Any]:
        """Convert to MCP capability declaration."""
        capability: Dict[str, Any] = {}

        if self.form:
            capability["form"] = {}
        if self.url:
            capability["url"] = {}
        if self.binary_max_size is not None:
            capability["binary"] = {
                "maxFileSize": self.binary_max_size,
                "supportedMimeTypes": self.binary_mime_types or ["*/*"],
            }

        return capability


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ElicitationMode",
    "FormField",
    "FormSchema",
    "ElicitationRequest",
    "ElicitationResponse",
    "ElicitationManager",
    "ElicitationCapability",
]

"""Testes para Open Responses Fase 2."""

import pytest
from vertice_core.openresponses_types import (
    ReasoningItem,
    SummaryTextContent,
    UrlCitation,
    JsonSchemaResponseFormat,
    VerticeTelemetryItem,
    VerticeGovernanceItem,
    ItemStatus,
    OutputTextContent,
)


class TestReasoningItem:
    """Testes para ReasoningItem."""

    def test_creation(self):
        item = ReasoningItem()
        assert item.type == "reasoning"
        assert item.id.startswith("rs_")
        assert item.status == ItemStatus.IN_PROGRESS
        assert item.content == []
        assert item.summary == []
        assert item.encrypted_content is None

    def test_append_content(self):
        item = ReasoningItem()
        item.append_content("Step 1: Analyze")
        item.append_content(" Step 2: Process")
        assert item.get_reasoning_text() == "Step 1: Analyze Step 2: Process"

    def test_set_summary(self):
        item = ReasoningItem()
        item.set_summary("Analyzed user request and found solution.")
        assert len(item.summary) == 1
        assert item.get_summary_text() == "Analyzed user request and found solution."

    def test_to_dict(self):
        item = ReasoningItem()
        item.append_content("Thinking...")
        item.set_summary("Short summary")
        item.status = ItemStatus.COMPLETED

        d = item.to_dict()
        assert d["type"] == "reasoning"
        assert d["status"] == "completed"
        assert len(d["content"]) == 1
        assert len(d["summary"]) == 1


class TestSummaryTextContent:
    """Testes para SummaryTextContent."""

    def test_creation(self):
        summary = SummaryTextContent(text="This is a summary")
        assert summary.type == "summary_text"
        assert summary.text == "This is a summary"

    def test_to_dict(self):
        summary = SummaryTextContent(text="Summary content")
        d = summary.to_dict()
        assert d["type"] == "summary_text"
        assert d["text"] == "Summary content"


class TestUrlCitation:
    """Testes para UrlCitation."""

    def test_creation(self):
        citation = UrlCitation(
            url="https://example.com",
            title="Example",
            start_index=0,
            end_index=50,
        )
        assert citation.type == "url_citation"
        assert citation.url == "https://example.com"

    def test_to_dict(self):
        citation = UrlCitation(url="https://example.com", start_index=10, end_index=20)
        d = citation.to_dict()
        assert d["url"] == "https://example.com"
        assert d["start_index"] == 10
        assert d["end_index"] == 20

    def test_to_dict_with_title(self):
        citation = UrlCitation(
            url="https://example.com", title="Example Site", start_index=0, end_index=30
        )
        d = citation.to_dict()
        assert d["title"] == "Example Site"


class TestOutputTextContentAnnotations:
    """Testes para annotations em OutputTextContent."""

    def test_add_citation(self):
        content = OutputTextContent(text="Python was created by Guido van Rossum.")
        content.add_citation("https://python.org", "Python Official Site", 0, 20)

        assert len(content.annotations) == 1
        citation = content.annotations[0]
        assert citation.url == "https://python.org"
        assert citation.title == "Python Official Site"
        assert citation.start_index == 0
        assert citation.end_index == 20

    def test_to_dict_with_annotations(self):
        content = OutputTextContent(text="Test text")
        content.add_citation("https://example.com")

        d = content.to_dict()
        assert d["type"] == "output_text"
        assert d["text"] == "Test text"
        assert len(d["annotations"]) == 1
        assert d["annotations"][0]["type"] == "url_citation"


class TestJsonSchemaResponseFormat:
    """Testes para JsonSchemaResponseFormat."""

    def test_creation(self):
        schema_format = JsonSchemaResponseFormat(
            name="user_info",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name"],
            },
        )
        assert schema_format.type == "json_schema"
        assert schema_format.name == "user_info"
        assert schema_format.strict is True

    def test_to_dict(self):
        schema_format = JsonSchemaResponseFormat(name="test", schema={"type": "object"})
        d = schema_format.to_dict()
        assert d["type"] == "json_schema"
        assert d["json_schema"]["name"] == "test"
        assert d["json_schema"]["strict"] is True

    def test_to_dict_with_description(self):
        schema_format = JsonSchemaResponseFormat(
            name="test", description="Test schema", schema={"type": "object"}
        )
        d = schema_format.to_dict()
        assert d["json_schema"]["description"] == "Test schema"


class TestVerticeExtensions:
    """Testes para extensões Vertice."""

    def test_telemetry_item(self):
        item = VerticeTelemetryItem(
            latency_ms=142,
            cache_hit=False,
            model="gemini-3-pro",
            provider="vertex-ai",
        )
        assert item.type == "vertice:telemetry"
        assert item.id.startswith("vt_")

        d = item.to_dict()
        assert d["latency_ms"] == 142
        assert d["model"] == "gemini-3-pro"

    def test_governance_item(self):
        item = VerticeGovernanceItem(
            allowed=True,
            reason="All checks passed",
            violations=[],
        )
        assert item.type == "vertice:governance"
        assert item.id.startswith("vg_")
        assert item.allowed is True

        d = item.to_dict()
        assert d["allowed"] is True
        assert d["reason"] == "All checks passed"

    def test_governance_item_with_violations(self):
        item = VerticeGovernanceItem(
            allowed=False,
            violations=["Inappropriate content", "Security risk"],
            checked_at="2026-01-16T10:00:00Z",
        )
        assert item.allowed is False
        assert len(item.violations) == 2

        d = item.to_dict()
        assert d["allowed"] is False
        assert len(d["violations"]) == 2
        assert d["checked_at"] == "2026-01-16T10:00:00Z"

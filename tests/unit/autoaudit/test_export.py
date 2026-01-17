"""
Tests for AutoAudit Export Logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from vertice_tui.core.autoaudit.export import export_html, export_json
from vertice_tui.core.autoaudit.service import AuditReport, ScenarioResult


@pytest.fixture
def dummy_report():
    return AuditReport(
        started_at="2023-01-01T00:00:00",
        ended_at="2023-01-01T00:01:00",
        total_scenarios=2,
        passed=1,
        failed=1,
        skipped=0,
        critical_errors=0,
        results=[
            ScenarioResult("s1", "SUCCESS", 0, 1, 1000, {"check": True}, ""),
            ScenarioResult("s2", "FAILURE", 0, 1, 1000, {"check": False}, "Error msg"),
        ],
    )


def test_export_html_generation(dummy_report):
    """Test HTML generation and file writing."""
    with patch("pathlib.Path.write_text") as mock_write, patch("pathlib.Path.mkdir"):
        # Test default path generation
        path = export_html(dummy_report)
        assert path.endswith(".html")

        mock_write.assert_called_once()
        content = mock_write.call_args[0][0]

        assert "<!DOCTYPE html>" in content
        assert "AutoAudit Report" in content
        assert "SUCCESS" in content
        assert "FAILURE" in content
        assert "Error msg" in content


def test_export_json_generation(dummy_report):
    """Test JSON serialization."""
    with patch("builtins.open", new_callable=MagicMock) as mock_open, patch("pathlib.Path.mkdir"):
        path = export_json(dummy_report)
        assert path.endswith(".json")

        # Check if json.dump was called
        # Getting the file handle from the context manager
        _ = mock_open.return_value.__enter__.return_value

        # Ideally we capture what was written, but with json.dump it writes to the handle
        # We can mock json.dump instead
        with patch("json.dump") as mock_dump:
            export_json(dummy_report)
            mock_dump.assert_called()
            args = mock_dump.call_args[0]
            data = args[0]
            assert data["passed"] == 1
            assert len(data["results"]) == 2

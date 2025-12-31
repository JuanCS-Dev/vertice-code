"""
Phase 5 TUI Lightweight - Complete Test Suite
==============================================

100% coverage for all extracted modules:
- prompt_sections.py
- help_builder.py
- plan_executor.py
- tool_sanitizer.py
- command_whitelist.py
- app_styles.py

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List


# =============================================================================
# TEST: prompt_sections.py
# =============================================================================

class TestPromptSections:
    """Test prompt section constants and structure."""

    def test_identity_is_string(self) -> None:
        """Test IDENTITY is a non-empty string."""
        from vertice_tui.core.prompt_sections import IDENTITY
        assert isinstance(IDENTITY, str)
        assert len(IDENTITY) > 100
        assert "PROMETHEUS" in IDENTITY

    def test_agentic_behavior_contains_loop(self) -> None:
        """Test AGENTIC_BEHAVIOR contains the agentic loop."""
        from vertice_tui.core.prompt_sections import AGENTIC_BEHAVIOR
        assert "while(task_not_complete)" in AGENTIC_BEHAVIOR
        assert "GATHER" in AGENTIC_BEHAVIOR
        assert "ACT" in AGENTIC_BEHAVIOR
        assert "VERIFY" in AGENTIC_BEHAVIOR

    def test_tool_protocol_has_rules(self) -> None:
        """Test TOOL_PROTOCOL has usage rules."""
        from vertice_tui.core.prompt_sections import TOOL_PROTOCOL
        assert "Rules" in TOOL_PROTOCOL
        assert "tool" in TOOL_PROTOCOL.lower()

    def test_nlu_section_has_examples(self) -> None:
        """Test NLU_SECTION has intent examples."""
        from vertice_tui.core.prompt_sections import NLU_SECTION
        assert "Intent Recognition" in NLU_SECTION
        assert "User Says" in NLU_SECTION

    def test_patterns_section_has_workflows(self) -> None:
        """Test PATTERNS_SECTION has common workflows."""
        from vertice_tui.core.prompt_sections import PATTERNS_SECTION
        assert "Create New Feature" in PATTERNS_SECTION
        assert "Fix Bug" in PATTERNS_SECTION
        assert "Git Workflow" in PATTERNS_SECTION

    def test_safety_section_has_guidelines(self) -> None:
        """Test SAFETY_SECTION has safety guidelines."""
        from vertice_tui.core.prompt_sections import SAFETY_SECTION
        assert "Always" in SAFETY_SECTION
        assert "Never" in SAFETY_SECTION

    def test_style_section_has_formatting(self) -> None:
        """Test STYLE_SECTION has formatting rules."""
        from vertice_tui.core.prompt_sections import STYLE_SECTION
        assert "Markdown" in STYLE_SECTION
        assert "TABLES" in STYLE_SECTION

    def test_tool_guidance_dict(self) -> None:
        """Test TOOL_GUIDANCE is a dict with tool names."""
        from vertice_tui.core.prompt_sections import TOOL_GUIDANCE
        assert isinstance(TOOL_GUIDANCE, dict)
        assert "read_file" in TOOL_GUIDANCE
        assert "write_file" in TOOL_GUIDANCE
        assert "bash" in TOOL_GUIDANCE

    def test_error_guidance_string(self) -> None:
        """Test ERROR_GUIDANCE is a helpful string."""
        from vertice_tui.core.prompt_sections import ERROR_GUIDANCE
        assert isinstance(ERROR_GUIDANCE, str)
        assert "error" in ERROR_GUIDANCE.lower()


# =============================================================================
# TEST: help_builder.py
# =============================================================================

class TestHelpBuilder:
    """Test help building functions."""

    def test_tool_categories_defined(self) -> None:
        """Test TOOL_CATEGORIES has expected categories."""
        from vertice_tui.core.help_builder import TOOL_CATEGORIES
        assert "File" in TOOL_CATEGORIES
        assert "Terminal" in TOOL_CATEGORIES
        assert "Git" in TOOL_CATEGORIES
        assert "Web" in TOOL_CATEGORIES

    def test_agent_commands_defined(self) -> None:
        """Test AGENT_COMMANDS has expected commands."""
        from vertice_tui.core.help_builder import AGENT_COMMANDS
        assert "/plan" in AGENT_COMMANDS
        assert "/review" in AGENT_COMMANDS
        assert "/test" in AGENT_COMMANDS
        assert AGENT_COMMANDS["/plan"] == "planner"

    def test_build_tool_list_empty(self) -> None:
        """Test build_tool_list with empty list."""
        from vertice_tui.core.help_builder import build_tool_list
        result = build_tool_list([])
        assert result == "No tools loaded."

    def test_build_tool_list_with_tools(self) -> None:
        """Test build_tool_list with tools."""
        from vertice_tui.core.help_builder import build_tool_list
        tools = ["read_file", "write_file", "bash_command", "git_status"]
        result = build_tool_list(tools)
        assert "File" in result
        assert "read_file" in result
        assert "Execution" in result
        assert "Git" in result

    def test_build_tool_list_uncategorized(self) -> None:
        """Test build_tool_list with uncategorized tools."""
        from vertice_tui.core.help_builder import build_tool_list
        tools = ["custom_tool", "another_tool"]
        result = build_tool_list(tools)
        assert "Other" in result
        assert "custom_tool" in result

    def test_build_command_help_empty_registry(self) -> None:
        """Test build_command_help with empty registry."""
        from vertice_tui.core.help_builder import build_command_help
        result = build_command_help({})
        assert "Agent Commands" in result

    def test_build_command_help_with_agents(self) -> None:
        """Test build_command_help with agents."""
        from vertice_tui.core.help_builder import build_command_help
        from dataclasses import dataclass

        @dataclass
        class MockAgentInfo:
            description: str

        registry = {
            "planner": MockAgentInfo(description="Plans tasks"),
            "reviewer": MockAgentInfo(description="Reviews code"),
        }
        result = build_command_help(registry)
        assert "/plan" in result
        assert "Plans tasks" in result

    def test_get_agent_commands_returns_copy(self) -> None:
        """Test get_agent_commands returns a copy."""
        from vertice_tui.core.help_builder import get_agent_commands, AGENT_COMMANDS
        result = get_agent_commands()
        assert result == AGENT_COMMANDS
        # Ensure it's a copy
        result["/new"] = "new"
        assert "/new" not in AGENT_COMMANDS


# =============================================================================
# TEST: plan_executor.py
# =============================================================================

class TestPlanExecutor:
    """Test plan execution detection."""

    def test_execute_patterns_exist(self) -> None:
        """Test EXECUTE_PATTERNS is defined."""
        from vertice_tui.core.plan_executor import EXECUTE_PATTERNS
        assert isinstance(EXECUTE_PATTERNS, list)
        assert len(EXECUTE_PATTERNS) > 0

    @pytest.mark.parametrize("message", [
        "make it real",
        "do it",
        "build it",
        "create it",
        "go",
        "let's go",
        "vamos",
        "bora",
        "execute the plan",
        "run the plan",
        "implement",
        "create the files",
        "write the files",
        "generate the code",
        "materializa",
        "faz isso",
        "cria os arquivos",
    ])
    def test_is_plan_execution_request_positive(self, message: str) -> None:
        """Test is_plan_execution_request detects execution requests."""
        from vertice_tui.core.plan_executor import is_plan_execution_request
        assert is_plan_execution_request(message) is True

    @pytest.mark.parametrize("message", [
        "hello",
        "what is this?",
        "explain the code",
        "help me understand",
        "show me the plan",
        "review this",
    ])
    def test_is_plan_execution_request_negative(self, message: str) -> None:
        """Test is_plan_execution_request rejects non-execution requests."""
        from vertice_tui.core.plan_executor import is_plan_execution_request
        assert is_plan_execution_request(message) is False

    def test_prepare_plan_execution_no_plan(self) -> None:
        """Test prepare_plan_execution with no saved plan."""
        from vertice_tui.core.plan_executor import prepare_plan_execution
        message, skip, preamble = prepare_plan_execution("make it real", None)
        assert message == "make it real"
        assert skip is False
        assert preamble is None

    def test_prepare_plan_execution_not_execution_request(self) -> None:
        """Test prepare_plan_execution with non-execution message."""
        from vertice_tui.core.plan_executor import prepare_plan_execution
        plan = "Create file main.py"
        message, skip, preamble = prepare_plan_execution("hello", plan)
        assert message == "hello"
        assert skip is False
        assert preamble is None

    def test_prepare_plan_execution_with_plan(self) -> None:
        """Test prepare_plan_execution with valid execution request."""
        from vertice_tui.core.plan_executor import prepare_plan_execution
        plan = "Step 1: Create main.py\nStep 2: Add tests"
        message, skip, preamble = prepare_plan_execution("make it real", plan)
        assert "Execute this plan" in message
        assert plan[:100] in message
        assert skip is True
        assert "Executing saved plan" in preamble


# =============================================================================
# TEST: tool_sanitizer.py
# =============================================================================

class TestToolSanitizer:
    """Test tool call sanitization."""

    def test_tool_patterns_exist(self) -> None:
        """Test _TOOL_PATTERNS is defined."""
        from vertice_tui.components.tool_sanitizer import _TOOL_PATTERNS
        assert isinstance(_TOOL_PATTERNS, list)
        assert len(_TOOL_PATTERNS) > 0

    def test_format_tool_call_bash(self) -> None:
        """Test _format_tool_call for bash commands."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("bash_command", {"command": "ls -la"})
        assert "```bash" in result
        assert "ls -la" in result

    def test_format_tool_call_bash_alt_key(self) -> None:
        """Test _format_tool_call for bash with 'cmd' key."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("bash", {"cmd": "pwd"})
        assert "```bash" in result
        assert "pwd" in result

    def test_format_tool_call_write_file(self) -> None:
        """Test _format_tool_call for write_file."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("write_file", {"path": "main.py"})
        assert "Escrevendo" in result
        assert "main.py" in result

    def test_format_tool_call_read_file(self) -> None:
        """Test _format_tool_call for read_file."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("read_file", {"file_path": "test.py"})
        assert "Lendo" in result
        assert "test.py" in result

    def test_format_tool_call_edit_file(self) -> None:
        """Test _format_tool_call for edit_file."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("edit_file", {"path": "config.py"})
        assert "Editando" in result

    def test_format_tool_call_web_search(self) -> None:
        """Test _format_tool_call for web_search."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("web_search", {"query": "python docs"})
        assert "Pesquisando" in result
        assert "python docs" in result

    def test_format_tool_call_web_fetch(self) -> None:
        """Test _format_tool_call for web_fetch."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("web_fetch", {"url": "https://example.com"})
        assert "Acessando" in result

    def test_format_tool_call_generic(self) -> None:
        """Test _format_tool_call for unknown tool."""
        from vertice_tui.components.tool_sanitizer import _format_tool_call
        result = _format_tool_call("custom_tool", {"arg1": "val1"})
        assert "custom_tool" in result
        assert "arg1" in result

    def test_sanitize_tool_call_json_no_match(self) -> None:
        """Test sanitize_tool_call_json with no tool calls."""
        from vertice_tui.components.tool_sanitizer import sanitize_tool_call_json
        result = sanitize_tool_call_json("Hello world")
        assert result == "Hello world"

    def test_sanitize_tool_call_json_tool_format(self) -> None:
        """Test sanitize_tool_call_json with tool format."""
        from vertice_tui.components.tool_sanitizer import sanitize_tool_call_json
        chunk = '{"tool": "bash_command", "args": {"command": "ls"}}'
        result = sanitize_tool_call_json(chunk)
        assert "```bash" in result
        assert "ls" in result

    def test_sanitize_tool_call_json_name_format(self) -> None:
        """Test sanitize_tool_call_json with name/arguments format."""
        from vertice_tui.components.tool_sanitizer import sanitize_tool_call_json
        chunk = '{"name": "read_file", "arguments": {"path": "test.py"}}'
        result = sanitize_tool_call_json(chunk)
        assert "Lendo" in result

    def test_sanitize_tool_call_json_invalid_json(self) -> None:
        """Test sanitize_tool_call_json with invalid JSON in args."""
        from vertice_tui.components.tool_sanitizer import sanitize_tool_call_json
        # This should return original if JSON parsing fails
        chunk = '{"tool": "bash", "args": {invalid}}'
        result = sanitize_tool_call_json(chunk)
        # Pattern won't match invalid JSON structure
        assert result == chunk


# =============================================================================
# TEST: command_whitelist.py
# =============================================================================

class TestCommandWhitelist:
    """Test command whitelist definitions."""

    def test_command_category_enum(self) -> None:
        """Test CommandCategory enum values."""
        from vertice_tui.core.command_whitelist import CommandCategory
        assert CommandCategory.TESTING.value == "testing"
        assert CommandCategory.LINTING.value == "linting"
        assert CommandCategory.GIT.value == "git"
        assert CommandCategory.FILE_SYSTEM.value == "file_system"

    def test_allowed_command_dataclass(self) -> None:
        """Test AllowedCommand is frozen dataclass."""
        from vertice_tui.core.command_whitelist import AllowedCommand, CommandCategory
        cmd = AllowedCommand(
            name="test",
            base_command="pytest",
            allowed_args=frozenset({"-v"}),
            category=CommandCategory.TESTING,
            timeout_seconds=60,
            description="Test command"
        )
        assert cmd.name == "test"
        assert cmd.base_command == "pytest"
        assert "-v" in cmd.allowed_args
        # Test frozen
        with pytest.raises(Exception):
            cmd.name = "changed"  # type: ignore

    def test_allowed_commands_dict_exists(self) -> None:
        """Test ALLOWED_COMMANDS dict is populated."""
        from vertice_tui.core.command_whitelist import ALLOWED_COMMANDS
        assert isinstance(ALLOWED_COMMANDS, dict)
        assert len(ALLOWED_COMMANDS) > 10
        assert "pytest" in ALLOWED_COMMANDS
        assert "git status" in ALLOWED_COMMANDS
        assert "ls" in ALLOWED_COMMANDS

    def test_allowed_commands_have_required_fields(self) -> None:
        """Test all ALLOWED_COMMANDS have required fields."""
        from vertice_tui.core.command_whitelist import ALLOWED_COMMANDS
        for key, cmd in ALLOWED_COMMANDS.items():
            assert cmd.name, f"{key} missing name"
            assert cmd.base_command, f"{key} missing base_command"
            assert cmd.category, f"{key} missing category"
            assert cmd.timeout_seconds > 0, f"{key} invalid timeout"

    def test_dangerous_patterns_frozenset(self) -> None:
        """Test DANGEROUS_PATTERNS is a frozenset."""
        from vertice_tui.core.command_whitelist import DANGEROUS_PATTERNS
        assert isinstance(DANGEROUS_PATTERNS, frozenset)
        assert len(DANGEROUS_PATTERNS) > 10

    @pytest.mark.parametrize("pattern", [
        "rm ", "sudo", "chmod", "chown", "eval", "exec",
        ";", "&&", "||", "| sh", "| bash",
    ])
    def test_dangerous_patterns_contains_expected(self, pattern: str) -> None:
        """Test DANGEROUS_PATTERNS contains security-critical patterns."""
        from vertice_tui.core.command_whitelist import DANGEROUS_PATTERNS
        assert pattern in DANGEROUS_PATTERNS


# =============================================================================
# TEST: app_styles.py
# =============================================================================

class TestAppStyles:
    """Test app styles and language detection."""

    def test_app_css_is_string(self) -> None:
        """Test APP_CSS is a valid CSS string."""
        from vertice_tui.app_styles import APP_CSS
        assert isinstance(APP_CSS, str)
        assert "Screen" in APP_CSS
        assert "background" in APP_CSS
        assert "#main" in APP_CSS
        assert "#prompt" in APP_CSS

    def test_language_map_exists(self) -> None:
        """Test LANGUAGE_MAP has common extensions."""
        from vertice_tui.app_styles import LANGUAGE_MAP
        assert isinstance(LANGUAGE_MAP, dict)
        assert LANGUAGE_MAP[".py"] == "python"
        assert LANGUAGE_MAP[".js"] == "javascript"
        assert LANGUAGE_MAP[".ts"] == "typescript"
        assert LANGUAGE_MAP[".json"] == "json"
        assert LANGUAGE_MAP[".md"] == "markdown"

    @pytest.mark.parametrize("suffix,expected", [
        (".py", "python"),
        (".js", "javascript"),
        (".ts", "typescript"),
        (".jsx", "javascript"),
        (".tsx", "typescript"),
        (".json", "json"),
        (".yaml", "yaml"),
        (".yml", "yaml"),
        (".md", "markdown"),
        (".sh", "bash"),
        (".html", "html"),
        (".css", "css"),
        (".sql", "sql"),
        (".rs", "rust"),
        (".go", "go"),
        (".java", "java"),
        (".rb", "ruby"),
        (".toml", "toml"),
    ])
    def test_detect_language_known(self, suffix: str, expected: str) -> None:
        """Test detect_language for known extensions."""
        from vertice_tui.app_styles import detect_language
        assert detect_language(suffix) == expected

    def test_detect_language_unknown(self) -> None:
        """Test detect_language for unknown extension."""
        from vertice_tui.app_styles import detect_language
        assert detect_language(".xyz") == "text"
        assert detect_language(".unknown") == "text"

    def test_detect_language_case_insensitive(self) -> None:
        """Test detect_language is case insensitive."""
        from vertice_tui.app_styles import detect_language
        assert detect_language(".PY") == "python"
        assert detect_language(".Js") == "javascript"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPhase5Integration:
    """Integration tests for Phase 5 modules working together."""

    def test_bridge_imports_help_builder(self) -> None:
        """Test bridge can import help_builder functions."""
        from vertice_tui.core.help_builder import build_tool_list, build_command_help, get_agent_commands
        # Just verify imports work
        assert callable(build_tool_list)
        assert callable(build_command_help)
        assert callable(get_agent_commands)

    def test_bridge_imports_plan_executor(self) -> None:
        """Test bridge can import plan_executor functions."""
        from vertice_tui.core.plan_executor import is_plan_execution_request, prepare_plan_execution
        assert callable(is_plan_execution_request)
        assert callable(prepare_plan_execution)

    def test_agentic_prompt_imports_sections(self) -> None:
        """Test agentic_prompt can import prompt_sections."""
        from vertice_tui.core.prompt_sections import (
            IDENTITY, AGENTIC_BEHAVIOR, TOOL_PROTOCOL,
            NLU_SECTION, PATTERNS_SECTION, SAFETY_SECTION,
            STYLE_SECTION, TOOL_GUIDANCE, ERROR_GUIDANCE
        )
        # Verify all are non-empty strings or dicts
        assert IDENTITY
        assert AGENTIC_BEHAVIOR
        assert TOOL_PROTOCOL
        assert NLU_SECTION
        assert PATTERNS_SECTION
        assert SAFETY_SECTION
        assert STYLE_SECTION
        assert TOOL_GUIDANCE
        assert ERROR_GUIDANCE

    def test_streaming_adapter_imports_sanitizer(self) -> None:
        """Test streaming_adapter can import tool_sanitizer."""
        from vertice_tui.components.tool_sanitizer import sanitize_tool_call_json
        assert callable(sanitize_tool_call_json)

    def test_safe_executor_imports_whitelist(self) -> None:
        """Test safe_executor can import command_whitelist."""
        from vertice_tui.core.command_whitelist import (
            AllowedCommand, CommandCategory,
            ALLOWED_COMMANDS, DANGEROUS_PATTERNS
        )
        assert AllowedCommand
        assert CommandCategory
        assert ALLOWED_COMMANDS
        assert DANGEROUS_PATTERNS

    def test_app_imports_styles(self) -> None:
        """Test app can import app_styles."""
        from vertice_tui.app_styles import APP_CSS, detect_language
        assert APP_CSS
        assert callable(detect_language)

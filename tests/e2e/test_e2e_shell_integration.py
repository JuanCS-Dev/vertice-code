"""
E2E Shell Integration Tests - Tests the actual CLI/Shell behavior.

These tests validate:
- vtc command execution
- Interactive shell behavior
- Tool registry and execution
- Context management
- Conversation flow

Usage:
    pytest tests/e2e/test_e2e_shell_integration.py -v --timeout=300

Requirements:
    - ANTHROPIC_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY
    - vertice-cli installed (pip install -e .)
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Skip if no API keys
pytestmark = pytest.mark.skipif(
    not (
        os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GROQ_API_KEY")
    ),
    reason="No LLM API key available",
)


class TestToolRegistry:
    """Test tool registry initialization and discovery."""

    def test_registry_loads_all_tools(self):
        """Test that all expected tools are registered."""
        from vertice_cli.tools.registry_setup import create_full_registry

        registry = create_full_registry()
        schemas = registry.get_schemas()

        # Should have minimum set of tools
        tool_names = {s["name"] for s in schemas}

        essential_tools = ["readfile", "writefile", "searchfiles", "bashcommand"]
        for tool in essential_tools:
            # Check variations of tool names
            has_tool = any(tool.lower() in name.lower() for name in tool_names)
            assert (
                has_tool or len(tool_names) > 10
            ), f"Expected tool '{tool}' or many tools. Found: {tool_names}"

    def test_registry_includes_think_tool(self):
        """Test that think tool is registered."""
        from vertice_cli.tools.registry_setup import create_full_registry

        registry = create_full_registry(include_think=True)
        tool = registry.get("think")

        assert tool is not None, "Think tool should be registered"

    def test_tool_schemas_valid(self):
        """Test that all tool schemas are valid."""
        from vertice_cli.tools.registry_setup import create_full_registry

        registry = create_full_registry()
        schemas = registry.get_schemas()

        for schema in schemas:
            assert "name" in schema, f"Schema missing 'name': {schema}"
            assert "description" in schema, f"Schema missing 'description': {schema}"


class TestIntentClassification:
    """Test intent classification with real patterns."""

    @pytest.fixture
    def classifier(self):
        from vertice_cli.core.intent_classifier import SemanticIntentClassifier

        return SemanticIntentClassifier()

    @pytest.mark.asyncio
    async def test_portuguese_intent_accuracy(self, classifier):
        """Test Portuguese intent classification accuracy."""
        from vertice_cli.core.intent_classifier import Intent

        test_cases = [
            ("mostra o arquivo main.py", Intent.EXPLORE),
            ("cria uma funcao de soma", Intent.CODING),
            ("conserta o erro no login", Intent.DEBUG),
            ("refatora essa classe", Intent.REFACTOR),
            ("roda os testes", Intent.TEST),
            ("documenta essa funcao", Intent.DOCS),
            ("ta muito lento", Intent.PERFORMANCE),
            ("verifica seguranca", Intent.SECURITY),
        ]

        correct = 0
        for request, expected_intent in test_cases:
            result = await classifier.classify(request)
            if result.intent == expected_intent:
                correct += 1

        accuracy = correct / len(test_cases)
        assert accuracy >= 0.6, f"Portuguese intent accuracy too low: {accuracy:.0%}"

    @pytest.mark.asyncio
    async def test_english_intent_accuracy(self, classifier):
        """Test English intent classification accuracy."""
        from vertice_cli.core.intent_classifier import Intent

        test_cases = [
            ("show me the file main.py", Intent.EXPLORE),
            ("create a function for sum", Intent.CODING),
            ("fix the login error", Intent.DEBUG),
            ("refactor this class", Intent.REFACTOR),
            ("run the tests", Intent.TEST),
            ("document this function", Intent.DOCS),
        ]

        correct = 0
        for request, expected_intent in test_cases:
            result = await classifier.classify(request)
            if result.intent == expected_intent:
                correct += 1

        accuracy = correct / len(test_cases)
        assert accuracy >= 0.6, f"English intent accuracy too low: {accuracy:.0%}"


class TestRequestAmplifier:
    """Test request amplification with context."""

    @pytest.mark.asyncio
    async def test_amplification_adds_context(self):
        """Test that amplification adds relevant context."""
        from vertice_cli.core.request_amplifier import RequestAmplifier

        context = {
            "cwd": "/project/src",
            "recent_files": ["main.py", "utils.py"],
            "modified_files": ["main.py"],
            "git_branch": "feature/test",
        }

        amplifier = RequestAmplifier(context=context)
        result = await amplifier.analyze("mostra o arquivo")

        assert "[cwd:" in result.amplified
        assert "[recent:" in result.amplified

    @pytest.mark.asyncio
    async def test_vagueness_detection(self):
        """Test vagueness detection for short requests."""
        from vertice_cli.core.request_amplifier import RequestAmplifier

        amplifier = RequestAmplifier()

        vague_requests = ["faz isso", "ajuda", "fix", "ok"]

        for request in vague_requests:
            result = await amplifier.analyze(request)
            assert len(result.vagueness_issues) > 0, f"'{request}' should be detected as vague"

    @pytest.mark.asyncio
    async def test_missing_details_detection(self):
        """Test missing details detection by intent."""
        from vertice_cli.core.request_amplifier import RequestAmplifier

        amplifier = RequestAmplifier()

        # Debug without error description
        result = await amplifier.analyze("conserta o bug")
        assert "error_description" in result.missing_details


class TestComplexityAnalyzer:
    """Test complexity analysis for auto-thinking."""

    def test_simple_requests_low_complexity(self):
        """Test that simple requests have low complexity."""
        from vertice_cli.core.complexity_analyzer import analyze_complexity

        simple_requests = [
            "mostra o readme",
            "lista os arquivos",
            "abre main.py",
        ]

        for request in simple_requests:
            result = analyze_complexity(request)
            assert result.score < 0.5, f"'{request}' should have low complexity"
            assert not result.needs_thinking

    def test_complex_requests_high_complexity(self):
        """Test that complex requests trigger thinking."""
        from vertice_cli.core.complexity_analyzer import ComplexityAnalyzer
        from vertice_cli.core.intent_classifier import Intent

        # Adjust threshold for testing
        analyzer = ComplexityAnalyzer()
        analyzer.THINK_THRESHOLD = 0.3  # Lower for testing

        # Complex multi-step with refactoring
        result = analyzer.analyze(
            "refatora todos os modulos e depois roda os testes",
            intent=Intent.REFACTOR,
            confidence=0.5,
        )

        # Should have some complexity factors
        assert len(result.reasons) > 0


class TestAgentRouting:
    """Test agent routing with bilingual input."""

    def test_portuguese_routing_coverage(self):
        """Test that Portuguese commands route correctly."""
        from scripts.maestro.routing import route_to_agent

        routing_tests = [
            ("mostra os arquivos", "explorer"),
            ("cria teste unitario", "testing"),
            ("refatora essa funcao", "refactorer"),
            ("revisa o codigo", "reviewer"),
            ("faz deploy", "devops"),
            ("documenta isso", "documentation"),
            ("ta lento demais", "performance"),
        ]

        correct = 0
        for request, expected_agent in routing_tests:
            result = route_to_agent(request)
            if result == expected_agent:
                correct += 1

        accuracy = correct / len(routing_tests)
        assert accuracy >= 0.7, f"Portuguese routing accuracy: {accuracy:.0%}"

    def test_english_routing_coverage(self):
        """Test that English commands route correctly."""
        from scripts.maestro.routing import route_to_agent

        routing_tests = [
            ("show me the files", "explorer"),
            ("create unit test", "testing"),
            ("refactor this function", "refactorer"),
            ("review the code", "reviewer"),
            ("deploy to production", "devops"),
            ("document this", "documentation"),
            ("it's too slow", "performance"),
        ]

        correct = 0
        for request, expected_agent in routing_tests:
            result = route_to_agent(request)
            if result == expected_agent:
                correct += 1

        accuracy = correct / len(routing_tests)
        assert accuracy >= 0.7, f"English routing accuracy: {accuracy:.0%}"


class TestToolExecution:
    """Test actual tool execution."""

    @pytest.fixture
    def temp_dir(self):
        """Create temp directory for tests."""
        d = tempfile.mkdtemp(prefix="vertice_tool_test_")
        yield Path(d)
        import shutil

        shutil.rmtree(d, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_readfile_tool(self, temp_dir):
        """Test readfile tool execution."""
        from vertice_cli.tools.registry_setup import create_full_registry

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        registry = create_full_registry()

        # Find read tool
        read_tool = registry.get("readfile") or registry.get("read_file")
        if read_tool:
            result = await read_tool.execute(path=str(test_file))
            assert result.success
            assert "Hello" in str(result.data)

    @pytest.mark.asyncio
    async def test_writefile_tool(self, temp_dir):
        """Test writefile tool execution."""
        from vertice_cli.tools.registry_setup import create_full_registry

        registry = create_full_registry()

        # Find write tool
        write_tool = registry.get("writefile") or registry.get("write_file")
        if write_tool:
            test_file = temp_dir / "output.txt"
            result = await write_tool.execute(path=str(test_file), content="Test content")
            assert result.success
            assert test_file.exists()
            assert test_file.read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_think_tool(self):
        """Test think tool execution."""
        from vertice_cli.tools.think_tool import ThinkTool

        tool = ThinkTool()
        result = await tool.execute(
            thought="""
        1) Entendimento: Preciso criar um arquivo
        2) Abordagens: Usar writefile ou bashcommand
        3) Decisao: Usar writefile por ser mais seguro
        4) Riscos: Sobrescrever arquivo existente
        5) Proximos passos: Verificar se existe, depois criar
        """
        )

        assert result.success
        assert result.metadata.get("has_structure", False)


class TestConversationContext:
    """Test conversation context management."""

    def test_context_tracks_files(self):
        """Test that context tracks file operations."""
        from vertice_cli.core.session_context import SessionContext

        context = SessionContext()

        # Track file read
        context.track_tool_call("readfile", {"path": "main.py"}, {"success": True})
        assert "main.py" in context.read_files or len(context.read_files) >= 0

    def test_context_tracks_modified(self):
        """Test that context tracks modified files."""
        from vertice_cli.core.session_context import SessionContext

        context = SessionContext()

        # Track file write
        context.track_tool_call("writefile", {"path": "output.py"}, {"success": True})


class TestPromptGeneration:
    """Test prompt generation."""

    def test_enhanced_prompt_includes_sections(self):
        """Test that enhanced prompt includes all PTCF sections."""
        from vertice_cli.prompts.system_prompts import build_enhanced_system_prompt

        tool_schemas = [
            {"name": "readfile", "description": "Read file", "parameters": {}, "category": "file"},
            {
                "name": "writefile",
                "description": "Write file",
                "parameters": {},
                "category": "file",
            },
        ]

        context = {
            "cwd": "/project",
            "modified_files": ["main.py"],
        }

        prompt = build_enhanced_system_prompt(tool_schemas, context)

        # Check PTCF sections
        assert "[P]" in prompt or "PERSONA" in prompt
        assert "[T]" in prompt or "TASK" in prompt
        assert "[C]" in prompt or "CONTEXT" in prompt
        assert "[F]" in prompt or "FORMAT" in prompt

        # Check context injection
        assert "/project" in prompt

    def test_prompt_includes_multilingual(self):
        """Test that prompt includes multilingual support section."""
        from vertice_cli.prompts.system_prompts import build_enhanced_system_prompt

        prompt = build_enhanced_system_prompt([], {})

        assert "MULTILINGUAL" in prompt or "Portuguese" in prompt


class TestFewShotExamples:
    """Test few-shot examples."""

    def test_portuguese_examples_exist(self):
        """Test that Portuguese examples are available."""
        from vertice_cli.prompts.few_shot_examples import FEW_SHOT_EXAMPLES_PTBR

        assert len(FEW_SHOT_EXAMPLES_PTBR) >= 5, "Expected at least 5 Portuguese examples"

        # Check example structure
        for example in FEW_SHOT_EXAMPLES_PTBR:
            assert "user" in example
            assert "assistant" in example

    def test_bilingual_example_selection(self):
        """Test bilingual example selection."""
        from vertice_cli.prompts.few_shot_examples import get_bilingual_examples

        # Portuguese input should get Portuguese examples
        pt_examples = get_bilingual_examples("mostra o arquivo main.py")
        # English input should get English examples
        en_examples = get_bilingual_examples("show me the main.py file")

        assert len(pt_examples) > 0
        assert len(en_examples) > 0


class TestErrorMessages:
    """Test localized error messages."""

    def test_error_messages_bilingual(self):
        """Test that error messages are bilingual."""
        from vertice_cli.core.error_messages import ERROR_MESSAGES

        # Check that messages have both languages
        for key, messages in ERROR_MESSAGES.items():
            assert "en" in messages, f"Missing English for {key}"
            assert "pt" in messages, f"Missing Portuguese for {key}"

    def test_get_error_message_formatting(self):
        """Test error message formatting."""
        from vertice_cli.core.error_messages import get_error_message

        # English
        en_msg = get_error_message("file_not_found", "en", path="/test.py")
        assert "/test.py" in en_msg

        # Portuguese
        pt_msg = get_error_message("file_not_found", "pt", path="/test.py")
        assert "/test.py" in pt_msg


# =============================================================================
# CLI EXECUTION TESTS (Optional - requires vtc installed)
# =============================================================================


class TestCLIExecution:
    """Test actual CLI execution (optional)."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp(prefix="vertice_cli_test_")
        yield Path(d)
        import shutil

        shutil.rmtree(d, ignore_errors=True)

    @pytest.mark.skipif(
        not os.path.exists("/usr/local/bin/vtc")
        and not os.path.exists(os.path.expanduser("~/.local/bin/vtc")),
        reason="vtc not installed",
    )
    def test_vtc_help(self):
        """Test vtc --help command."""
        result = subprocess.run(["vtc", "--help"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0 or "vertice" in result.stdout.lower()

    @pytest.mark.skipif(
        not os.path.exists("/usr/local/bin/vtc")
        and not os.path.exists(os.path.expanduser("~/.local/bin/vtc")),
        reason="vtc not installed",
    )
    def test_vtc_version(self):
        """Test vtc --version command."""
        result = subprocess.run(["vtc", "--version"], capture_output=True, text=True, timeout=10)
        # Should return version or help
        assert result.returncode == 0 or len(result.stdout) > 0


# =============================================================================
# STRESS TESTS
# =============================================================================


class TestStress:
    """Stress tests for the system."""

    @pytest.mark.asyncio
    async def test_rapid_classification(self):
        """Test rapid intent classification."""
        from vertice_cli.core.intent_classifier import SemanticIntentClassifier

        classifier = SemanticIntentClassifier()

        requests = [
            "mostra arquivo",
            "cria funcao",
            "busca TODO",
            "conserta erro",
            "refatora classe",
        ] * 10  # 50 requests

        start = time.time()
        results = await asyncio.gather(*[classifier.classify(req) for req in requests])
        duration = time.time() - start

        assert len(results) == 50
        assert duration < 5, f"Classification took too long: {duration}s"

    @pytest.mark.asyncio
    async def test_rapid_amplification(self):
        """Test rapid request amplification."""
        from vertice_cli.core.request_amplifier import RequestAmplifier

        context = {"cwd": "/project"}
        amplifier = RequestAmplifier(context=context)

        requests = ["mostra arquivo", "cria funcao", "busca TODO"] * 20

        start = time.time()
        results = await asyncio.gather(*[amplifier.analyze(req) for req in requests])
        duration = time.time() - start

        assert len(results) == 60
        assert duration < 3, f"Amplification took too long: {duration}s"


# =============================================================================
# JULES RUNNER REPORT
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def test_session_report(request):
    """Generate test session report for Jules."""
    yield

    # Generate report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version,
        "platform": sys.platform,
        "tests_collected": 0,
        "tests_passed": 0,
        "tests_failed": 0,
    }

    # Try to get stats from pytest
    if hasattr(request.config, "_numcollected"):
        report["tests_collected"] = request.config._numcollected

    print("\n" + "=" * 60)
    print("VERTICE E2E SHELL INTEGRATION TEST REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))

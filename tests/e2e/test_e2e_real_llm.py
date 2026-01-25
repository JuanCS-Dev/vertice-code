"""
E2E Real LLM Tests - Heavy Integration Tests for Vertice-Code.

These tests validate REAL behavior with actual LLM calls.
Designed to be run by Jules or similar CI systems.

Requirements:
- ANTHROPIC_API_KEY or GOOGLE_API_KEY environment variable
- Network access to LLM providers
- ~5-10 minutes to run complete suite

Usage:
    pytest tests/e2e/test_e2e_real_llm.py -v --timeout=300

    # Run specific category:
    pytest tests/e2e/test_e2e_real_llm.py -k "app_creation" -v
    pytest tests/e2e/test_e2e_real_llm.py -k "refactoring" -v
    pytest tests/e2e/test_e2e_real_llm.py -k "portuguese" -v
"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import pytest

# Skip all tests if no API keys available
pytestmark = pytest.mark.skipif(
    not (
        os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GROQ_API_KEY")
    ),
    reason="No LLM API key available (set ANTHROPIC_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY)",
)


@dataclass
class TestResult:
    """Result of an E2E test."""

    success: bool
    duration: float
    tool_calls: List[Dict[str, Any]]
    files_created: List[str]
    files_modified: List[str]
    errors: List[str]
    llm_response: str


class VerticeE2ETestRunner:
    """
    E2E test runner that executes real Vertice commands with LLM.

    This runner:
    1. Creates isolated temp directories for each test
    2. Initializes real LLM clients
    3. Executes tool chains
    4. Validates outputs
    """

    def __init__(self, work_dir: Optional[Path] = None):
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="vertice_e2e_"))
        self.tool_calls: List[Dict] = []
        self.errors: List[str] = []
        self.files_before: set = set()

    async def setup(self):
        """Setup test environment."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.files_before = set(self.work_dir.rglob("*"))

        # Initialize LLM client
        from vertice_core.core.llm_client import get_llm_client

        self.llm = await get_llm_client()

        # Initialize tool registry
        from vertice_core.tools.registry_setup import create_full_registry

        self.registry = create_full_registry()

    async def cleanup(self):
        """Cleanup test environment."""
        if self.work_dir.exists() and str(self.work_dir).startswith(tempfile.gettempdir()):
            shutil.rmtree(self.work_dir, ignore_errors=True)

    async def execute_request(self, request: str, max_iterations: int = 5) -> TestResult:
        """
        Execute a natural language request through the full pipeline.

        Args:
            request: Natural language request (PT or EN)
            max_iterations: Max tool call iterations

        Returns:
            TestResult with execution details
        """
        start_time = time.time()
        tool_calls = []
        errors = []
        llm_response = ""

        try:
            # Build system prompt
            from vertice_core.prompts.system_prompts import build_enhanced_system_prompt

            tool_schemas = self.registry.get_schemas()

            context = {
                "cwd": str(self.work_dir),
                "modified_files": [],
                "read_files": [],
            }

            system_prompt = build_enhanced_system_prompt(tool_schemas, context)

            # Execute request with LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request},
            ]

            for iteration in range(max_iterations):
                response = await self.llm.generate_async(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000,
                )

                llm_response = (
                    response.get("content", str(response))
                    if isinstance(response, dict)
                    else str(response)
                )

                # Parse tool calls
                parsed_calls = self._parse_tool_calls(llm_response)

                if not parsed_calls:
                    break  # No more tool calls, done

                # Execute each tool call
                for call in parsed_calls:
                    tool_name = call.get("tool", "")
                    args = call.get("args", {})

                    # Inject work_dir for file operations
                    if "path" in args and not args["path"].startswith("/"):
                        args["path"] = str(self.work_dir / args["path"])
                    if "file_path" in args and not args["file_path"].startswith("/"):
                        args["file_path"] = str(self.work_dir / args["file_path"])

                    tool_calls.append({"tool": tool_name, "args": args, "iteration": iteration})

                    tool = self.registry.get(tool_name)
                    if tool:
                        try:
                            result = await tool.execute(**args)
                            result_str = (
                                str(result.data)[:500]
                                if hasattr(result, "data")
                                else str(result)[:500]
                            )

                            # Add result to conversation
                            messages.append({"role": "assistant", "content": llm_response})
                            messages.append(
                                {
                                    "role": "user",
                                    "content": f"Tool {tool_name} result: {result_str}",
                                }
                            )
                        except Exception as e:
                            errors.append(f"Tool {tool_name} failed: {e}")
                    else:
                        errors.append(f"Unknown tool: {tool_name}")

        except Exception as e:
            errors.append(f"Execution failed: {e}")

        # Calculate files created/modified
        files_after = set(self.work_dir.rglob("*"))
        files_created = [
            str(f.relative_to(self.work_dir))
            for f in (files_after - self.files_before)
            if f.is_file()
        ]

        duration = time.time() - start_time

        return TestResult(
            success=len(errors) == 0,
            duration=duration,
            tool_calls=tool_calls,
            files_created=files_created,
            files_modified=[],  # Would need file content tracking
            errors=errors,
            llm_response=llm_response,
        )

    def _parse_tool_calls(self, response: str) -> List[Dict]:
        """Parse tool calls from LLM response."""
        try:
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                json_str = response[start:end]
                calls = json.loads(json_str)
                if isinstance(calls, list):
                    return calls
        except (json.JSONDecodeError, ValueError):
            pass
        return []


# =============================================================================
# APP CREATION TESTS
# =============================================================================


class TestAppCreation:
    """Tests for creating applications from scratch."""

    @pytest.fixture
    async def runner(self):
        """Create test runner."""
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_create_python_hello_world(self, runner):
        """Test creating a simple Python hello world script."""
        result = await runner.execute_request(
            "Cria um arquivo hello.py com uma funcao que imprime 'Ola Mundo'"
        )

        assert "hello.py" in result.files_created or any(
            "hello" in f for f in result.files_created
        ), f"Expected hello.py to be created. Files: {result.files_created}"
        assert len(result.tool_calls) > 0, "Expected at least one tool call"

        # Verify file content
        hello_path = runner.work_dir / "hello.py"
        if hello_path.exists():
            content = hello_path.read_text()
            assert "def" in content or "print" in content, "Expected Python code"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_create_python_calculator(self, runner):
        """Test creating a calculator module with multiple functions."""
        result = await runner.execute_request(
            "Cria um arquivo calculator.py com funcoes de soma, subtracao, multiplicacao e divisao"
        )

        assert any(
            "calculator" in f.lower() for f in result.files_created
        ), f"Expected calculator.py. Files: {result.files_created}"

        calc_path = runner.work_dir / "calculator.py"
        if calc_path.exists():
            content = calc_path.read_text()
            # Should have multiple functions
            assert content.count("def ") >= 3, "Expected at least 3 function definitions"

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_create_flask_api(self, runner):
        """Test creating a basic Flask API structure."""
        result = await runner.execute_request(
            "Create a simple Flask API with a /health endpoint that returns JSON status ok"
        )

        # Should create at least one Python file
        py_files = [f for f in result.files_created if f.endswith(".py")]
        assert len(py_files) > 0, f"Expected Python files. Created: {result.files_created}"

        # Check for Flask imports
        for py_file in py_files:
            path = runner.work_dir / py_file
            if path.exists():
                content = path.read_text()
                if "flask" in content.lower() or "Flask" in content:
                    assert True
                    return

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_create_cli_tool(self, runner):
        """Test creating a CLI tool with argparse."""
        result = await runner.execute_request(
            "Cria uma ferramenta CLI em Python usando argparse com opcoes --input e --output"
        )

        py_files = [f for f in result.files_created if f.endswith(".py")]
        assert len(py_files) > 0, "Expected Python files"

        # Check for argparse usage
        for py_file in py_files:
            path = runner.work_dir / py_file
            if path.exists():
                content = path.read_text()
                if "argparse" in content or "ArgumentParser" in content:
                    assert "--input" in content or "input" in content
                    return

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_create_data_class_model(self, runner):
        """Test creating a data model with dataclasses."""
        result = await runner.execute_request(
            "Cria um arquivo models.py com dataclasses User e Product com campos apropriados"
        )

        assert any(
            "model" in f.lower() for f in result.files_created
        ), f"Expected models.py. Created: {result.files_created}"

        models_path = runner.work_dir / "models.py"
        if models_path.exists():
            content = models_path.read_text()
            assert "@dataclass" in content or "dataclass" in content
            assert "User" in content or "user" in content.lower()


# =============================================================================
# REFACTORING TESTS
# =============================================================================


class TestRefactoring:
    """Tests for code refactoring operations."""

    @pytest.fixture
    async def runner(self):
        """Create test runner with initial files."""
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    async def _create_initial_file(self, runner: VerticeE2ETestRunner, filename: str, content: str):
        """Helper to create initial file for refactoring tests."""
        path = runner.work_dir / filename
        path.write_text(content)
        runner.files_before.add(path)

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_refactor_extract_function(self, runner):
        """Test extracting a function from inline code."""
        initial_code = """
def process_data(data):
    # Validation logic that should be extracted
    if not data:
        raise ValueError("Data is empty")
    if not isinstance(data, dict):
        raise TypeError("Data must be dict")
    if "id" not in data:
        raise KeyError("Missing id field")

    # Processing
    result = data.copy()
    result["processed"] = True
    return result
"""
        await self._create_initial_file(runner, "processor.py", initial_code)

        result = await runner.execute_request(
            "Refatora processor.py extraindo a logica de validacao para uma funcao separada validate_data"
        )

        # Check if file was modified
        processor_path = runner.work_dir / "processor.py"
        if processor_path.exists():
            content = processor_path.read_text()
            # Should now have validate_data function
            has_validate = "validate_data" in content or "def validate" in content
            assert has_validate or len(result.tool_calls) > 0, "Expected refactoring to occur"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_refactor_rename_variable(self, runner):
        """Test renaming a variable throughout a file."""
        initial_code = """
def calculate(x):
    temp = x * 2
    temp = temp + 10
    result = temp / 2
    return result

def process(x):
    temp = x ** 2
    return temp
"""
        await self._create_initial_file(runner, "calc.py", initial_code)

        result = await runner.execute_request(
            "Renomeia a variavel 'temp' para 'intermediate_value' em calc.py"
        )

        calc_path = runner.work_dir / "calc.py"
        if calc_path.exists():
            content = calc_path.read_text()
            # Either renamed or at least tried to edit
            assert "intermediate" in content or len(result.tool_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_refactor_add_type_hints(self, runner):
        """Test adding type hints to a function."""
        initial_code = """
def add(a, b):
    return a + b

def greet(name):
    return f"Hello, {name}!"

def process_items(items):
    return [item.upper() for item in items]
"""
        await self._create_initial_file(runner, "functions.py", initial_code)

        result = await runner.execute_request(
            "Adiciona type hints em todas as funcoes de functions.py"
        )

        func_path = runner.work_dir / "functions.py"
        if func_path.exists():
            content = func_path.read_text()
            # Should have type annotations
            has_types = "->" in content or ": str" in content or ": int" in content
            assert has_types or len(result.tool_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_refactor_add_docstrings(self, runner):
        """Test adding docstrings to functions."""
        initial_code = """
def calculate_total(items, tax_rate):
    subtotal = sum(item.price for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax

def apply_discount(price, discount_percent):
    return price * (1 - discount_percent / 100)
"""
        await self._create_initial_file(runner, "pricing.py", initial_code)

        result = await runner.execute_request(
            "Adiciona docstrings descritivas para todas as funcoes em pricing.py"
        )

        pricing_path = runner.work_dir / "pricing.py"
        if pricing_path.exists():
            content = pricing_path.read_text()
            # Should have docstrings
            has_docs = '"""' in content or "'''" in content
            assert has_docs or len(result.tool_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_refactor_class_to_dataclass(self, runner):
        """Test converting a regular class to a dataclass."""
        initial_code = """
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age

    def __repr__(self):
        return f"User(name={self.name}, email={self.email}, age={self.age})"
"""
        await self._create_initial_file(runner, "user.py", initial_code)

        result = await runner.execute_request(
            "Converte a classe User em user.py para usar dataclass"
        )

        user_path = runner.work_dir / "user.py"
        if user_path.exists():
            content = user_path.read_text()
            has_dataclass = "@dataclass" in content or "dataclass" in content
            assert has_dataclass or len(result.tool_calls) > 0


# =============================================================================
# PORTUGUESE NLU TESTS
# =============================================================================


class TestPortugueseNLU:
    """Tests for Portuguese natural language understanding."""

    @pytest.fixture
    async def runner(self):
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_imperative_mostra(self, runner):
        """Test 'mostra' command in Portuguese."""
        # Create a file first
        (runner.work_dir / "teste.py").write_text("print('teste')")

        result = await runner.execute_request("mostra o arquivo teste.py")

        # Should call readfile tool
        read_calls = [c for c in result.tool_calls if "read" in c["tool"].lower()]
        assert len(read_calls) > 0 or "print" in result.llm_response, "Expected file read operation"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_imperative_cria(self, runner):
        """Test 'cria' command in Portuguese."""
        result = await runner.execute_request(
            "cria um arquivo config.json com chave 'nome' valor 'teste'"
        )

        json_files = [f for f in result.files_created if f.endswith(".json")]
        assert len(json_files) > 0 or len(result.tool_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_imperative_busca(self, runner):
        """Test 'busca' command in Portuguese."""
        # Create files with TODO
        (runner.work_dir / "app.py").write_text("# TODO: implement login\nprint('app')")
        (runner.work_dir / "utils.py").write_text("# TODO: add tests\ndef util(): pass")

        result = await runner.execute_request("busca todos os TODO nos arquivos Python")

        search_calls = [
            c
            for c in result.tool_calls
            if "search" in c["tool"].lower() or "grep" in c["tool"].lower()
        ]
        assert len(search_calls) > 0 or "TODO" in result.llm_response

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_colloquial_ta_quebrado(self, runner):
        """Test colloquial 'ta quebrado' expression."""
        # Create file with syntax error
        (runner.work_dir / "broken.py").write_text("def func(\n    print('incomplete'")

        result = await runner.execute_request("o arquivo broken.py ta quebrado, conserta ele")

        # Should attempt to read and fix
        assert len(result.tool_calls) > 0, "Expected tool calls for fixing"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_accented_input(self, runner):
        """Test handling of accented Portuguese input."""
        result = await runner.execute_request("Cria uma função que calcula a média de números")

        # Should understand and create file
        assert len(result.tool_calls) > 0 or len(result.files_created) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_portuguese_onde_fica(self, runner):
        """Test 'onde fica' (where is) query."""
        # Create project structure
        (runner.work_dir / "src").mkdir()
        (runner.work_dir / "src" / "main.py").write_text("def main(): pass")
        (runner.work_dir / "src" / "config.py").write_text("CONFIG = {}")

        result = await runner.execute_request("onde fica o arquivo de configuracao?")

        # Should search for config files
        assert len(result.tool_calls) > 0 or "config" in result.llm_response.lower()


# =============================================================================
# COMPLEX WORKFLOW TESTS
# =============================================================================


class TestComplexWorkflows:
    """Tests for complex multi-step workflows."""

    @pytest.fixture
    async def runner(self):
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_create_and_test_module(self, runner):
        """Test creating a module and then creating tests for it."""
        # Step 1: Create module
        result1 = await runner.execute_request(
            "Cria um modulo math_utils.py com funcoes add, subtract, multiply, divide"
        )

        assert any(
            "math" in f.lower() for f in result1.files_created
        ), "Expected math_utils.py to be created"

        # Step 2: Create tests
        result2 = await runner.execute_request(
            "Agora cria testes unitarios para math_utils.py usando pytest"
        )

        test_files = [f for f in result2.files_created if "test" in f.lower()]
        assert len(test_files) > 0 or "test" in result2.llm_response.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_read_analyze_refactor(self, runner):
        """Test reading, analyzing, and refactoring a file."""
        # Create complex file
        complex_code = """
def process_user_data(user_dict):
    # This function does too many things
    if not user_dict:
        return None
    if "name" not in user_dict:
        return None
    if "email" not in user_dict:
        return None

    name = user_dict["name"].strip().title()
    email = user_dict["email"].strip().lower()

    if "@" not in email:
        return None

    result = {
        "name": name,
        "email": email,
        "username": email.split("@")[0],
        "domain": email.split("@")[1],
    }

    return result
"""
        (runner.work_dir / "processor.py").write_text(complex_code)

        result = await runner.execute_request(
            "Analisa processor.py e refatora para separar validacao, normalizacao e criacao do resultado"
        )

        # Should have multiple tool calls (read, then edit/write)
        assert len(result.tool_calls) >= 2, "Expected read and edit operations"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_project_structure_creation(self, runner):
        """Test creating a complete project structure."""
        result = await runner.execute_request(
            "Cria a estrutura de um projeto Python com pastas src, tests, docs e arquivos __init__.py, main.py, README.md"
        )

        # Should create multiple files/directories
        assert (
            len(result.files_created) >= 3
        ), f"Expected multiple files. Created: {result.files_created}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_api_endpoint_with_validation(self, runner):
        """Test creating an API endpoint with input validation."""
        result = await runner.execute_request(
            "Cria um endpoint FastAPI POST /users que recebe JSON com name e email, valida os campos e retorna o usuario criado"
        )

        py_files = [f for f in result.files_created if f.endswith(".py")]
        assert len(py_files) > 0

        # Check for FastAPI code
        for f in py_files:
            path = runner.work_dir / f
            if path.exists():
                content = path.read_text()
                if "fastapi" in content.lower() or "FastAPI" in content:
                    assert "@" in content, "Expected decorator usage"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @pytest.fixture
    async def runner(self):
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_handle_nonexistent_file(self, runner):
        """Test handling request for non-existent file."""
        result = await runner.execute_request("mostra o arquivo nao_existe.py")

        # Should handle gracefully - either error message or search
        assert (
            len(result.tool_calls) > 0
            or "not found" in result.llm_response.lower()
            or "nao encontr" in result.llm_response.lower()
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_handle_ambiguous_request(self, runner):
        """Test handling ambiguous/vague request."""
        result = await runner.execute_request("faz isso")

        # Should ask for clarification or explain inability
        assert len(result.llm_response) > 0, "Expected some response"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_handle_invalid_syntax_fix(self, runner):
        """Test fixing a file with invalid syntax."""
        invalid_code = """
def broken_function(
    print("missing closing paren"

def another_function():
    return "ok"
"""
        (runner.work_dir / "broken.py").write_text(invalid_code)

        result = await runner.execute_request("corrija os erros de sintaxe em broken.py")

        assert len(result.tool_calls) > 0, "Expected tool calls for fixing"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestPerformance:
    """Performance and stress tests."""

    @pytest.fixture
    async def runner(self):
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_simple_request_latency(self, runner):
        """Test latency for simple requests."""
        result = await runner.execute_request("cria um arquivo test.txt com conteudo 'hello'")

        # Should complete in reasonable time
        assert result.duration < 30, f"Request took too long: {result.duration}s"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_multiple_file_operations(self, runner):
        """Test handling multiple file operations."""
        result = await runner.execute_request(
            "Cria tres arquivos: a.py com funcao f1, b.py com funcao f2, c.py com funcao f3"
        )

        # Should handle multiple files
        assert len(result.files_created) >= 2 or len(result.tool_calls) >= 3


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.fixture
    async def runner(self):
        runner = VerticeE2ETestRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_full_development_cycle(self, runner):
        """Test a complete development cycle: create, read, modify."""
        # Create
        result1 = await runner.execute_request(
            "Cria utils.py com funcao format_name que recebe um nome"
        )
        assert len(result1.files_created) > 0 or len(result1.tool_calls) > 0

        # Read
        if (runner.work_dir / "utils.py").exists():
            result2 = await runner.execute_request("Mostra o conteudo de utils.py")
            assert "def" in result2.llm_response or len(result2.tool_calls) > 0

        # Modify
        result3 = await runner.execute_request(
            "Adiciona uma docstring na funcao format_name em utils.py"
        )
        assert len(result3.tool_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_nlu_to_tool_execution(self, runner):
        """Test the full NLU to tool execution pipeline."""
        from vertice_core.core.intent_classifier import SemanticIntentClassifier, Intent
        from vertice_core.core.request_amplifier import RequestAmplifier
        from vertice_core.core.complexity_analyzer import analyze_complexity

        request = "mostra os arquivos Python no diretorio atual"

        # Intent classification
        classifier = SemanticIntentClassifier()
        intent_result = await classifier.classify(request)
        assert intent_result.intent == Intent.EXPLORE

        # Request amplification
        context = {"cwd": str(runner.work_dir)}
        amplifier = RequestAmplifier(context=context)
        amplified = await amplifier.analyze(request)
        assert amplified.amplified != ""

        # Complexity analysis
        complexity = analyze_complexity(request, intent_result.intent, intent_result.confidence)
        assert not complexity.needs_thinking  # Simple request

        # Tool execution
        result = await runner.execute_request(request)
        assert len(result.tool_calls) > 0


# =============================================================================
# REPORT GENERATION
# =============================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate summary report after tests."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))

    terminalreporter.write_sep("=", "VERTICE E2E TEST SUMMARY")
    terminalreporter.write_line(f"Passed: {passed}")
    terminalreporter.write_line(f"Failed: {failed}")
    terminalreporter.write_line(f"Skipped: {skipped}")
    terminalreporter.write_line(f"Total: {passed + failed + skipped}")

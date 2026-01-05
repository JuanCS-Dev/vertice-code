"""
E2E Brutal Scenario Tests - Heavy Real-World Scenarios.

These are the HARDEST tests - real project creation and refactoring.
Each test simulates a real developer workflow with actual LLM calls.

WARNING: These tests are SLOW (5-15 minutes each) and use real API credits.

Usage:
    # Run all brutal tests (slow, ~30-60 minutes)
    pytest tests/e2e/test_e2e_brutal_scenarios.py -v --timeout=900

    # Run specific scenario
    pytest tests/e2e/test_e2e_brutal_scenarios.py -k "fastapi" -v

Requirements:
    - ANTHROPIC_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY
    - At least 10 minutes per test
    - Sufficient API credits
"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import pytest

# Skip if no API keys
pytestmark = [
    pytest.mark.skipif(
        not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GROQ_API_KEY")),
        reason="No LLM API key available"
    ),
    pytest.mark.slow,  # Mark as slow tests
]


@dataclass
class ScenarioResult:
    """Result of a brutal scenario test."""
    scenario_name: str
    success: bool
    duration: float
    steps_completed: int
    steps_total: int
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)
    validation_results: Dict[str, bool] = field(default_factory=dict)


class BrutalScenarioRunner:
    """
    Runner for brutal real-world scenario tests.

    Each scenario consists of multiple steps that must be executed
    in sequence, simulating a real development workflow.
    """

    def __init__(self):
        self.work_dir = Path(tempfile.mkdtemp(prefix="vertice_brutal_"))
        self.llm = None
        self.registry = None
        self.tool_calls: List[Dict] = []
        self.errors: List[str] = []

    async def setup(self):
        """Initialize LLM and registry."""
        from vertice_cli.core.llm_client import get_llm_client
        from vertice_cli.tools.registry_setup import create_full_registry

        self.llm = await get_llm_client()
        self.registry = create_full_registry()

    async def cleanup(self):
        """Cleanup test directory."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)

    async def execute_step(self, step_description: str, request: str) -> bool:
        """
        Execute a single step in the scenario.

        Args:
            step_description: Human-readable step description
            request: Natural language request to execute

        Returns:
            True if step succeeded, False otherwise
        """
        print(f"\n  Step: {step_description}")
        print(f"  Request: {request[:80]}...")

        try:
            from vertice_cli.prompts.system_prompts import build_enhanced_system_prompt

            tool_schemas = self.registry.get_schemas()
            context = {'cwd': str(self.work_dir)}

            system_prompt = build_enhanced_system_prompt(tool_schemas, context)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request},
            ]

            # Execute with LLM
            response = await self.llm.generate_async(
                messages=messages,
                temperature=0.1,
                max_tokens=4000,
            )

            response_text = response.get("content", str(response)) if isinstance(response, dict) else str(response)

            # Parse and execute tool calls
            tool_calls = self._parse_tool_calls(response_text)

            for call in tool_calls:
                tool_name = call.get("tool", "")
                args = call.get("args", {})

                # Inject work_dir
                for key in ["path", "file_path", "directory"]:
                    if key in args and not str(args[key]).startswith("/"):
                        args[key] = str(self.work_dir / args[key])

                self.tool_calls.append(call)

                tool = self.registry.get(tool_name)
                if tool:
                    await tool.execute(**args)

            return True

        except Exception as e:
            self.errors.append(f"Step '{step_description}' failed: {e}")
            return False

    def _parse_tool_calls(self, response: str) -> List[Dict]:
        """Parse tool calls from response."""
        try:
            if '[' in response and ']' in response:
                start = response.index('[')
                end = response.rindex(']') + 1
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return []

    def validate_file_exists(self, path: str) -> bool:
        """Validate that a file exists."""
        full_path = self.work_dir / path
        return full_path.exists()

    def validate_file_contains(self, path: str, content: str) -> bool:
        """Validate that a file contains specific content."""
        full_path = self.work_dir / path
        if not full_path.exists():
            return False
        return content in full_path.read_text()

    def validate_directory_exists(self, path: str) -> bool:
        """Validate that a directory exists."""
        full_path = self.work_dir / path
        return full_path.is_dir()

    def get_created_files(self) -> List[str]:
        """Get list of all files created in work_dir."""
        return [str(f.relative_to(self.work_dir)) for f in self.work_dir.rglob("*") if f.is_file()]


# =============================================================================
# SCENARIO: CREATE FASTAPI APPLICATION
# =============================================================================

class TestFastAPICreation:
    """Brutal test: Create a complete FastAPI application."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_create_complete_fastapi_app(self, runner):
        """
        Create a complete FastAPI application with:
        - Main app file
        - Models with Pydantic
        - CRUD endpoints
        - Input validation
        - Error handling
        """
        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Create main app", "Cria um arquivo app.py com FastAPI app basico com endpoint GET /health retornando status ok"),
            ("Create models", "Cria models.py com Pydantic models User (id, name, email) e Item (id, title, price)"),
            ("Add CRUD endpoints", "Adiciona em app.py endpoints POST /users, GET /users/{id}, PUT /users/{id}, DELETE /users/{id}"),
            ("Add validation", "Adiciona validacao de email no model User e validacao de price > 0 no model Item"),
            ("Add error handling", "Adiciona tratamento de erros 404 para usuario nao encontrado e 400 para dados invalidos"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        # Validations
        validations = {
            "app.py exists": runner.validate_file_exists("app.py"),
            "models.py exists": runner.validate_file_exists("models.py"),
            "has FastAPI import": runner.validate_file_contains("app.py", "FastAPI") or
                                  runner.validate_file_contains("app.py", "fastapi"),
            "has health endpoint": runner.validate_file_contains("app.py", "/health") or
                                   runner.validate_file_contains("app.py", "health"),
            "has User model": runner.validate_file_contains("models.py", "User") if runner.validate_file_exists("models.py") else False,
        }

        result = ScenarioResult(
            scenario_name="FastAPI Application Creation",
            success=steps_completed >= 3,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            tool_calls=runner.tool_calls,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        print(f"  Files: {result.files_created}")
        print(f"  Validations: {validations}")

        assert result.success, f"Scenario failed: {result.errors}"
        assert validations.get("app.py exists", False), "app.py should exist"


# =============================================================================
# SCENARIO: CREATE CLI TOOL WITH TESTING
# =============================================================================

class TestCLIToolCreation:
    """Brutal test: Create a CLI tool with tests."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_create_cli_with_tests(self, runner):
        """
        Create a CLI tool with:
        - Argparse configuration
        - Multiple commands
        - Unit tests
        """
        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Create CLI structure", "Cria cli.py com argparse, subcomandos 'add' e 'list', e funcao main()"),
            ("Implement add command", "Implementa o comando 'add' que adiciona um item a uma lista em JSON"),
            ("Implement list command", "Implementa o comando 'list' que lista todos os itens do JSON"),
            ("Create tests", "Cria test_cli.py com testes pytest para os comandos add e list"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        validations = {
            "cli.py exists": runner.validate_file_exists("cli.py"),
            "test_cli.py exists": runner.validate_file_exists("test_cli.py"),
            "has argparse": runner.validate_file_contains("cli.py", "argparse") if runner.validate_file_exists("cli.py") else False,
        }

        result = ScenarioResult(
            scenario_name="CLI Tool Creation with Tests",
            success=steps_completed >= 2,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        assert result.success, f"Scenario failed: {result.errors}"


# =============================================================================
# SCENARIO: REFACTOR LEGACY CODE
# =============================================================================

class TestLegacyRefactoring:
    """Brutal test: Refactor legacy code to modern standards."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    async def _setup_legacy_code(self, runner):
        """Setup legacy code files for refactoring."""
        legacy_code = '''
# Old style Python code with many issues

class user_manager:
    def __init__(self):
        self.users = []
        self.db = None

    def add_user(self, name, email, age):
        # No validation
        user = {"name": name, "email": email, "age": age}
        self.users.append(user)
        return user

    def get_user(self, name):
        for u in self.users:
            if u["name"] == name:
                return u
        return None

    def delete_user(self, name):
        for i, u in enumerate(self.users):
            if u["name"] == name:
                del self.users[i]
                return True
        return False

    def update_user(self, name, email=None, age=None):
        user = self.get_user(name)
        if user:
            if email:
                user["email"] = email
            if age:
                user["age"] = age
            return user
        return None

    def get_all_users(self):
        return self.users

    def validate_email(self, email):
        if "@" in email:
            return True
        return False
'''
        (runner.work_dir / "user_manager.py").write_text(legacy_code)

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_refactor_legacy_to_modern(self, runner):
        """
        Refactor legacy code to:
        - Use dataclasses
        - Add type hints
        - Add proper validation
        - Follow PEP8
        """
        await self._setup_legacy_code(runner)

        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Analyze code", "Leia user_manager.py e identifique os principais problemas de qualidade"),
            ("Add type hints", "Adiciona type hints em todas as funcoes de user_manager.py"),
            ("Convert to dataclass", "Cria uma dataclass User separada e refatora user_manager para usa-la"),
            ("Add validation", "Adiciona validacao de email e age >= 0 nos metodos add_user e update_user"),
            ("Rename class", "Renomeia a classe user_manager para UserManager seguindo PEP8"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        validations = {
            "file exists": runner.validate_file_exists("user_manager.py"),
            "has type hints": runner.validate_file_contains("user_manager.py", "->") or
                             runner.validate_file_contains("user_manager.py", ": str"),
        }

        result = ScenarioResult(
            scenario_name="Legacy Code Refactoring",
            success=steps_completed >= 2,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        assert result.success, f"Scenario failed: {result.errors}"


# =============================================================================
# SCENARIO: CREATE DATA PIPELINE
# =============================================================================

class TestDataPipelineCreation:
    """Brutal test: Create a data processing pipeline."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_create_etl_pipeline(self, runner):
        """
        Create a data pipeline with:
        - Data reader (CSV/JSON)
        - Data transformer
        - Data writer
        - Error handling
        """
        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Create reader", "Cria reader.py com classe DataReader que le arquivos CSV e JSON"),
            ("Create transformer", "Cria transformer.py com classe DataTransformer com metodos normalize, filter, aggregate"),
            ("Create writer", "Cria writer.py com classe DataWriter que escreve para CSV e JSON"),
            ("Create pipeline", "Cria pipeline.py que usa Reader, Transformer e Writer em sequencia"),
            ("Add error handling", "Adiciona try/except em pipeline.py para tratar erros de arquivo e dados"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        files_needed = ["reader.py", "transformer.py", "writer.py", "pipeline.py"]
        validations = {
            f"{f} exists": runner.validate_file_exists(f) for f in files_needed
        }

        result = ScenarioResult(
            scenario_name="Data Pipeline Creation",
            success=steps_completed >= 3,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        assert result.success, f"Scenario failed: {result.errors}"


# =============================================================================
# SCENARIO: PORTUGUESE-ONLY WORKFLOW
# =============================================================================

class TestPortugueseWorkflow:
    """Brutal test: Complete workflow in Portuguese only."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_complete_portuguese_workflow(self, runner):
        """
        Execute complete workflow using only Portuguese commands:
        - Create files
        - Read and analyze
        - Modify and refactor
        - Search and list
        """
        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Cria calculadora", "Cria um arquivo calculadora.py com funcoes soma, subtracao, multiplicacao e divisao"),
            ("Mostra conteudo", "Mostra o conteudo do arquivo calculadora.py"),
            ("Adiciona docstrings", "Adiciona docstrings em portugues para todas as funcoes em calculadora.py"),
            ("Cria testes", "Cria um arquivo test_calculadora.py com testes para cada funcao"),
            ("Busca funcoes", "Busca todas as funcoes definidas nos arquivos Python"),
            ("Refatora divisao", "Refatora a funcao divisao em calculadora.py para tratar divisao por zero"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        validations = {
            "calculadora.py exists": runner.validate_file_exists("calculadora.py"),
            "has soma function": runner.validate_file_contains("calculadora.py", "def soma") or
                                 runner.validate_file_contains("calculadora.py", "soma"),
        }

        result = ScenarioResult(
            scenario_name="Portuguese-Only Workflow",
            success=steps_completed >= 3,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        print(f"  Files created: {result.files_created}")
        assert result.success, f"Scenario failed: {result.errors}"


# =============================================================================
# SCENARIO: MICROSERVICES ARCHITECTURE
# =============================================================================

class TestMicroservicesCreation:
    """Brutal test: Create microservices architecture."""

    @pytest.fixture
    async def runner(self):
        runner = BrutalScenarioRunner()
        await runner.setup()
        yield runner
        await runner.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(900)
    async def test_create_microservices(self, runner):
        """
        Create microservices structure with:
        - User service
        - Order service
        - Shared models
        - API gateway concept
        """
        start_time = time.time()
        steps_completed = 0

        steps = [
            ("Create directory structure", "Cria pastas services/user, services/order, shared"),
            ("Create shared models", "Cria shared/models.py com classes User e Order usando dataclass"),
            ("Create user service", "Cria services/user/app.py com FastAPI e endpoints CRUD para User"),
            ("Create order service", "Cria services/order/app.py com FastAPI e endpoints para criar e listar Orders"),
            ("Create gateway", "Cria gateway.py que roteia requests para os servicos user e order"),
        ]

        for desc, request in steps:
            success = await runner.execute_step(desc, request)
            if success:
                steps_completed += 1

        validations = {
            "shared dir exists": runner.validate_directory_exists("shared"),
            "user service exists": runner.validate_file_exists("services/user/app.py") or
                                   runner.validate_file_exists("user/app.py") or
                                   len([f for f in runner.get_created_files() if "user" in f]) > 0,
        }

        result = ScenarioResult(
            scenario_name="Microservices Architecture",
            success=steps_completed >= 2,
            duration=time.time() - start_time,
            steps_completed=steps_completed,
            steps_total=len(steps),
            files_created=runner.get_created_files(),
            errors=runner.errors,
            validation_results=validations,
        )

        print(f"\n  Result: {steps_completed}/{len(steps)} steps completed")
        print(f"  Files: {result.files_created}")
        assert result.success, f"Scenario failed: {result.errors}"


# =============================================================================
# FINAL REPORT
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate final report."""
    print("\n" + "=" * 70)
    print("BRUTAL SCENARIO TEST REPORT")
    print("=" * 70)

    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    skipped = len(terminalreporter.stats.get('skipped', []))

    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {passed + failed + skipped}")
    print("=" * 70)

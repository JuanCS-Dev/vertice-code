"""
Tests for Audit Scenarios.

Validates scenario definitions and YAML loading logic.
"""
import yaml
from pathlib import Path
from tempfile import NamedTemporaryFile

from vertice_tui.core.autoaudit.scenarios import (
    SCENARIOS,
    Expectation,
    ScenarioCategory,
    get_scenarios_by_category,
    get_scenario_by_id,
    load_custom_scenarios,
)


class TestScenarios:
    def test_scenarios_integrity(self):
        """Valida se todos os cenários built-in são válidos."""
        assert len(SCENARIOS) > 0
        ids = set()
        for s in SCENARIOS:
            assert s.id, "Scenario must have ID"
            assert s.id not in ids, f"Duplicate ID: {s.id}"
            ids.add(s.id)

            assert s.prompt, f"Scenario {s.id} missing prompt"
            assert isinstance(s.category, ScenarioCategory), f"Invalid category in {s.id}"
            assert len(s.expectations) > 0, f"Scenario {s.id} has no expectations"
            assert s.timeout_seconds > 0

    def test_get_helpers(self):
        """Testa funções helper de busca."""
        # By ID
        s = SCENARIOS[0]
        found = get_scenario_by_id(s.id)
        assert found == s
        assert get_scenario_by_id("non_existent_id_999") is None

        # By Category
        tools_scenarios = get_scenarios_by_category(ScenarioCategory.TOOLS)
        assert len(tools_scenarios) > 0
        for s in tools_scenarios:
            assert s.category == ScenarioCategory.TOOLS

    def test_custom_yaml_loading(self):
        """Testa carregamento de YAML customizado."""
        data = {
            "scenarios": [
                {
                    "id": "test_yaml_01",
                    "category": "tools",
                    "prompt": "/test code",
                    "expectations": ["has_response", "latency_under_5s"],
                    "description": "Test YAML Loader",
                    "timeout_seconds": 10,
                }
            ]
        }

        # Cria arquivo temporário
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            yaml.dump(data, tmp)
            tmp_path = Path(tmp.name)

        try:
            loaded = load_custom_scenarios(tmp_path)
            assert len(loaded) == 1
            s = loaded[0]
            assert s.id == "test_yaml_01"
            assert s.category == ScenarioCategory.TOOLS
            assert s.prompt == "/test code"
            assert Expectation.HAS_RESPONSE in s.expectations
            assert Expectation.LATENCY_UNDER_5S in s.expectations
            assert s.timeout_seconds == 10
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_yaml_defaults(self):
        """Testa defaults ao carregar YAML incompleto."""
        data = {
            "scenarios": [
                {
                    "id": "test_defaults",
                    "prompt": "/minimal",
                    # category default=analysis, expectations default=[has_response]
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            yaml.dump(data, tmp)
            tmp_path = Path(tmp.name)

        try:
            loaded = load_custom_scenarios(tmp_path)
            s = loaded[0]
            assert s.category == ScenarioCategory.ANALYSIS
            assert s.expectations == [Expectation.HAS_RESPONSE]
            assert s.timeout_seconds == 30
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_invalid_yaml_path(self):
        """Caminho inválido deve retornar lista vazia."""
        assert load_custom_scenarios(Path("/non/existent/path.yaml")) == []

    def test_malformed_yaml(self):
        """Arquivo malformado deve ser tratado graciosamente."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write("scenarios: [ { invalid json... ")
            tmp_path = Path(tmp.name)

        try:
            # Deve capturar excessão e retornar vazio
            assert load_custom_scenarios(tmp_path) == []
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

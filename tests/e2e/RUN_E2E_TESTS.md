# E2E Test Suite for Vertice-Code

## Overview

This directory contains **heavy integration tests** that validate the real behavior of Vertice-Code with actual LLM calls.

## Test Files

| File | Description | Duration | Tests |
|------|-------------|----------|-------|
| `test_e2e_real_llm.py` | Real LLM interactions, app creation, refactoring | 30-60 min | ~30 |
| `test_e2e_shell_integration.py` | Tool registry, NLU components, context | 5-10 min | ~40 |
| `test_e2e_brutal_scenarios.py` | Heavy multi-step workflows (FastAPI, CLI, ETL) | 60-90 min | ~6 |

### Prometheus Tests

| File | Description | Duration |
|------|-------------|----------|
| `../prometheus/test_scientific_validation.py` | Full Prometheus pipeline validation | 10-15 min |
| `../prometheus/test_e2e_quick.py` | Quick Prometheus smoke test | 2-5 min |
| `tools/test_prometheus_tools.py` | Prometheus tool unit tests | 1-2 min |

## Requirements

### Environment Variables

Set at least ONE of these API keys:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export GOOGLE_API_KEY="..."
# OR
export GROQ_API_KEY="..."
```

### Python Dependencies

```bash
pip install -e .
pip install pytest pytest-asyncio pytest-timeout
```

## Running Tests

### Quick Validation (5-10 minutes)

```bash
# Run shell integration tests only (no heavy LLM calls)
pytest tests/e2e/test_e2e_shell_integration.py -v --timeout=120
```

### Full LLM Tests (30-60 minutes)

```bash
# Run all real LLM tests
pytest tests/e2e/test_e2e_real_llm.py -v --timeout=300
```

### Brutal Scenarios (60-90 minutes)

```bash
# Run all brutal scenarios
pytest tests/e2e/test_e2e_brutal_scenarios.py -v --timeout=900

# Run specific scenario
pytest tests/e2e/test_e2e_brutal_scenarios.py -k "fastapi" -v
pytest tests/e2e/test_e2e_brutal_scenarios.py -k "portuguese" -v
```

### Complete Suite (2-3 hours)

```bash
# Run everything
pytest tests/e2e/ -v --timeout=900

# With coverage
pytest tests/e2e/ -v --timeout=900 --cov=vertice_cli
```

### Prometheus Integration (10-15 minutes)

```bash
# Quick smoke test
python tests/prometheus/test_e2e_quick.py

# Full scientific validation
python tests/prometheus/test_scientific_validation.py

# Prometheus tool tests
pytest tests/e2e/tools/test_prometheus_tools.py -v
```

## Test Categories

### 1. App Creation Tests

Tests creating applications from natural language:

- Python hello world
- Calculator module
- Flask/FastAPI API
- CLI tools with argparse
- Data models with dataclasses

### 2. Refactoring Tests

Tests code refactoring operations:

- Extract function
- Rename variable
- Add type hints
- Add docstrings
- Convert class to dataclass

### 3. Portuguese NLU Tests

Tests Portuguese language understanding:

- Imperative forms (mostra, cria, busca)
- Colloquial expressions (ta quebrado, onde fica)
- Accented input handling
- Complete Portuguese workflows

### 4. Complex Workflows

Tests multi-step operations:

- Create module + tests
- Read + analyze + refactor
- Project structure creation
- API with validation

### 5. Error Handling

Tests error recovery:

- Non-existent files
- Ambiguous requests
- Invalid syntax fixes

## Expected Results

### Minimum Passing

- Shell Integration: **95%+** should pass
- Real LLM Tests: **80%+** should pass
- Brutal Scenarios: **60%+** should pass (these are very hard)

### Portuguese Accuracy Targets

- Intent Classification: **80%+**
- Agent Routing: **85%+**
- Request Amplification: **90%+**

## Troubleshooting

### Tests Skipped

If all tests are skipped, check API keys:

```bash
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY
echo $GROQ_API_KEY
```

### Timeout Errors

Increase timeout for slow LLMs:

```bash
pytest tests/e2e/ -v --timeout=600
```

### Import Errors

Ensure vertice-cli is installed:

```bash
pip install -e .
```

## Jules Instructions

### For Quick Validation

```bash
cd /media/juan/DATA/Vertice-Code
source .venv/bin/activate  # if using venv
export GROQ_API_KEY="..."  # or other API key

# Quick test (5 min)
pytest tests/e2e/test_e2e_shell_integration.py -v --timeout=120 2>&1 | tee e2e_quick_results.txt
```

### For Prometheus Validation

```bash
cd /media/juan/DATA/Vertice-Code
source .venv/bin/activate
export GOOGLE_API_KEY="..."  # Required for Prometheus

# Verify imports work (should print "OK")
python -c "from vertice_tui.core.prometheus_client import PrometheusClient; print('OK')"

# Run quick smoke test
python tests/prometheus/test_e2e_quick.py

# Run full validation
python tests/prometheus/test_scientific_validation.py 2>&1 | tee prometheus_validation.txt
```

### For Complete Validation

```bash
cd /media/juan/DATA/Vertice-Code
source .venv/bin/activate

# Full test (2+ hours)
pytest tests/e2e/ -v --timeout=900 2>&1 | tee e2e_full_results.txt
```

### Report Format

After running, generate report:

```bash
pytest tests/e2e/ -v --timeout=900 --tb=short 2>&1 | tee E2E_REPORT.txt
```

## Sample Output

```
===================== test session starts =====================
platform linux -- Python 3.11.x, pytest-8.x.x
collected 76 items

tests/e2e/test_e2e_shell_integration.py::TestToolRegistry::test_registry_loads_all_tools PASSED
tests/e2e/test_e2e_shell_integration.py::TestIntentClassification::test_portuguese_intent_accuracy PASSED
...
tests/e2e/test_e2e_real_llm.py::TestAppCreation::test_create_python_hello_world PASSED
tests/e2e/test_e2e_real_llm.py::TestRefactoring::test_refactor_extract_function PASSED
...
tests/e2e/test_e2e_brutal_scenarios.py::TestFastAPICreation::test_create_complete_fastapi_app PASSED

===================== 70 passed, 6 failed in 3847.23s =====================
```

---

**Author:** Claude Opus 4.5
**Date:** 2026-01-04
**Version:** 1.1

### Changelog

- v1.1 (2026-01-04): Added Prometheus validation section and tests
- v1.0 (2026-01-03): Initial version

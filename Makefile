
test-e2e:
pytest tests/tui_e2e
python3 scripts/e2e/measure_quality.py

test-quality-real:
python3 scripts/e2e/measure_quality.py --real --scenario complex_feature


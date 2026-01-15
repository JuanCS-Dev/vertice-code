
### 🧪 TUI Quality Assurance (New)
We now support "Heavy Duty" simulation where the TUI is driven by a scripted or real LLM to perform complex coding tasks.

**Run Scripts:**
```bash
# Run Headless & Interactive Tests
make test-e2e

# Run Real LLM Simulation (Requires GEMINI_API_KEY)
make test-quality-real
# Or manually:
python3 scripts/e2e/measure_quality.py --real --scenario complex_feature
```

**Scenarios:**
- `refactor_scenario`: Refactoring legacy code into classes.
- `complex_feature`: Building a FastAPI+SQLite backend.
- `debug_fix`: Fixing an infinite loop bug.

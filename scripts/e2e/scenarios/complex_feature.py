
"""
Complex Feature Scenario
Target: Create a simple boilerplate FastAPI backend with SQLite integration.
"""

SETUP_FILES = {}

PROMPT = """
Create a simple FastAPI application with one Todo model and a SQLite database.
It should have:
1. `main.py`: The FastAPI app and routes (GET /todos, POST /todos).
2. `database.py`: SQLAlchemy setup (SessionLocal, Base).
3. `models.py`: The Todo model (id, title, completed).
No folder nesting needed, keep it flat.
"""

EXPECTED_FILES = ["main.py", "database.py", "models.py"]

def check_fastapi():
    main = open("main.py").read()
    return "FastAPI" in main and "app.include_router" not in main # Simple check

def check_models():
    models = open("models.py").read()
    return "Column(Integer" in models and "tablename" in models

VALIDATION_RULES = [
    lambda: check_fastapi(),
    lambda: check_models(),
    lambda: "create_engine" in open("database.py").read()
]

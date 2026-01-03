"""
Test Generators - Test Case Generation Logic.

Pure functions for generating test cases from AST analysis.
Follows Boris Cherny philosophy: pure functions, zero side effects.

Capabilities:
    - Unit test generation (pytest-style)
    - Edge case tests (None, empty, boundaries)
    - Class integration tests
    - TUI tests for Textual apps
"""

import ast
from typing import List, Union

from .models import TestCase, TestType


def generate_test_suite(source_code: str) -> List[TestCase]:
    """Generate comprehensive test suite for source code.

    Args:
        source_code: Python source code to test

    Returns:
        List of generated TestCase objects

    Strategy:
        1. Parse AST to extract functions/classes
        2. Generate unit tests for each function
        3. Generate edge case tests
        4. Generate integration tests for classes
        5. Generate TUI tests for Textual apps
    """
    test_cases: List[TestCase] = []

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return test_cases

    # Extract functions (including async)
    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    # Extract classes
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    # Generate unit tests for functions
    for func in functions:
        if not func.name.startswith("_"):  # Skip private functions
            test_cases.extend(generate_function_tests(func))

    # Generate integration tests for classes
    for cls in classes:
        test_cases.extend(generate_class_tests(cls))

    # Generate TUI tests if Textual detected
    if "textual" in source_code.lower():
        tui_apps = [
            cls for cls in classes
            if any(
                isinstance(b, ast.Name) and b.id == 'App'
                for b in cls.bases
            )
        ]
        for app in tui_apps:
            test_cases.extend(generate_tui_tests(app))

    return test_cases


def generate_function_tests(
    func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
) -> List[TestCase]:
    """Generate tests for a single function.

    Args:
        func: AST FunctionDef node

    Returns:
        List of test cases for this function
    """
    tests: List[TestCase] = []
    func_name = func.name

    # Analyze function signature
    params = [arg.arg for arg in func.args.args]
    has_return = _has_return_statement(func)

    # Generate basic unit test
    basic_test = _create_basic_test(func_name, params, has_return)
    tests.append(basic_test)

    # Generate edge case tests
    if params:
        edge_tests = _create_edge_case_tests(func_name, params)
        tests.extend(edge_tests)

    return tests


def generate_class_tests(cls: ast.ClassDef) -> List[TestCase]:
    """Generate integration tests for a class.

    Args:
        cls: AST ClassDef node

    Returns:
        List of test cases for this class
    """
    tests: List[TestCase] = []
    class_name = cls.name

    # Test class instantiation
    init_test = TestCase(
        name=f"test_{class_name}_instantiation",
        code=f'''def test_{class_name}_instantiation():
    """Test {class_name} can be instantiated."""
    instance = {class_name}()
    assert instance is not None
    assert isinstance(instance, {class_name})
''',
        test_type=TestType.INTEGRATION,
        target=class_name,
        assertions=2,
        complexity=2,
    )
    tests.append(init_test)

    return tests


def generate_tui_tests(app_class: ast.ClassDef) -> List[TestCase]:
    """Generate tests for Textual TUI apps.

    Args:
        app_class: AST ClassDef node for Textual App

    Returns:
        List of TUI test cases
    """
    tests = []
    app_name = app_class.name

    # 1. Basic App Load Test
    tests.append(TestCase(
        name=f"test_{app_name.lower()}_load",
        code=f'''
@pytest.mark.asyncio
async def test_{app_name.lower()}_load():
    """Test that {app_name} loads without error."""
    app = {app_name}()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.is_running
''',
        test_type=TestType.TUI,
        target=app_name,
        assertions=1,
        complexity=2
    ))

    # 2. Key Press Interaction Test
    tests.append(TestCase(
        name=f"test_{app_name.lower()}_q_quit",
        code=f'''
@pytest.mark.asyncio
async def test_{app_name.lower()}_quit_command():
    """Test that pressing 'q' behaves as expected."""
    app = {app_name}()
    async with app.run_test() as pilot:
        await pilot.press("q")
        assert app.return_code is None or app.return_code == 0
''',
        test_type=TestType.TUI,
        target=app_name,
        assertions=1,
        complexity=3
    ))

    return tests


def _create_basic_test(
    func_name: str, params: List[str], has_return: bool
) -> TestCase:
    """Create basic happy-path test.

    Args:
        func_name: Function being tested
        params: List of parameter names
        has_return: Whether function returns a value

    Returns:
        TestCase for basic functionality
    """
    # Generate mock parameters
    param_values = ", ".join(_mock_param_value(p) for p in params)

    # Generate test code
    if has_return:
        code = f'''def test_{func_name}_basic():
    """Test basic functionality of {func_name}."""
    result = {func_name}({param_values})
    assert result is not None
'''
    else:
        code = f'''def test_{func_name}_basic():
    """Test basic functionality of {func_name}."""
    {func_name}({param_values})
    # No exception should be raised
'''

    return TestCase(
        name=f"test_{func_name}_basic",
        code=code,
        test_type=TestType.UNIT,
        target=func_name,
        assertions=1,
        complexity=2,
    )


def _create_edge_case_tests(
    func_name: str, params: List[str]
) -> List[TestCase]:
    """Create edge case tests.

    Args:
        func_name: Function being tested
        params: List of parameter names

    Returns:
        List of edge case test cases
    """
    tests: List[TestCase] = []

    # Test with None values
    none_test = TestCase(
        name=f"test_{func_name}_with_none",
        code=f'''def test_{func_name}_with_none():
    """Test {func_name} handles None input."""
    import pytest
    with pytest.raises((TypeError, ValueError)):
        {func_name}(None)
''',
        test_type=TestType.EDGE_CASE,
        target=func_name,
        assertions=1,
        complexity=3,
    )
    tests.append(none_test)

    # Test with empty values
    if any(p in ["list", "dict", "str", "data"] for p in params):
        empty_test = TestCase(
            name=f"test_{func_name}_with_empty",
            code=f'''def test_{func_name}_with_empty():
    """Test {func_name} handles empty input."""
    result = {func_name}('')
    assert result is not None
''',
            test_type=TestType.EDGE_CASE,
            target=func_name,
            assertions=1,
            complexity=3,
        )
        tests.append(empty_test)

    return tests


def _has_return_statement(
    func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
) -> bool:
    """Check if function has return statement.

    Args:
        func: AST FunctionDef node

    Returns:
        True if function returns a value
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Return) and node.value is not None:
            return True
    return False


def _mock_param_value(param_name: str) -> str:
    """Generate mock value for parameter.

    Args:
        param_name: Parameter name

    Returns:
        String representation of mock value
    """
    param_lower = param_name.lower()

    if "id" in param_lower:
        return "1"
    elif "name" in param_lower:
        return "'test_name'"
    elif "email" in param_lower:
        return "'test@example.com'"
    elif "list" in param_lower or "items" in param_lower:
        return "[]"
    elif "dict" in param_lower or "data" in param_lower:
        return "{}"
    elif "bool" in param_lower or param_name.startswith("is_"):
        return "True"
    else:
        return "None"


__all__ = [
    "generate_test_suite",
    "generate_function_tests",
    "generate_class_tests",
    "generate_tui_tests",
]

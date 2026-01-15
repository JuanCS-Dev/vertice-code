
"""
Refactor Scenario
Target: Take a messy script 'messy_math.py' and refactor it into 'math_utils.py' (class-based) and 'test_math.py'.
"""

SETUP_FILES = {
    "messy_math.py": """
def do_math(a, b, op):
    if op == 'add': return a + b
    if op == 'sub': return a - b
    if op == 'mul': return a * b
    return 0

print(do_math(10, 5, 'add'))
"""
}

PROMPT = """
I have a file named 'messy_math.py'. 
Please refactor it into a clean, object-oriented module named 'math_utils.py' with a 'MathOperations' class.
Also create a unittest file 'test_math.py' to verify it.
"""

EXPECTED_FILES = ["math_utils.py", "test_math.py"]

VALIDATION_RULES = [
    lambda: "class MathOperations" in open("math_utils.py").read(),
    lambda: "import unittest" in open("test_math.py").read(),
    lambda: "messy_math.py" in open("messy_math.py").read() # Should NOT be deleted unless asked
]

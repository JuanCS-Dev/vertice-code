"""
AST Analyzers - Code Structure Analysis for Documentation.

Provides AST-based analysis to extract documentation metadata
from Python modules, classes, and functions.

Features:
    - Module structure extraction
    - Class hierarchy analysis
    - Function signature parsing
    - Type annotation extraction
"""

import ast
from pathlib import Path
from typing import List, Tuple, Union

from .models import ClassDoc, FunctionDoc, ModuleDoc


def analyze_module(file_path: Path) -> ModuleDoc:
    """Analyze Python module using AST.

    Args:
        file_path: Path to .py file

    Returns:
        ModuleDoc with extracted structure

    Raises:
        SyntaxError: If file has invalid Python syntax
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    module_docstring = ast.get_docstring(tree)

    classes: List[ClassDoc] = []
    functions: List[FunctionDoc] = []
    imports: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(analyze_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(analyze_function(node))

    return ModuleDoc(
        name=file_path.stem,
        docstring=module_docstring,
        classes=classes,
        functions=functions,
        imports=imports,
        file_path=str(file_path),
    )


def analyze_class(node: ast.ClassDef) -> ClassDoc:
    """Analyze class definition.

    Args:
        node: AST ClassDef node

    Returns:
        ClassDoc with class metadata
    """
    docstring = ast.get_docstring(node)
    bases = [_get_name(base) for base in node.bases]
    methods: List[FunctionDoc] = []
    attributes: List[Tuple[str, str, None]] = []

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(analyze_function(item))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            attr_name = item.target.id
            attr_type = _get_name(item.annotation) if item.annotation else "Any"
            attributes.append((attr_name, attr_type, None))

    return ClassDoc(
        name=node.name,
        docstring=docstring,
        bases=bases,
        methods=methods,
        attributes=attributes,
        line_number=node.lineno,
    )


def analyze_function(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> FunctionDoc:
    """Analyze function/method definition.

    Args:
        node: AST FunctionDef or AsyncFunctionDef node

    Returns:
        FunctionDoc with function metadata
    """
    docstring = ast.get_docstring(node)
    signature = _get_signature(node)

    parameters: List[Tuple[str, str, None]] = []
    for arg in node.args.args:
        param_name = arg.arg
        param_type = _get_name(arg.annotation) if arg.annotation else "Any"
        parameters.append((param_name, param_type, None))

    returns = None
    if node.returns:
        return_type = _get_name(node.returns)
        returns = (return_type, None)

    return FunctionDoc(
        name=node.name,
        signature=signature,
        docstring=docstring,
        parameters=parameters,
        returns=returns,
        raises=[],
        examples=[],
        line_number=node.lineno,
    )


def _get_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """Generate function signature string.

    Args:
        node: AST function node

    Returns:
        Signature string (e.g., "def foo(x: int, y: str) -> bool")
    """
    args = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {_get_name(arg.annotation)}"
        args.append(arg_str)

    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    sig = f"{prefix} {node.name}({', '.join(args)})"
    if node.returns:
        sig += f" -> {_get_name(node.returns)}"
    return sig


def _get_name(node: ast.expr) -> str:
    """Extract name from AST node.

    Args:
        node: AST expression node

    Returns:
        String representation of the name
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Subscript):
        return f"{_get_name(node.value)}[{_get_name(node.slice)}]"
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, (ast.List, ast.Tuple)):
        elts = [_get_name(e) for e in node.elts]
        return f"[{', '.join(elts)}]"
    elif isinstance(node, ast.Call):
        func = _get_name(node.func)
        args = [_get_name(a) for a in node.args]
        return f"{func}({', '.join(args)})"
    elif isinstance(node, ast.BinOp):
        return f"{_get_name(node.left)} | {_get_name(node.right)}"
    else:
        return "Any"


__all__ = [
    "analyze_module",
    "analyze_class",
    "analyze_function",
]

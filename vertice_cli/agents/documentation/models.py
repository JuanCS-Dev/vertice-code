"""
Documentation Models - Enums and Dataclasses for Documentation Agent.

Contains type-safe data structures for documentation formats,
styles, and extracted documentation metadata.

Philosophy (Boris Cherny):
    "Code tells you how. Documentation tells you why."
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class DocFormat(str, Enum):
    """Supported documentation formats."""

    MARKDOWN = "markdown"
    RST = "rst"  # ReStructuredText (Sphinx)
    HTML = "html"
    DOCSTRING = "docstring"  # In-code docstrings
    API_REFERENCE = "api_reference"


class DocstringStyle(str, Enum):
    """Docstring formatting styles."""

    GOOGLE = "google"  # Google Style (default)
    NUMPY = "numpy"  # NumPy/SciPy
    SPHINX = "sphinx"  # Sphinx/RST


@dataclass
class FunctionDoc:
    """Documentation for a function/method."""

    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Tuple[str, str, Optional[str]]]  # (name, type, description)
    returns: Optional[Tuple[str, str]]  # (type, description)
    raises: List[Tuple[str, str]]  # (exception, reason)
    examples: List[str]
    line_number: int


@dataclass
class ClassDoc:
    """Documentation for a class."""

    name: str
    docstring: Optional[str]
    bases: List[str]
    methods: List[FunctionDoc]
    attributes: List[Tuple[str, str, Optional[str]]]  # (name, type, description)
    line_number: int


@dataclass
class ModuleDoc:
    """Documentation for a module."""

    name: str
    docstring: Optional[str]
    classes: List[ClassDoc]
    functions: List[FunctionDoc]
    imports: List[str]
    file_path: str


__all__ = [
    "DocFormat",
    "DocstringStyle",
    "FunctionDoc",
    "ClassDoc",
    "ModuleDoc",
]

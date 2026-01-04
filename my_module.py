
"""My Module.

This module provides a collection of utility functions.
"""

def add(a: int, b: int) -> int:
    """Adds two integers.

    Args:
        a: The first integer.
        b: The second integer.

    Returns:
        The sum of a and b.

    Raises:
        TypeError: If either a or b is not an integer.
    """
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Inputs must be integers.")
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtracts two integers.

    Args:
        a: The first integer.
        b: The second integer.

    Returns:
        The difference of a and b.

    Raises:
        TypeError: If either a or b is not an integer.
    """
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Inputs must be integers.")
    return a - b

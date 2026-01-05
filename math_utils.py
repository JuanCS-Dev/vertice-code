'''A collection of thread-safe mathematical utility functions.'''

import functools
from typing import Generator


def fibonacci(n: int) -> Generator[int, None, None]:
    """Generates the Fibonacci sequence up to n numbers.

    Args:
        n: The number of Fibonacci numbers to generate.

    Yields:
        The next number in the Fibonacci sequence.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


@functools.lru_cache(maxsize=None)
def factorial(n: int) -> int:
    """Calculates the factorial of a non-negative integer with caching.

    Args:
        n: The non-negative integer to calculate the factorial of.

    Returns:
        The factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 1
    return n * factorial(n - 1)

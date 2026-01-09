"""A module to calculate Fibonacci numbers using memoized recursion."""

from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    """
    Calculates the nth Fibonacci number using recursion with memoization
    provided by functools.lru_cache.

    Args:
        n: The index of the Fibonacci number to calculate (must be a non-negative integer).

    Returns:
        The nth Fibonacci number.
        
    Raises:
        ValueError: If n is not a non-negative integer.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

if __name__ == "__main__":
    # Demonstrate the usage for n=10 and n=50
    n1 = 10
    n2 = 50

    print(f"Calculating Fibonacci number for n={n1}")
    result1 = fibonacci(n1)
    print(f"Fibonacci({n1}) = {result1}")

    print(f"Calculating Fibonacci number for n={n2}")
    result2 = fibonacci(n2)
    print(f"Fibonacci({n2}) = {result2}")


"""
This module provides a function to calculate the factorial of a non-negative integer.
"""

def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.

    Args:
        n: The non-negative integer for which to calculate the factorial.

    Returns:
        The factorial of n.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is a negative integer.
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

if __name__ == '__main__':
    num = 5
    fact = factorial(num)
    print(f"The factorial of {num} is {fact}")

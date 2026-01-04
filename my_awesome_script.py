
"""
A simple Python script.
"""


def add(x: int, y: int) -> int:
    """
    Adds two integers together.

    Args:
        x: The first integer.
        y: The second integer.

    Returns:
        The sum of x and y.
    """
    return x + y


if __name__ == "__main__":
    result = add(5, 3)
    print(f"The result of adding 5 and 3 is: {result}")

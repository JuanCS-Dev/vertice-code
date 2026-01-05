'''Tests for the math_utils module.'''

import pytest

from math_utils import factorial, fibonacci


def def test_fibonacci():
    """Tests the fibonacci sequence generator."""
    assert list(fibonacci(0)) == []
    assert list(fibonacci(1)) == [0]
    assert list(fibonacci(2)) == [0, 1]
    assert list(fibonacci(5)) == [0, 1, 1, 2, 3]
    assert list(fibonacci(10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def def test_fibonacci_negative_input():
    """Tests that fibonacci raises a ValueError for negative input."""
    with pytest.raises(ValueError):
        list(fibonacci(-1))


def def test_factorial():
    """Tests the factorial calculator."""
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800


def def test_factorial_negative_input():
    """Tests that factorial raises a ValueError for negative input."""
    with pytest.raises(ValueError):
        factorial(-1)


def def test_factorial_cache():
    """Tests the caching of the factorial function."""
    # The first call will calculate and cache the result.
    factorial(10)
    # The second call should be faster as it uses the cache.
    # We can also check the cache info.
    assert factorial.cache_info().hits > 0

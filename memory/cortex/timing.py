
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def timing_decorator(func):
    """An async-aware timing decorator."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000
        logger.info(f"{func.__name__} executed in {elapsed_time:.2f}ms")
        return result
    return wrapper

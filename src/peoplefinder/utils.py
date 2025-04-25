from functools import wraps

from django.core.cache import cache


def cache_for_one_hour(func):
    """
    A decorator that caches the output of a function for 1 hour.
    """
    # 1 hour
    cache_time: int = 60 * 60
    cache_key = f"{func.__module__}.{func.__name__}"

    @wraps(func)
    def wrapper(*args, **kwargs):
        if cached_response := cache.get(cache_key):
            return cached_response

        uncached_response = func(*args, **kwargs)
        cache.add(cache_key, uncached_response, cache_time)
        return uncached_response

    return wrapper

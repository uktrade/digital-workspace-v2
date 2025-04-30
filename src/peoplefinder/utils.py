from functools import wraps

from django.core.cache import cache


def cache_for(days: int|None = None, hours: int|None = None, minutes: int|None=None, seconds:int|None = None):
    """
    A decorator that caches the output of a function for the specified number of minutes.
    """
    if days is None and hours is None and minutes is None and seconds is None:
        raise ValueError("No cache time specified")

    cache_time:int = 0
    if seconds is not None:
        cache_time += seconds

    if minutes is not None:
        cache_time += minutes * 60

    if hours is not None:
        cache_time += hours * 60 * 60

    if days is not None:
        cache_time += days * 24 * 60 * 60

    def cache_for_specified_minutes(func):
        cache_key = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            if cached_response := cache.get(cache_key):
                return cached_response

            uncached_response = func(*args, **kwargs)
            cache.add(cache_key, uncached_response, cache_time)
            return uncached_response
        return wrapper
    return cache_for_specified_minutes

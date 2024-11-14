from datetime import time
from functools import wraps

from django.core.cache import cache
from waffle import flag_is_active

from core.models import FeatureFlag


def get_all_feature_flags(request):
    return {
        flag.name: flag_is_active(request, flag.name)
        for flag in FeatureFlag.objects.all()
    }


def format_time(time_obj: time) -> str:
    """
    Build a time string that shows the needed information.

    Returns:
     - If there are minutes on the hour: `10:30` -> `10:30am`
     - If there are not minutes on the hour: `10:00` -> `10am`

    """
    if time_obj.minute == 0:
        return time_obj.strftime("%-I%p").lstrip("0").lower()
    return time_obj.strftime("%-I:%M%p").lstrip("0").lower()


def cache_lock(cache_key: str, cache_time: int = 60 * 60 * 3):
    # A decorator that prevents a function from running if the cache key is currently set.
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.add(cache_key, "locked", 60 * 60 * 3):
                return
            func(*args, **kwargs)
            cache.delete(cache_key)

        return wrapper

    return decorator

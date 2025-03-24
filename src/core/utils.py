from datetime import time
from functools import wraps

from django.core.cache import cache
from django.http import HttpRequest
from waffle import flag_is_active

from core import flags
from core.models import ExternalLinkSetting, FeatureFlag


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
    """
    A decorator that prevents a function from running if the cache key is currently set.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.add(cache_key, "locked", cache_time):
                return
            try:
                func(*args, **kwargs)
            finally:
                cache.delete(cache_key)

        return wrapper

    return decorator


def get_external_link_settings(request: HttpRequest) -> dict:
    """
    Get the external link settings from the database.
    """
    external_link_settings = {
        "enabled": flag_is_active(request, flags.EXTERNAL_LINKS),
    }

    exclude_domains = cache.get("external_link_settings__exclude_domains", None)
    domain_mapping = cache.get("external_link_settings__domain_mapping", None)

    if exclude_domains is None or domain_mapping is None:
        exclude_domains = []
        domain_mapping = {}

        for els in ExternalLinkSetting.objects.all():
            if els.exclude:
                exclude_domains.append(els.domain)
            else:
                domain_mapping[els.domain] = els.external_link_text

            cache.set(
                "external_link_settings__exclude_domains", exclude_domains, 60 * 60 * 12
            )
            cache.set(
                "external_link_settings__domain_mapping", domain_mapping, 60 * 60 * 12
            )

    external_link_settings["exclude_domains"] = exclude_domains
    external_link_settings["domain_mapping"] = domain_mapping
    return external_link_settings

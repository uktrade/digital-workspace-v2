from datetime import time
from functools import wraps

from django.core.cache import cache
from django.db import models
from django.http import HttpRequest
from waffle import flag_is_active as waffle_flag_is_active

from core import flags
from core.models import ExternalLinkSetting, FeatureFlag


EXTENDED_LINKS_SETTINGS_CACHE = {
    "keys": {
        "exclude_domains": "external_link_settings__exclude_domains",
        "domain_mapping": "external_link_settings__domain_mapping",
    },
    "timeout": 60 * 60 * 12,
}


def get_all_feature_flags(request) -> dict[str, bool]:
    if all_flags := request.session.get("all_feature_flags", False):
        return all_flags

    all_flags = {
        flag.name: waffle_flag_is_active(request, flag.name)
        for flag in FeatureFlag.objects.all()
    }
    # This small amount of DB-backed data is accessed multiple times per request, so session storage makes sense
    request.session["all_feature_flags"] = all_flags
    return all_flags


def flag_is_active(request, flag_name: str) -> bool | None:
    """Replicates waffle functionality but uses cached results"""
    all_flags: dict[str, bool] = get_all_feature_flags(request)
    try:
        return all_flags[flag_name]
    except KeyError:
        return None


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


def cache_for(
    days: int | None = None,
    hours: int | None = None,
    minutes: int | None = None,
    seconds: int | None = None,
):
    """
    A decorator that caches the output of a function for the specified number of minutes.
    """
    if days is None and hours is None and minutes is None and seconds is None:
        raise ValueError("No cache time specified")

    cache_time: int = 0
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


def get_external_link_settings(request: HttpRequest) -> dict:
    """
    Get the external link settings from the database.
    """
    external_link_settings = {
        "enabled": flag_is_active(request, flags.EXTERNAL_LINKS),
    }

    exclude_domains = cache.get(
        EXTENDED_LINKS_SETTINGS_CACHE["keys"]["exclude_domains"], None
    )
    domain_mapping = cache.get(
        EXTENDED_LINKS_SETTINGS_CACHE["keys"]["domain_mapping"], None
    )

    if exclude_domains is None or domain_mapping is None:
        exclude_domains = []
        domain_mapping = {}

        for els in ExternalLinkSetting.objects.all():
            if els.exclude:
                exclude_domains.append(els.domain)
            else:
                domain_mapping[els.domain] = els.external_link_text

            cache.set(
                EXTENDED_LINKS_SETTINGS_CACHE["keys"]["exclude_domains"],
                exclude_domains,
                EXTENDED_LINKS_SETTINGS_CACHE["timeout"],
            )
            cache.set(
                EXTENDED_LINKS_SETTINGS_CACHE["keys"]["domain_mapping"],
                domain_mapping,
                EXTENDED_LINKS_SETTINGS_CACHE["timeout"],
            )

    external_link_settings["exclude_domains"] = exclude_domains
    external_link_settings["domain_mapping"] = domain_mapping
    return external_link_settings


def get_data_for_django_filters_choices(
    *, model: models.Model, field_name: str
) -> list[tuple[str, str]]:
    """
    Returns a list[tuple[value, value]] for a given model and field name,
    as django_filters expects choices to be in a list of tuple.
    """
    data = (
        model.objects.order_by(field_name).values_list(field_name, flat=True).distinct()
    )
    return [(value, value) for value in data]

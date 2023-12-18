from .base import *  # noqa

APP_ENV = "build"

SEARCH_ENABLE_QUERY_CACHE = False  # Don't access Redis at build time

LOGGING["handlers"]["ecs"]["formatter"] = "asim_formatter"  # noqa F405

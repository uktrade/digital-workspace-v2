from .base import *  # noqa

from django_log_formatter_asim import ASIMFormatter

APP_ENV = "build"

SEARCH_ENABLE_QUERY_CACHE = False  # Don't access Redis at build time

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "asim_formatter": {
            "()": ASIMFormatter,
        },
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "ecs": {
            "class": "logging.StreamHandler",
            "formatter": "asim_formatter",
        },
        "simple": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": [
                "ecs",
                "simple",
                "stdout",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                "ecs",
                "simple",
                "stdout",
            ],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "ecs",
                "simple",
                "stdout",
            ],
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "opensearch": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("OPENSEARCH_LOG_LEVEL", "INFO"),
        },
        "environ": {
            "handlers": [
                "stdout",
            ],
            "level": os.getenv("ENVIRON_LOG_LEVEL", "INFO"),
        },
    },
}

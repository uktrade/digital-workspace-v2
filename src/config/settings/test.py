import logging

from .base import *  # noqa

APP_ENV = "test"
DEBUG = True
TEMPLATE_DEBUG = True

# Required for tests to bypass SSO.
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # noqa

# Turn off Celery
CELERY_ALWAYS_EAGER = True

WAGTAILSEARCH_BACKENDS["default"] |= {  # noqa
    "INDEX": "test_wagtail",
    "AUTO_UPDATE": False,
}

INSTALLED_APPS += [  # noqa F405
    "django_extensions",
]

LOGGING["handlers"] |= {  # noqa F405
    "file": {
        "level": "DEBUG",
        "class": "logging.FileHandler",
        "filename": "/tmp/wagtail-debug.log",  # noqa S108
    }
}
LOGGING["loggers"] = {  # noqa F405
    "django.db.backends.schema": {
        "handlers": ["file"],
        "propagate": True,
        "level": "INFO",
    },
    # "": {
    #     "handlers": ["file"],
    #     "level": "DEBUG",
    # },
}

logging.disable(logging.WARN)

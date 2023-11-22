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

INSTALLED_APPS = [  # noqa F405
    "testapp",
    "django_extensions",
] + INSTALLED_APPS

# Remove the uk_staff_locations database
del DATABASES["uk_staff_locations"]  # noqa F405
INGESTED_MODELS_DATABASES.remove("uk_staff_locations")  # noqa F405

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

import logging

from .base import *  # noqa


APP_ENV = "test"
DEBUG = False
TEMPLATE_DEBUG = False

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

logging.disable(logging.WARN)

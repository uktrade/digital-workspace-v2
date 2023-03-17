from .base import *  # noqa


APP_ENV = "test"

# Required for tests to bypass SSO.
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # noqa

# Turn off Celery
CELERY_ALWAYS_EAGER = True

WAGTAILSEARCH_BACKENDS["default"] |= {  # noqa
    "INDEX": "test_wagtail",
    "AUTO_UPDATE": False,
}

import logging
logging.disable(logging.WARN)

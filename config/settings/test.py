from .base import *  # noqa


APP_ENV = "test"

# Required for tests to bypass SSO.
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # noqa

MAILCHIMP_TIMEOUT = 1
MAILCHIMP_SLEEP_INTERVAL = 1

from .base import *  # noqa


# Required for tests to bypass SSO.
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # noqa

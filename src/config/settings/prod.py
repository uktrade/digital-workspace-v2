from .base import *  # noqa

DEBUG = False

AWS_S3_URL_PROTOCOL = "https:"
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")  # noqa F405
AWS_QUERYSTRING_AUTH = False

SESSION_COOKIE_AGE = 60 * 60

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 15768000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING["root"]["handlers"] = [  # noqa F405
    "ecs",
    "simple",
]
LOGGING["loggers"]["django"]["propagate"] = False  # noqa F405
LOGGING["loggers"]["django.db.backends"]["propagate"] = False  # noqa F405
